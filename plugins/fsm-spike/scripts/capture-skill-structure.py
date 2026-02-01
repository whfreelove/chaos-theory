#!/usr/bin/env python3
"""
Spike: Capture the full Skill tool_response structure.
Triggered by PostToolUse on Skill.
"""
import json
import sys
from pathlib import Path
from datetime import datetime

OUTPUT_FILE = Path("/tmp/claude/fsm-skill-capture.json")

def main():
    try:
        # Read hook input from stdin
        hook_input = sys.stdin.read()

        if not hook_input:
            print(json.dumps({"continue": True}))
            return

        hook_data = json.loads(hook_input)

        # Capture full structure with timestamp
        capture = {
            "timestamp": datetime.now().isoformat(),
            "top_level_keys": list(hook_data.keys()),
            "full_data": hook_data
        }

        # Ensure output directory exists
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Append to file (each capture on new line)
        with OUTPUT_FILE.open("a") as f:
            f.write(json.dumps(capture, indent=2, default=str) + "\n---\n")

        print(f"FSM-SPIKE: Captured Skill structure to {OUTPUT_FILE}", file=sys.stderr)

    except Exception as e:
        print(f"FSM-SPIKE: ERROR - {type(e).__name__}: {e}", file=sys.stderr)

    print(json.dumps({"continue": True}))

if __name__ == '__main__':
    main()
