#!/usr/bin/env python3
"""One-shot Ember connectivity probe (dev only, not part of the product).

POSTs a minimal text input to the Responses API with model muse-ember-1.0
and prints the reply text, token usage and computed cost.

Auth, in order:
1. MODEL_API_KEY env var (off-VM runs: fly.io, a laptop) — used as Bearer.
2. The registered custom.meta-model-api connection (this VM only): each
   request carries only an hsurr: surrogate, swapped in by the runtime for
   the approved host api.meta.ai. The real credential never touches a file,
   an argument, an environment variable or a log.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

try:
    # VM-only: the surrogate lives under /opt/muse, which a laptop
    # (or fly.io) does not have. Guard the import so the probe still
    # runs off-VM with a real MODEL_API_KEY.
    sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
    from dynamic_credentials import (
        DynamicCredentialError,
        add_surrogate_to_request,
        read_json_response,
    )
    _SURROGATE_AVAILABLE = True
except ImportError:
    _SURROGATE_AVAILABLE = False

    def read_json_response(response):
        return json.loads(response.read().decode("utf-8"))

CONNECTION = "custom.meta-model-api"
API_URL = "https://api.meta.ai/v1/responses"
ALLOWED_HOSTS = ["api.meta.ai"]
MODEL = "muse-ember-1.0"
# Ember pricing per guide: $0.10 / 1M input tokens, $0.50 / 1M output tokens.
IN_PRICE = 0.10 / 1_000_000
OUT_PRICE = 0.50 / 1_000_000


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise RuntimeError("redirect refused, verify the endpoint")


def build_request(payload: dict) -> urllib.request.Request:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        API_URL, data=data, method="POST",
        headers={"Content-Type": "application/json"},
    )
    key = os.environ.get("MODEL_API_KEY")
    if key:
        request.add_header("Authorization", f"Bearer {key}")
    else:
        if not _SURROGATE_AVAILABLE:
            raise RuntimeError("no Ember credential: set MODEL_API_KEY")
        add_surrogate_to_request(
            request, CONNECTION, allowed_hosts=ALLOWED_HOSTS)
    return request


def main():
    payload = {
        "model": MODEL,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text",
                     "text": "Reply with exactly this word: OK"}
                ],
            }
        ],
    }
    last_error = None
    for attempt in range(3):
        try:
            with urllib.request.build_opener(NoRedirect()).open(
                    build_request(payload), timeout=150) as response:
                result = read_json_response(response)
            break
        except urllib.error.HTTPError as exc:
            last_error = exc
            body = exc.read().decode("utf-8", "replace")[:500]
            if exc.code not in (404, 429, 500, 502, 503, 504) or attempt == 2:
                raise RuntimeError(
                    f"Meta Model API error {exc.code}: {body}") from exc
            time.sleep(0.5 * (2 ** attempt))
    else:
        raise RuntimeError(f"Meta Model API call failed: {last_error}")

    usage = result.get("usage", {}) or {}
    in_tok = usage.get("input_tokens", 0)
    out_tok = usage.get("output_tokens", 0)
    cost = in_tok * IN_PRICE + out_tok * OUT_PRICE
    texts = []
    for item in result.get("output", []) or []:
        for part in item.get("content", []) or []:
            if part.get("type") == "output_text":
                texts.append(part.get("text", ""))
    print(json.dumps({
        "model": MODEL,
        "reply": "".join(texts),
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "cost_usd": round(cost, 6),
        "raw_keys": sorted(result.keys()),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
