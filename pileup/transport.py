"""Build the live Ember request_fn (transport seam for the server/probe).

Auth, in order:
1. MODEL_API_KEY env var (fly.io secrets, a laptop) — used as Bearer.
2. The registered custom.meta-model-api connection (this VM only): each
   request carries only an hsurr: surrogate, swapped in by the runtime for
   the approved host api.meta.ai.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

API_URL = "https://api.meta.ai/v1/responses"
ALLOWED_HOSTS = ["api.meta.ai"]
_RETRYABLE = {404, 429, 500, 502, 503, 504}

try:
    sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
    from dynamic_credentials import (  # noqa: E402
        add_surrogate_to_request,
        read_json_response,
    )
    _HAVE_SURROGATE = True
except ImportError:  # off-VM: no authd socket, MODEL_API_KEY is the way in.
    _HAVE_SURROGATE = False


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise RuntimeError("redirect refused, verify the endpoint")


def live_request_fn():
    """Return a request_fn(payload) -> dict for the live Responses API."""
    def call(payload: dict) -> dict:
        data = json.dumps(payload).encode("utf-8")
        last_error: Exception | None = None
        for attempt in range(3):
            request = urllib.request.Request(
                API_URL, data=data, method="POST",
                headers={"Content-Type": "application/json"},
            )
            key = os.environ.get("MODEL_API_KEY")
            if key:
                request.add_header("Authorization", f"Bearer {key}")
            elif _HAVE_SURROGATE:
                add_surrogate_to_request(
                    request, "custom.meta-model-api",
                    allowed_hosts=ALLOWED_HOSTS)
            else:
                raise RuntimeError(
                    "no Ember credential: set MODEL_API_KEY")
            try:
                with urllib.request.build_opener(NoRedirect()).open(
                        request, timeout=150) as response:
                    return read_json_response(response)
            except urllib.error.HTTPError as exc:
                last_error = exc
                body = exc.read().decode("utf-8", "replace")[:500]
                if exc.code not in _RETRYABLE or attempt == 2:
                    raise RuntimeError(
                        f"Meta Model API error {exc.code}: {body}") from exc
                time.sleep(0.5 * (2 ** attempt))
        raise RuntimeError(f"Meta Model API call failed: {last_error}")

    return call
