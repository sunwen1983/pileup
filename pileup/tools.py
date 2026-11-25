"""Talk to MCP backends over stdio and execute a plan through them.

The wire shape is JSON-RPC 2.0, one object per line, protocolVersion
"2025-03-26" (the same shape mcpgate's echo-backend uses). The PileUp
server uses this to turn planned actions into real tool calls: dated
actions become calendar events, undated ones become reminders.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def backend_argv(name: str) -> list[str]:
    return [sys.executable, str(ROOT / "tools" / "mock_tools.py"), name]


class MCPStdioClient:
    """One MCP server process, driven over stdin/stdout."""

    def __init__(self, argv):
        self.argv = argv
        self.proc = None
        self._next_id = 0

    def __enter__(self):
        self.proc = subprocess.Popen(
            self.argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            text=True, bufsize=1)
        self._request("initialize", {"protocolVersion": "2025-03-26",
                                     "capabilities": {},
                                     "clientInfo": {"name": "pileup",
                                                    "version": "0.1.0"}})
        self._notify("notifications/initialized")
        return self

    def __exit__(self, *exc):
        if self.proc is not None:
            try:
                self.proc.stdin.close()
            except BrokenPipeError:
                pass
            self.proc.wait(timeout=5)
            self.proc = None
        return False

    def _request(self, method, params=None):
        self._next_id += 1
        req = {"jsonrpc": "2.0", "id": self._next_id, "method": method}
        if params is not None:
            req["params"] = params
        self.proc.stdin.write(json.dumps(req) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        if not line:
            raise RuntimeError(f"{method}: backend closed the connection")
        resp = json.loads(line)
        if "error" in resp:
            err = resp["error"]
            raise RuntimeError(f"{method}: {err.get('message')} "
                               f"(code {err.get('code')})")
        return resp.get("result", {})

    def _notify(self, method):
        self.proc.stdin.write(json.dumps(
            {"jsonrpc": "2.0", "method": method}) + "\n")
        self.proc.stdin.flush()

    def list_tools(self):
        return self._request("tools/list").get("tools", [])

    def call(self, name, arguments):
        result = self._request("tools/call",
                               {"name": name, "arguments": arguments})
        return result.get("structuredContent", result)


def execute_plan_actions(actions, calendar_factory=None,
                         reminders_factory=None):
    """Execute plan actions: dated -> calendar event, undated -> reminder.

    Returns a list of {action, tool, result}. The factories default to the
    mock backends; tests pass fakes.
    """
    calendar_factory = calendar_factory or (
        lambda: MCPStdioClient(backend_argv("calendar")))
    reminders_factory = reminders_factory or (
        lambda: MCPStdioClient(backend_argv("reminders")))
    done = []
    with calendar_factory() as calendar, reminders_factory() as reminders:
        for action in actions:
            due = action.get("due")
            if due:
                result = calendar.call("calendar.create_event", {
                    "title": action.get("text", ""),
                    "start": due + "T09:00:00"})
                done.append({"action": action, "tool": "calendar.create_event",
                             "result": result})
            else:
                result = reminders.call("reminders.create", {
                    "text": action.get("text", ""), "due": None})
                done.append({"action": action, "tool": "reminders.create",
                             "result": result})
    return done
