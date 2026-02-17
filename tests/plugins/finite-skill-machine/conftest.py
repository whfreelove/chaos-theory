"""Pytest configuration and fixtures for FSM tests."""

import importlib.util
import json
from pathlib import Path

import pytest

# Load helpers.py via importlib.util (bare imports fail under importmode = "importlib")
_helpers_spec = importlib.util.spec_from_file_location(
    "helpers", Path(__file__).parent / "helpers.py"
)
_helpers_module = importlib.util.module_from_spec(_helpers_spec)
_helpers_spec.loader.exec_module(_helpers_module)

# Module-level references for conftest's own fixture use
_make_task_file = _helpers_module._make_task_file


@pytest.fixture(scope="session")
def run_hook():
    """Session-scoped fixture returning the run_hook callable from helpers.py."""
    return _helpers_module.run_hook


@pytest.fixture(scope="session")
def make_task_file():
    """Session-scoped fixture returning the _make_task_file callable from helpers.py."""
    return _helpers_module._make_task_file


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
        "metadata": {"fsm": "test-skill"}
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
        "metadata": {"fsm": "test-skill"}
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


@pytest.fixture
def hydrate_module():
    """Import hydrate-tasks.py as a module for direct function testing."""
    import importlib.util
    script_path = Path(__file__).resolve().parents[3] / "plugins" / "finite-skill-machine" / "scripts" / "hydrate-tasks.py"
    spec = importlib.util.spec_from_file_location("hydrate_tasks", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def task_dir_all_pending(task_dir):
    """Task directory with all-pending matching tasks."""
    _make_task_file(task_dir, 1, "pending")
    _make_task_file(task_dir, 2, "pending")
    return task_dir


@pytest.fixture
def task_dir_all_completed(task_dir):
    """Task directory with all-completed matching tasks."""
    _make_task_file(task_dir, 1, "completed")
    _make_task_file(task_dir, 2, "completed")
    return task_dir


@pytest.fixture
def task_dir_all_in_progress(task_dir):
    """Task directory with all-in_progress matching tasks."""
    _make_task_file(task_dir, 1, "in_progress")
    _make_task_file(task_dir, 2, "in_progress")
    return task_dir


@pytest.fixture
def task_dir_mixed_completed_pending(task_dir):
    """Task directory with mixed completed+pending tasks."""
    _make_task_file(task_dir, 1, "completed")
    _make_task_file(task_dir, 2, "pending")
    return task_dir


@pytest.fixture
def task_dir_mixed_in_progress_completed(task_dir):
    """Task directory with mixed in_progress+completed tasks."""
    _make_task_file(task_dir, 1, "in_progress")
    _make_task_file(task_dir, 2, "completed")
    return task_dir


