#!/usr/bin/env python3
"""Mock MCP backends for PileUp (stdlib only, no dependencies).

One program, two backends, selected by argv[1]. Each process is a minimal
MCP server speaking JSON-RPC 2.0 over stdio, one object per line
(protocolVersion "2025-03-26", modeled on mcpgate's echo-backend shape).
mcpgate spawns one process per backend; the PileUp server can also talk to
them directly through pileup.tools.MCPStdioClient.

    python3 tools/mock_tools.py calendar    # calendar.create_event, list_events
    python3 tools/mock_tools.py reminders   # reminders.create, list

Data is in-memory only and resets when the process exits — every response
says so in its "note" field. These are demo tools, not real accounts.
"""
import json
import sys


class RpcError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def _str(args, key, default=""):
    value = args.get(key, default)
    return value if isinstance(value, str) else default


def _schema(properties, required):
    return {"type": "object", "properties": properties, "required": required}


class Backend:
    def __init__(self, name, tools):
        self.name = name
        self.tools = tools  # list of (name, description, schema, fn)

    def handle(self, req):
        method = req.get("method")
        if method == "initialize":
            return {"protocolVersion": "2025-03-26",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "pileup-mock-" + self.name,
                                   "version": "0.1.0"}}
        if method == "ping":
            return {}
        if method == "tools/list":
            return {"tools": [{"name": n, "description": d, "inputSchema": s}
                              for n, d, s, _ in self.tools]}
        if method == "tools/call":
            params = req.get("params") or {}
            name = params.get("name")
            args = params.get("arguments") or {}
            for tool_name, _, _, fn in self.tools:
                if tool_name == name:
                    result = fn(args)
                    return {"content": [{"type": "text",
                                         "text": json.dumps(result)}],
                            "structuredContent": result}
            raise RpcError(-32602, "unknown tool: " + str(name))
        if method.startswith("notifications/"):
            return None  # notifications get no response
        raise RpcError(-32601, "method not found: " + str(method))


def calendar_backend():
    events = []

    def create_event(args):
        event = {"id": len(events) + 1,
                 "title": _str(args, "title"),
                 "start": _str(args, "start"),
                 "end": _str(args, "end"),
                 "notes": _str(args, "notes"),
                 "note": "mock data — in-memory only, resets on restart"}
        events.append(event)
        return event

    def list_events(args):
        return {"events": list(events),
                "note": "mock data — in-memory only, resets on restart"}

    return Backend("calendar", [
        ("calendar.create_event", "Create a calendar event.",
         _schema({"title": {"type": "string"},
                  "start": {"type": "string"},
                  "end": {"type": "string"},
                  "notes": {"type": "string"}}, ["title", "start"]),
         create_event),
        ("calendar.list_events", "List created events.",
         _schema({}, []), list_events),
    ])


def reminders_backend():
    reminders = []

    def create(args):
        reminder = {"id": len(reminders) + 1,
                    "text": _str(args, "text"),
                    "due": args.get("due"),
                    "note": "mock data — in-memory only, resets on restart"}
        reminders.append(reminder)
        return reminder

    def list_all(args):
        return {"reminders": list(reminders),
                "note": "mock data — in-memory only, resets on restart"}

    return Backend("reminders", [
        ("reminders.create", "Create a reminder.",
         _schema({"text": {"type": "string"},
                  "due": {"type": ["string", "null"]}}, ["text"]),
         create),
        ("reminders.list", "List created reminders.",
         _schema({}, []), list_all),
    ])


def main():
    if len(sys.argv) < 2:
        print("usage: mock_tools.py <calendar|reminders>", file=sys.stderr)
        return 2
    if sys.argv[1] == "calendar":
        backend = calendar_backend()
    elif sys.argv[1] == "reminders":
        backend = reminders_backend()
    else:
        print(f"unknown backend {sys.argv[1]!r} (want calendar|reminders)",
              file=sys.stderr)
        return 2
    print(f"pileup mock {backend.name}: ready", file=sys.stderr)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            _respond(None, None, RpcError(-32700, "parse error"))
            continue
        try:
            result = backend.handle(req)
        except RpcError as exc:
            _respond(req.get("id"), None, exc)
            continue
        if result is not None:
            _respond(req.get("id"), result, None)
    return 0


def _respond(req_id, result, error):
    payload = {"jsonrpc": "2.0", "id": req_id}
    if error is not None:
        payload["error"] = {"code": error.code, "message": error.message}
    else:
        payload["result"] = result
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    raise SystemExit(main())
