"""Tests for the 3-agent pipeline (classify -> extract -> plan).

The transport is fake and answers per agent marker, so no live API call
is made. These tests pin the wiring (shapes, ordering, conflicts, ledger),
not the model's judgment.
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pileup.client import EmberClient, Ledger
from pileup.pipeline import run_pile

CLASSIFY = json.dumps({"type": "flyer", "confidence": 0.9})
EXTRACT = json.dumps({
    "dates": [{"text": "Dec 12, 9 AM", "iso": "2026-12-12T09:00:00"}],
    "amounts": [],
    "people": ["Amelia"],
    "actions": [{"text": "bring a poster board", "due": "2026-12-12"}],
})
PLAN = json.dumps({
    "actions": [
        {"text": "pay the bill", "due": "2026-12-05", "source": "item-2"},
        {"text": "bring a poster board", "due": "2026-12-12",
         "source": "item-1"},
    ],
    "conflicts": [{"text": "two items due Dec 5"}],
})


def fake_transport(payload):
    text = json.dumps(payload)
    if "CLASSIFY-ITEM" in text:
        reply = CLASSIFY
    elif "EXTRACT-FIELDS" in text:
        reply = EXTRACT
    elif "PLAN-ACTIONS" in text:
        reply = PLAN
    else:
        reply = "{}"
    return {
        "output": [{"content": [{"type": "output_text", "text": reply}]}],
        "usage": {"input_tokens": 100, "output_tokens": 50},
    }


def make_client():
    return EmberClient(fake_transport, Ledger())


class TestRunPile(unittest.TestCase):
    def test_one_flyer_text_item_end_to_end(self):
        client = make_client()
        result = run_pile(client, [
            {"id": "item-1", "kind": "text",
             "text": "Science Fair, Dec 12, 9 AM, bring a poster board"},
        ])
        item = result["items"][0]
        self.assertEqual(item["type"], "flyer")
        self.assertEqual(item["extracted"]["people"], ["Amelia"])
        self.assertEqual(len(result["plan"]["actions"]), 2)

    def test_plan_actions_sorted_by_due_date(self):
        # The mock PLAN lists Dec 12 before Dec 5; the pipeline must order.
        client = make_client()
        result = run_pile(client, [
            {"id": "item-1", "kind": "text", "text": "flyer"},
            {"id": "item-2", "kind": "text", "text": "bill"},
        ])
        dues = [a["due"] for a in result["plan"]["actions"]]
        self.assertEqual(dues, sorted(dues))

    def test_conflicts_surfaced(self):
        client = make_client()
        result = run_pile(client, [
            {"id": "item-1", "kind": "text", "text": "flyer"},
        ])
        self.assertEqual(result["plan"]["conflicts"],
                         [{"text": "two items due Dec 5"}])

    def test_every_call_logged_with_cost(self):
        client = make_client()
        run_pile(client, [
            {"id": "item-1", "kind": "text", "text": "flyer"},
        ])
        # 1 classify + 1 extract + 1 plan = 3 calls, each 0.000035.
        self.assertEqual(len(client.ledger.records), 3)
        self.assertAlmostEqual(client.ledger.total(), 3 * 0.000035, places=9)


if __name__ == "__main__":
    unittest.main()
