"""Tests for the mock MCP tool backends and the plan executor.

The backends are real subprocesses speaking JSON-RPC 2.0 over stdio
(modeled on mcpgate's echo-backend shape); the executor is tested through
a fake client and through the server's /api/run with execute=true.
"""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pileup.tools import MCPStdioClient, execute_plan_actions  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MOCK = [sys.executable, str(ROOT / "tools" / "mock_tools.py")]


class FakeClient:
    """Records tool calls instead of spawning a process."""

    def __init__(self):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def call(self, name, arguments):
        self.calls.append((name, arguments))
        return {"id": len(self.calls), "note": "fake"}


class TestMockBackends(unittest.TestCase):
    def test_calendar_create_and_list(self):
        with MCPStdioClient(MOCK + ["calendar"]) as client:
            tools = client.list_tools()
            names = [t["name"] for t in tools]
            self.assertIn("calendar.create_event", names)
            self.assertIn("calendar.list_events", names)
            event = client.call("calendar.create_event", {
                "title": "pay the bill", "start": "2026-12-05T09:00:00"})
            self.assertEqual(event["title"], "pay the bill")
            self.assertEqual(event["id"], 1)
            listed = client.call("calendar.list_events", {})
            self.assertEqual(len(listed["events"]), 1)

    def test_reminders_create_and_list(self):
        with MCPStdioClient(MOCK + ["reminders"]) as client:
            reminder = client.call("reminders.create", {
                "text": "call the plumber", "due": None})
            self.assertEqual(reminder["text"], "call the plumber")
            self.assertEqual(reminder["id"], 1)
            listed = client.call("reminders.list", {})
            self.assertEqual(len(listed["reminders"]), 1)

    def test_unknown_tool_is_an_error(self):
        with MCPStdioClient(MOCK + ["calendar"]) as client:
            with self.assertRaises(RuntimeError):
                client.call("calendar.nope", {})

    def test_unknown_dataset_exits_nonzero(self):
        proc = subprocess.run(MOCK + ["nope"], capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)


class TestExecutePlan(unittest.TestCase):
    def test_dated_goes_to_calendar_undated_to_reminders(self):
        fake = FakeClient()
        results = execute_plan_actions(
            [{"text": "pay the bill", "due": "2026-12-05"},
             {"text": "call the plumber", "due": None}],
            calendar_factory=lambda: fake,
            reminders_factory=lambda: fake)
        self.assertEqual(len(results), 2)
        self.assertEqual(fake.calls[0][0], "calendar.create_event")
        self.assertEqual(fake.calls[0][1]["title"], "pay the bill")
        self.assertEqual(fake.calls[1][0], "reminders.create")
        self.assertEqual(fake.calls[1][1]["text"], "call the plumber")


if __name__ == "__main__":
    unittest.main()
