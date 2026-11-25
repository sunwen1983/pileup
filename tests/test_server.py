"""Tests for the PileUp server (stdlib unittest, mock transport).

Starts a real server on an ephemeral port and talks to it over HTTP.
"""
import http.client
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["PILEUP_TRANSPORT"] = "mock"
os.environ["PILEUP_TRACE_DIR"] = tempfile.mkdtemp(prefix="pileup-traces-")

from pileup.server import create_server  # noqa: E402


def request(server, method, path, body=None):
    conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1],
                                     timeout=10)
    headers = {"Content-Type": "application/json"} if body is not None else {}
    conn.request(method, path,
                 body=json.dumps(body) if body is not None else None,
                 headers=headers)
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    return resp.status, json.loads(data) if data else {}


class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server(0)
        cls.thread = threading.Thread(target=cls.server.serve_forever,
                                      daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_health(self):
        status, body = request(self.server, "GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(body, {"ok": True, "transport": "mock"})

    def test_index_serves_ui(self):
        conn = http.client.HTTPConnection("127.0.0.1",
                                          self.server.server_address[1],
                                          timeout=10)
        conn.request("GET", "/")
        resp = conn.getresponse()
        self.assertEqual(resp.status, 200)
        self.assertIn("PileUp", resp.read().decode("utf-8"))
        conn.close()

    def test_run_demo_pile_mock(self):
        pile = json.loads(
            (Path(__file__).resolve().parent.parent / "demo" / "pile.json")
            .read_text())
        status, body = request(self.server, "POST", "/api/run", pile)
        self.assertEqual(status, 200)
        # 5 items x (classify + extract) + 1 plan = 11 calls at 0.000035.
        self.assertEqual(len(body["ledger"]), 11)
        self.assertAlmostEqual(body["total_cost_usd"], 11 * 0.000035,
                               places=9)
        self.assertEqual(body["transport"], "mock")
        dues = [a["due"] for a in body["plan"]["actions"]]
        self.assertEqual(dues, sorted(dues))

    def test_run_empty_items_rejected(self):
        status, body = request(self.server, "POST", "/api/run", {"items": []})
        self.assertEqual(status, 400)

    def test_run_bad_json_rejected(self):
        conn = http.client.HTTPConnection("127.0.0.1",
                                          self.server.server_address[1],
                                          timeout=10)
        conn.request("POST", "/api/run", body="{not json",
                     headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        self.assertEqual(resp.status, 400)
        conn.close()


if __name__ == "__main__":
    unittest.main()
