"""Muse Ember client: one Responses call, usage + cost ledger, budget guard.

The transport is injected (``request_fn(payload) -> dict``), the same seam
FixLens uses: the caller owns auth (a surrogate, a key, a test fake), this
module owns the model contract, the cost math and the budget.
"""
from __future__ import annotations

import json
import time

MODEL = "muse-ember-1.0"
# Ember pricing (Participant Guide §01): $0.10 / 1M input, $0.50 / 1M output.
INPUT_PRICE_PER_TOKEN = 0.10 / 1_000_000
OUTPUT_PRICE_PER_TOKEN = 0.50 / 1_000_000


class BudgetExceeded(RuntimeError):
    """Raised before a call that would start at or over the budget."""


def cost_usd(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens * INPUT_PRICE_PER_TOKEN
            + output_tokens * OUTPUT_PRICE_PER_TOKEN)


class Ledger:
    """Append-only record of Ember calls (agent, tokens, cost)."""

    def __init__(self, path: str | None = None):
        self.records: list[dict] = []
        self.path = path

    def record(self, agent: str, input_tokens: int, output_tokens: int) -> dict:
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "agent": agent,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost_usd(input_tokens, output_tokens),
        }
        self.records.append(entry)
        if self.path:
            with open(self.path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry) + "\n")
        return entry

    def total(self) -> float:
        return sum(r["cost_usd"] for r in self.records)


def build_input(item: dict) -> list[dict]:
    """Turn one pile item into Responses API content parts."""
    kind = item.get("kind")
    if kind == "text":
        return [{"type": "input_text", "text": item["text"]}]
    if kind == "image":
        mime = item.get("mime", "image/jpeg")
        return [{"type": "input_image",
                 "image_url": f"data:{mime};base64,{item['data']}"}]
    if kind == "audio":
        return [{"type": "input_audio",
                 "input_audio": {"data": item["data"],
                                 "format": item.get("format", "mp3")}}]
    if kind == "pdf":
        # Shape per the OpenAI-compatible Responses API; verify live in E1.
        return [{"type": "input_file",
                 "filename": item.get("filename", "document.pdf"),
                 "file_data": f"data:application/pdf;base64,{item['data']}"}]
    raise ValueError(f"unknown pile item kind: {kind!r}")


def _output_text(result: dict) -> str:
    if isinstance(result.get("output_text"), str):
        return result["output_text"]
    texts = []
    for item in result.get("output", []) or []:
        for part in item.get("content", []) or []:
            if part.get("type") == "output_text":
                texts.append(part.get("text", ""))
    return "".join(texts)


class EmberClient:
    """One Ember model behind an injected transport, with a hard budget."""

    def __init__(self, request_fn, ledger: Ledger | None = None,
                 budget_usd: float = 10.0, model: str = MODEL):
        self.request_fn = request_fn
        self.ledger = ledger or Ledger()
        self.budget_usd = budget_usd
        self.model = model

    def complete(self, agent: str, parts: list[dict]) -> str:
        if self.ledger.total() >= self.budget_usd:
            raise BudgetExceeded(
                f"Ember budget ${self.budget_usd:.2f} reached "
                f"(spent ${self.ledger.total():.6f}); refusing call for {agent}")
        payload = {"model": self.model,
                   "input": [{"role": "user", "content": parts}]}
        result = self.request_fn(payload)
        text = _output_text(result)
        if not text:
            raise ValueError(f"empty reply from {self.model} for {agent}")
        usage = result.get("usage", {}) or {}
        self.ledger.record(agent, usage.get("input_tokens", 0),
                           usage.get("output_tokens", 0))
        return text
