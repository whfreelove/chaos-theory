#!/usr/bin/env python3
import json, sys
from pathlib import Path

CAPTURE_FILE = Path("/tmp/claude/pre-tool-use-capture.jsonl")
CAPTURE_FILE.parent.mkdir(parents=True, exist_ok=True)

event = json.loads(sys.stdin.read())
with CAPTURE_FILE.open("a") as f:
    f.write(json.dumps(event) + "\n")

print(json.dumps({"continue": True}))
