# Mock MCP backends — calendar + reminders

Two minimal MCP servers over stdio (JSON-RPC 2.0, one object per line,
protocolVersion "2025-03-26"), the same wire shape as mcpgate's
echo-backend. They exist so the planner's actions become real tool calls
in the demo: dated actions create calendar events, undated ones create
reminders. Data is in-memory only and resets when the process exits —
every response says so in its `note`.

## Run directly

```bash
python3 tools/mock_tools.py calendar    # calendar.create_event, list_events
python3 tools/mock_tools.py reminders   # reminders.create, list
```

Or from Python: `pileup.tools.MCPStdioClient` spawns one and drives it;
`pileup.tools.execute_plan_actions` routes a plan's actions through both.

## Through mcpgate

mcpgate spawns one process per backend. In `mcpgate/config.yaml`:

```yaml
backends:
  - name: calendar
    command: ["python3", "tools/mock_tools.py", "calendar"]
  - name: reminders
    command: ["python3", "tools/mock_tools.py", "reminders"]
```

(Adjust the path to where this repo is deployed.)

## Swap in real providers later

Keep the tool names and response fields (`calendar.create_event`,
`reminders.create`) and point mcpgate at the real MCP servers instead —
the planner never sees the difference.
