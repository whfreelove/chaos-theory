"""Non-fixture test helper functions for FSM tests.

Loaded by conftest.py via importlib.util.spec_from_file_location and exposed
as session-scoped fixtures. Not importable via bare import statements under
importmode = "importlib".
"""

import json
import os
import subprocess
from pathlib import Path


def _make_task_file(task_dir, task_id, status, fsm_value="test-skill"):
    """Helper to create task files with consistent format."""
    (task_dir / f"{task_id}.json").write_text(json.dumps({
        "id": str(task_id), "subject": f"Task {task_id}", "description": "",
        "activeForm": "", "owner": "", "status": status,
        "blocks": [], "blockedBy": [],
        "metadata": {"fsm": fsm_value}
    }))


def run_hook(
    session_id: str,
    command_name: str,
    cwd: str,
    task_root: str | None = None,
    plugins_file: str | None = None,
    user_skills_root: str | None = None,
) -> tuple[int, str, str]:
    """Execute hook script with JSON stdin, return (exit_code, stdout, stderr)."""
    script_path = Path(__file__).resolve().parents[3] / "plugins" / "finite-skill-machine" / "scripts" / "hydrate-tasks.py"

    stdin_data = {
        "session_id": session_id,
        "cwd": cwd,
        "tool_response": {"commandName": command_name}
    }

    env = os.environ.copy()
    if task_root:
        env["FSM_TASK_ROOT"] = task_root
    if plugins_file:
        env["FSM_PLUGINS_FILE"] = plugins_file
    if user_skills_root:
        env["FSM_USER_SKILLS_ROOT"] = user_skills_root

    result = subprocess.run(
        ["python3", str(script_path)],
        input=json.dumps(stdin_data),
        capture_output=True,
        text=True,
        env=env
    )
    return result.returncode, result.stdout, result.stderr
