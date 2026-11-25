"""Tests for the 3-agent pipeline (classify -> extract -> plan).

The transport is fake and answers per agent marker, so no live API call
is made. These tests pin the wiring (shapes, ordering, conflicts, ledger),
not the model's judgment.
"""
import datetime
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pileup.client import EmberClient, Ledger
from pileup.mock import CLASSIFY, EXTRACT, PLAN, fake_transport
from pileup.pipeline import PLAN_PROMPT, extract, run_pile


def make_client():
    return EmberClient(fake_transport, Ledger())


def recording_transport(captured):
    """Fake transport that records each payload before answering."""
    def call(payload):
        text = json.dumps(payload)
        captured.append(text)
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
    return call


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


class TestPromptRules(unittest.TestCase):
    """Regression: live E1 showed the extractor returning iso null for
    'Dec 12, 9 AM' (no year given) and the planner flagging 'missing
    amounts' as a conflict. The prompts must pin both rules."""

    def test_extract_prompt_carries_today_and_year_rule(self):
        captured = []
        client = EmberClient(recording_transport(captured), Ledger())
        extract(client, {"id": "t1", "kind": "text", "text": "flyer"},
                "flyer")
        prompt = next(p for p in captured if "EXTRACT-FIELDS" in p)
        self.assertIn(datetime.date.today().isoformat(), prompt)
        self.assertIn("assume the current year", prompt)

    def test_plan_prompt_only_flags_real_conflicts(self):
        self.assertNotIn("missing amounts", PLAN_PROMPT)
        self.assertIn("not a conflict", PLAN_PROMPT)


if __name__ == "__main__":
    unittest.main()
