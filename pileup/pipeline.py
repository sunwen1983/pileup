"""The three-agent pipeline: classify -> extract -> plan.

Each agent is one Ember call with a JSON-only reply. The pipeline owns the
wiring (shapes, ordering, conflicts); the model owns the judgment.
"""
from __future__ import annotations

import datetime
import json

from .client import build_input

CLASSIFY_PROMPT = (
    "CLASSIFY-ITEM\n"
    "You classify one messy pile item. Reply with JSON only, no other text:\n"
    '{"type": one of flyer, bill, voice_memo, chat, note, other, '
    '"confidence": 0.0-1.0}.'
)

EXTRACT_PROMPT = (
    "EXTRACT-FIELDS\n"
    "You extract structured fields from one pile item of type {item_type}. "
    "Today is {today}. Reply with JSON only, no other text:\n"
    '{"dates": [{"text": ..., "iso": "YYYY-MM-DDTHH:MM:SS or null"}], '
    '"amounts": [{"text": ..., "value": number, "currency": "USD"}], '
    '"people": [...], '
    '"actions": [{"text": ..., "due": "YYYY-MM-DD or null"}]}. '
    "Use null when a field is absent. When a date has no year, assume "
    "the current year; when it has no time, use 09:00."
)

PLAN_PROMPT = (
    "PLAN-ACTIONS\n"
    "You are given extracted pile items as JSON. Reply with JSON only, "
    "no other text:\n"
    '{"actions": [{"text": ..., "due": "YYYY-MM-DD or null", '
    '"source": item id}], "conflicts": [{"text": ...}]}. '
    "Order actions by due date. Flag only real conflicts: two actions "
    "due on the same date, or an action whose due date is already past. "
    "A missing date or a missing amount is not a conflict."
)


def _as_json(text: str, what: str) -> dict:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{what} did not reply with JSON: {text[:200]}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{what} reply was not a JSON object: {text[:200]}")
    return parsed


def classify(client, item: dict) -> dict:
    parts = [{"type": "input_text", "text": CLASSIFY_PROMPT}]
    parts += build_input(item)
    return _as_json(client.complete("classify", parts), "classifier")


def extract(client, item: dict, item_type: str) -> dict:
    # .replace, not .format: the prompt's literal JSON braces must survive.
    prompt = (EXTRACT_PROMPT
              .replace("{item_type}", item_type)
              .replace("{today}", datetime.date.today().isoformat()))
    parts = [{"type": "input_text", "text": prompt}]
    parts += build_input(item)
    return _as_json(client.complete("extract", parts), "extractor")


def plan(client, extracted_items: list[dict]) -> dict:
    parts = [{"type": "input_text",
              "text": PLAN_PROMPT + "\n" + json.dumps(extracted_items)}]
    raw = _as_json(client.complete("plan", parts), "planner")
    actions = sorted(raw.get("actions", []),
                     key=lambda a: (a.get("due") is None, a.get("due") or ""))
    return {"actions": actions, "conflicts": raw.get("conflicts", [])}


def run_pile(client, items: list[dict]) -> dict:
    """Run a whole pile through classify -> extract -> plan."""
    done = []
    for item in items:
        found = classify(client, item)
        item_type = found.get("type", "other")
        fields = extract(client, item, item_type)
        done.append({"id": item.get("id"), "type": item_type,
                     "confidence": found.get("confidence"),
                     "extracted": fields})
    return {"items": done, "plan": plan(client, done)}
