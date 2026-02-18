#!/usr/bin/env python3
import json, sys
from pathlib import Path

RESPONSE_FILE = Path("/tmp/claude/pre-tool-use-response.json")

if RESPONSE_FILE.exists():
    response = json.loads(RESPONSE_FILE.read_text())
else:
    response = {"continue": True}

print(json.dumps(response))
