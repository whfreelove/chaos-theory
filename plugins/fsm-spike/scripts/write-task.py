#!/usr/bin/env python3
"""
Spike: Test direct task file writing.
Triggered by PostToolUse on Read.
"""
import json
import sys
from pathlib import Path

# Write to /tmp immediately - if this file exists, hook fired
Path("/tmp/fsm-spike-fired.txt").write_text("Hook fired!\n")

# Immediate startup indicator
print("FSM-SPIKE: ========== HOOK FIRED ==========", file=sys.stderr)

def main():
    try:
        # Read hook input from stdin
        hook_input = sys.stdin.read()
        print(f"FSM-SPIKE: stdin length={len(hook_input)}", file=sys.stderr)

        if not hook_input:
            print("FSM-SPIKE: ERROR - No stdin received", file=sys.stderr)
            print(json.dumps({"continue": True}))
            return

        hook_data = json.loads(hook_input)
        print(f"FSM-SPIKE: hook_data keys={list(hook_data.keys())}", file=sys.stderr)

        # Get session ID from hook input
        session_id = hook_data.get('session_id')
        print(f"FSM-SPIKE: session_id={session_id}", file=sys.stderr)

        if not session_id:
            print("FSM-SPIKE: ERROR - No session_id in hook input", file=sys.stderr)
            print(json.dumps({"continue": True}))
            return

        task_dir = Path.home() / '.claude' / 'tasks' / session_id
        print(f"FSM-SPIKE: Task dir={task_dir}", file=sys.stderr)
        print(f"FSM-SPIKE: Task dir exists={task_dir.exists()}", file=sys.stderr)

        if not task_dir.exists():
            print(f"FSM-SPIKE: ERROR - Task directory does not exist: {task_dir}", file=sys.stderr)
            print(json.dumps({"continue": True}))
            return

        # Write a test task with a high ID to avoid conflicts
        task_id = "9999"
        task_file = task_dir / f"{task_id}.json"
        print(f"FSM-SPIKE: Will write to {task_file}", file=sys.stderr)

        task = {
            "id": task_id,
            "subject": "DIRECT-WRITE-TEST: Written by hook!",
            "description": "This task was written directly to disk by the fsm-spike hook",
            "status": "pending",
            "blocks": [],
            "blockedBy": []
        }

        task_file.write_text(json.dumps(task, indent=2))
        print(f"FSM-SPIKE: SUCCESS - Wrote task to {task_file}", file=sys.stderr)

    except PermissionError as e:
        print(f"FSM-SPIKE: PERMISSION ERROR - {e}", file=sys.stderr)
        print("FSM-SPIKE: macOS sandbox blocking write to ~/.claude/tasks/", file=sys.stderr)
    except Exception as e:
        print(f"FSM-SPIKE: UNEXPECTED ERROR - {type(e).__name__}: {e}", file=sys.stderr)

    # Output valid JSON response
    print(json.dumps({"continue": True}))

if __name__ == '__main__':
    main()
    print("FSM-SPIKE: ========== HOOK COMPLETE ==========", file=sys.stderr)
