#!/usr/bin/env python3
"""PreToolUse hook A — logs when fired and returns a configurable response.

Reads response from /tmp/claude/hook-a-response.json (defaults to continue: true).
Appends invocation record to /tmp/claude/hook-a-log.jsonl.
"""
import json, sys, time
from pathlib import Path

LOG_FILE = Path("/tmp/claude/hook-a-log.jsonl")
RESPONSE_FILE = Path("/tmp/claude/hook-a-response.json")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

event = json.loads(sys.stdin.read())

# Log the invocation with timestamp
log_entry = {
    "hook": "A",
    "timestamp": time.time(),
    "tool_name": event.get("tool_name", "unknown"),
    "tool_input": event.get("tool_input", {}),
}
with LOG_FILE.open("a") as f:
    f.write(json.dumps(log_entry) + "\n")

# Return configured response
if RESPONSE_FILE.exists():
    response = json.loads(RESPONSE_FILE.read_text())
else:
    response = {"continue": True}

print(json.dumps(response))
