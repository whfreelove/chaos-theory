"""Pytest configuration and fixtures for FSM tests."""

import json
import os
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def task_dir(tmp_path):
    """Empty task directory for fresh hydration tests."""
    d = tmp_path / "tasks" / "test-session"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def task_dir_with_manual_task(task_dir):
    """Task directory with a pre-existing manual task."""
    (task_dir / "5.json").write_text(json.dumps({
        "id": "5",
        "subject": "Manual task",
        "description": "",
        "activeForm": "",
        "owner": "",
        "status": "pending",
        "blocks": [],
        "blockedBy": [],
        "metadata": {}
    }))
    return task_dir


@pytest.fixture
def task_dir_with_fsm_tasks(task_dir):
    """Task directory with pre-existing FSM-tagged tasks."""
    (task_dir / "1.json").write_text(json.dumps({
        "id": "1",
        "subject": "FSM task 1",
        "description": "",
        "activeForm": "",
        "owner": "",
        "status": "pending",
        "blocks": [],
        "blockedBy": [],
        "metadata": {"fsm": "other-skill"}
    }))
    (task_dir / "2.json").write_text(json.dumps({
        "id": "2",
        "subject": "FSM task 2",
        "description": "",
        "activeForm": "",
        "owner": "",
        "status": "pending",
        "blocks": [],
        "blockedBy": ["1"],
        "metadata": {"fsm": "other-skill"}
    }))
    return task_dir


@pytest.fixture
def skill_dir(tmp_path):
    """Non-plugin skill directory with fsm.json."""
    d = tmp_path / "project" / ".claude" / "skills" / "test-skill"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def installed_plugins_file(tmp_path):
    """Create installed_plugins.json file."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir(parents=True)
    plugins_file = plugins_dir / "installed_plugins.json"
    return plugins_file


@pytest.fixture
def plugin_install_dir(tmp_path):
    """Plugin installation directory."""
    d = tmp_path / "plugin-install"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def v2_installed_plugins(tmp_path):
    """V2 format installed_plugins.json with one plugin."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir(parents=True)
    plugins_file = plugins_dir / "installed_plugins.json"

    # Create plugin install directory with fsm.json
    install_dir = tmp_path / "my-plugin-install" / "skills" / "my-skill"
    install_dir.mkdir(parents=True)
    (install_dir / "fsm.json").write_text(json.dumps([
        {"id": 1, "subject": "V2 plugin task"}
    ]))

    project_path = str(tmp_path / "myproject")

    plugins_file.write_text(json.dumps({
        "version": 2,
        "plugins": {
            "my-plugin@chaos-theory": [
                {
                    "scope": "project",
                    "projectPath": project_path,
                    "installPath": str(tmp_path / "my-plugin-install")
                }
            ]
        }
    }))

    return plugins_file


@pytest.fixture
def v2_multi_key_plugins(tmp_path):
    """V2 registry with alpha and beta plugins."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir(parents=True)
    plugins_file = plugins_dir / "installed_plugins.json"

    # Alpha plugin
    alpha_dir = tmp_path / "alpha-install" / "skills" / "my-skill"
    alpha_dir.mkdir(parents=True)
    (alpha_dir / "fsm.json").write_text(json.dumps([
        {"id": 1, "subject": "FROM ALPHA"}
    ]))

    # Beta plugin
    beta_dir = tmp_path / "beta-install" / "skills" / "my-skill"
    beta_dir.mkdir(parents=True)
    (beta_dir / "fsm.json").write_text(json.dumps([
        {"id": 1, "subject": "FROM BETA"}
    ]))

    plugins_file.write_text(json.dumps({
        "version": 2,
        "plugins": {
            "alpha@marketplace": [
                {"scope": "user", "installPath": str(tmp_path / "alpha-install")}
            ],
            "beta@marketplace": [
                {"scope": "user", "installPath": str(tmp_path / "beta-install")}
            ]
        }
    }))

    return plugins_file


def run_hook(
    session_id: str,
    command_name: str,
    cwd: str,
    task_root: str | None = None,
    plugins_file: str | None = None,
    user_skills_root: str | None = None,
) -> tuple[int, str, str]:
    """Execute hook script with JSON stdin, return (exit_code, stdout, stderr)."""
    script_path = Path(__file__).parent.parent / "scripts" / "hydrate-tasks.py"

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
