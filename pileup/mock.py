"""Canned Ember transport for demos and tests (no live API call).

Answers per agent marker with fixed JSON, so the pipeline wiring, the
ordering and the ledger can be exercised without spending a cent.
"""
import json

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
