"""Tests for the Ember client: cost math, ledger, budget guard, parsing.

Runs on stdlib unittest only (no pytest in this environment).
The transport is a fake request_fn, so no live API call is made.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pileup.client import BudgetExceeded, EmberClient, Ledger, build_input


def fake_transport(usage=None, text="OK"):
    """Return a request_fn that answers with a canned Responses payload."""
    usage = usage or {"input_tokens": 100, "output_tokens": 50}

    def call(payload):
        return {
            "output": [
                {"type": "message",
                 "content": [{"type": "output_text", "text": text}]}
            ],
            "usage": dict(usage),
        }

    return call


class TestCostMath(unittest.TestCase):
    def test_100_in_50_out_costs_0_000035(self):
        # $0.10/1M in + $0.50/1M out (independent of the code under test).
        ledger = Ledger()
        client = EmberClient(fake_transport(), ledger)
        client.complete("probe", build_input({"kind": "text", "text": "hi"}))
        self.assertAlmostEqual(ledger.total(), 0.000035, places=9)


class TestBudgetGuard(unittest.TestCase):
    def test_second_call_refused_once_budget_reached(self):
        ledger = Ledger()
        # One call costs 0.000035, so a 0.00001 budget is spent after call 1.
        client = EmberClient(fake_transport(), ledger, budget_usd=0.00001)
        client.complete("probe", build_input({"kind": "text", "text": "hi"}))
        with self.assertRaises(BudgetExceeded):
            client.complete("probe", build_input({"kind": "text", "text": "hi"}))

    def test_call_at_exact_budget_is_refused(self):
        ledger = Ledger()
        ledger.record("probe", 100, 50)  # 0.000035
        client = EmberClient(fake_transport(), ledger, budget_usd=0.000035)
        with self.assertRaises(BudgetExceeded):
            client.complete("probe", build_input({"kind": "text", "text": "hi"}))


class TestLedger(unittest.TestCase):
    def test_record_and_total(self):
        ledger = Ledger()
        ledger.record("classify", 1000, 200)
        ledger.record("extract", 2000, 400)
        # (1000+2000)*0.10/1e6 + (200+400)*0.50/1e6 = 0.0003 + 0.0003
        self.assertAlmostEqual(ledger.total(), 0.0006, places=9)
        self.assertEqual(len(ledger.records), 2)
        self.assertEqual(ledger.records[0]["agent"], "classify")


class TestParsing(unittest.TestCase):
    def test_joins_output_text_parts(self):
        def call(payload):
            return {
                "output": [
                    {"content": [{"type": "output_text", "text": "hel"},
                                 {"type": "output_text", "text": "lo"}]},
                ],
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }

        client = EmberClient(call, Ledger())
        self.assertEqual(
            client.complete("probe", build_input({"kind": "text", "text": "hi"})),
            "hello")


class TestBuildInput(unittest.TestCase):
    def test_text_item_becomes_input_text(self):
        parts = build_input({"kind": "text", "text": "hello"})
        self.assertEqual(parts, [{"type": "input_text", "text": "hello"}])

    def test_image_item_becomes_input_image_data_url(self):
        parts = build_input({"kind": "image", "data": "aGVsbG8=",
                             "mime": "image/png"})
        self.assertEqual(parts, [{"type": "input_image",
                                  "image_url": "data:image/png;base64,aGVsbG8="}])

    def test_audio_item_becomes_input_audio(self):
        parts = build_input({"kind": "audio", "data": "aGVsbG8=",
                             "format": "mp3"})
        self.assertEqual(parts, [{"type": "input_audio",
                                  "input_audio": {"data": "aGVsbG8=",
                                                  "format": "mp3"}}])

    def test_unknown_kind_raises(self):
        with self.assertRaises(ValueError):
            build_input({"kind": "smoke-signal", "text": "hi"})


if __name__ == "__main__":
    unittest.main()
