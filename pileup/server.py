"""PileUp server (stdlib only, no dependencies).

Routes:
  GET  /              the UI (public/index.html)
  GET  /api/health    {"ok": true, "transport": "mock"|"live"}
  GET  /demo/pile.json  the demo pile fixture
  POST /api/run       {"items": [...]} -> {items, plan, ledger, total_cost_usd}

Transport: PILEUP_TRANSPORT=mock (default, canned replies, free) or live
(real Ember; needs MODEL_API_KEY or the VM surrogate). Budget:
PILEUP_BUDGET_USD (default 10.0). Each run's ledger is appended to
traces/run-<timestamp>.jsonl when PILEUP_TRACE_DIR is set (default traces/).
"""
from __future__ import annotations

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from pileup.client import EmberClient, Ledger
from pileup.mock import fake_transport
from pileup.pipeline import run_pile
from pileup.tools import execute_plan_actions
from pileup.transport import live_request_fn

ROOT = Path(__file__).resolve().parent.parent


def make_client() -> tuple[EmberClient, str]:
    transport = os.environ.get("PILEUP_TRANSPORT", "mock").lower()
    budget = float(os.environ.get("PILEUP_BUDGET_USD", "10.0"))
    trace_dir = os.environ.get("PILEUP_TRACE_DIR", "traces")
    ledger = Ledger()
    ledger.path = None  # set per run below; the client only tracks totals
    if transport == "live":
        client = EmberClient(live_request_fn(), ledger, budget_usd=budget)
    else:
        client = EmberClient(fake_transport, ledger, budget_usd=budget)
    return client, transport


def trace_path(trace_dir: str) -> str:
    Path(trace_dir).mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    return os.path.join(trace_dir, f"run-{stamp}.jsonl")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # keep the console quiet
        pass

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str) -> None:
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/health":
            _, transport = make_client()
            self._send_json(200, {"ok": True, "transport": transport})
            return
        if self.path == "/demo/pile.json":
            self._send_file(ROOT / "demo" / "pile.json", "application/json")
            return
        if self.path in ("/", "/index.html"):
            self._send_file(ROOT / "public" / "index.html", "text/html")
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/run":
            self._send_json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
            items = body.get("items")
            if not isinstance(items, list) or not items:
                raise ValueError("items must be a non-empty list")
        except (ValueError, json.JSONDecodeError) as exc:
            self._send_json(400, {"error": f"bad request: {exc}"})
            return
        client, transport = make_client()
        try:
            result = run_pile(client, items)
        except Exception as exc:  # model/transport failure: report, don't crash
            self._send_json(502, {"error": str(exc)})
            return
        tool_results = None
        tool_error = None
        if body.get("execute") and os.environ.get("PILEUP_TOOLS", "on") != "off":
            try:
                tool_results = execute_plan_actions(result["plan"]["actions"])
            except Exception as exc:
                tool_error = str(exc)
        trace_dir = os.environ.get("PILEUP_TRACE_DIR", "traces")
        path = trace_path(trace_dir)
        with open(path, "a", encoding="utf-8") as handle:
            for record in client.ledger.records:
                handle.write(json.dumps(record) + "\n")
        self._send_json(200, {
            "items": result["items"],
            "plan": result["plan"],
            "tool_results": tool_results,
            "tool_error": tool_error,
            "ledger": client.ledger.records,
            "total_cost_usd": round(client.ledger.total(), 6),
            "transport": transport,
            "trace_file": path,
        })


def create_server(port: int = 0, host: str | None = None) -> ThreadingHTTPServer:
    host = host or os.environ.get("HOST", "0.0.0.0")
    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    server = create_server(port)
    print(f"PileUp on http://{server.server_address[0]}:{server.server_address[1]} "
          f"(transport={os.environ.get('PILEUP_TRANSPORT', 'mock')})")
    server.serve_forever()


if __name__ == "__main__":
    main()
