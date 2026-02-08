"""Tests for the FSM hydrate-tasks hook."""

import json
from pathlib import Path

import pytest

from conftest import run_hook


class TestStdinParsing:
    """REQ-THS-1: Skill tool triggers FSM hook."""

    def test_missing_session_id_fails(self, tmp_path):
        """SCN-THS-1.3: Missing session_id fails the hook."""
        import subprocess

        script_path = Path(__file__).parent.parent / "scripts" / "hydrate-tasks.py"
        stdin_data = {
            "cwd": "/tmp",
            "tool_response": {"commandName": "test-skill"}
        }

        result = subprocess.run(
            ["python3", str(script_path)],
            input=json.dumps(stdin_data),
            capture_output=True,
            text=True
        )

        assert result.returncode != 0
        assert "session_id" in result.stderr

    def test_missing_command_name_fails(self, tmp_path):
        """SCN-THS-1.4: Missing commandName fails the hook."""
        import subprocess

        script_path = Path(__file__).parent.parent / "scripts" / "hydrate-tasks.py"
        stdin_data = {
            "session_id": "test-123",
            "cwd": "/tmp",
            "tool_response": {}
        }

        result = subprocess.run(
            ["python3", str(script_path)],
            input=json.dumps(stdin_data),
            capture_output=True,
            text=True
        )

        assert result.returncode != 0
        assert "commandName" in result.stderr

    def test_malformed_stdin_fails(self, tmp_path):
        """SCN-THS-1.5: Malformed stdin JSON fails the hook."""
        import subprocess

        script_path = Path(__file__).parent.parent / "scripts" / "hydrate-tasks.py"

        result = subprocess.run(
            ["python3", str(script_path)],
            input="not valid json",
            capture_output=True,
            text=True
        )

        assert result.returncode != 0
        assert "parse" in result.stderr.lower() or "json" in result.stderr.lower()


class TestFsmJsonValidation:
    """REQ-THS-4: Hook validates fsm.json atomically."""

    def test_valid_fsm_creates_tasks(self, task_dir, skill_dir):
        """SCN-THS-4.1: Valid fsm.json creates tasks."""
        fsm_json = [
            {"id": 1, "subject": "Task one"},
            {"id": 2, "subject": "Task two", "blockedBy": [1]}
        ]
        (skill_dir / "fsm.json").write_text(json.dumps(fsm_json))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        assert exit_code == 0
        assert json.loads(stdout) == {"continue": True}
        assert (task_dir / "1.json").exists()
        assert (task_dir / "2.json").exists()

    def test_malformed_json_fails(self, task_dir, skill_dir):
        """SCN-THS-4.2: Malformed JSON fails the hook."""
        (skill_dir / "fsm.json").write_text("not valid json [")

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        assert exit_code != 0
        assert "malformed" in stderr.lower() or "json" in stderr.lower()

    def test_missing_id_fails(self, task_dir, skill_dir):
        """SCN-THS-4.3: Missing required field fails the hook."""
        fsm_json = [{"subject": "No ID task"}]
        (skill_dir / "fsm.json").write_text(json.dumps(fsm_json))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        assert exit_code != 0
        assert "id" in stderr.lower()

    def test_missing_subject_fails(self, task_dir, skill_dir):
        """SCN-THS-4.3: Missing subject field fails the hook."""
        fsm_json = [{"id": 1}]
        (skill_dir / "fsm.json").write_text(json.dumps(fsm_json))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        assert exit_code != 0
        assert "subject" in stderr.lower()

    def test_duplicate_ids_fail(self, task_dir, skill_dir):
        """SCN-THS-4.4: Duplicate IDs fail the hook."""
        fsm_json = [
            {"id": 1, "subject": "First"},
            {"id": 1, "subject": "Duplicate"}
        ]
        (skill_dir / "fsm.json").write_text(json.dumps(fsm_json))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        assert exit_code != 0
        assert "duplicate" in stderr.lower()

    def test_invalid_dependency_fails(self, task_dir, skill_dir):
        """SCN-THS-4.5: Invalid dependency reference fails the hook."""
        fsm_json = [{"id": 1, "subject": "Task", "blockedBy": [99]}]
        (skill_dir / "fsm.json").write_text(json.dumps(fsm_json))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        assert exit_code != 0
        assert "99" in stderr

    def test_multiple_errors_reported(self, task_dir, skill_dir):
        """SCN-THS-4.6: Multiple errors reported together."""
        fsm_json = [
            {"id": 1, "subject": "Valid"},
            {"id": 1, "subject": "Duplicate"},
            {"id": 3, "blockedBy": [99]}  # Missing subject AND invalid ref
        ]
        (skill_dir / "fsm.json").write_text(json.dumps(fsm_json))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        assert exit_code != 0
        # Should report multiple errors
        assert "duplicate" in stderr.lower()
        assert "subject" in stderr.lower()
        assert "99" in stderr

    def test_task_file_structure(self, task_dir, skill_dir):
        """SCN-THS-4.7: Task files written with correct structure."""
        fsm_json = [{
            "id": 1,
            "subject": "Set up environment",
            "description": "Install deps",
            "activeForm": "Setting up"
        }]
        (skill_dir / "fsm.json").write_text(json.dumps(fsm_json))

        run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        task = json.loads((task_dir / "1.json").read_text())

        # Verify structure per spec
        assert task["id"] == "1"  # String, not number
        assert task["subject"] == "Set up environment"
        assert task["description"] == "Install deps"
        assert task["activeForm"] == "Setting up"
        assert task["status"] == "pending"
        assert task["owner"] == ""
        assert task["blocks"] == []
        assert task["blockedBy"] == []
        assert task["metadata"]["fsm"] == "test-skill"


class TestIdTranslation:
    """REQ-THS-5: Hook translates local IDs to actual IDs."""

    def test_empty_task_dir_no_offset(self, task_dir, skill_dir):
        """SCN-THS-5.1: Empty task directory - IDs start at 1."""
        fsm_json = [{"id": 1, "subject": "Task"}]
        (skill_dir / "fsm.json").write_text(json.dumps(fsm_json))

        run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        assert (task_dir / "1.json").exists()
        task = json.loads((task_dir / "1.json").read_text())
        assert task["id"] == "1"

    def test_existing_tasks_offset_ids(self, task_dir_with_manual_task, skill_dir):
        """SCN-THS-5.2: Existing tasks offset new IDs."""
        fsm_json = [
            {"id": 1, "subject": "Task 1"},
            {"id": 2, "subject": "Task 2"},
            {"id": 3, "subject": "Task 3"}
        ]
        (skill_dir / "fsm.json").write_text(json.dumps(fsm_json))

        run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir_with_manual_task.parent)
        )

        # Manual task is 5, so new tasks should be 6, 7, 8
        assert (task_dir_with_manual_task / "6.json").exists()
        assert (task_dir_with_manual_task / "7.json").exists()
        assert (task_dir_with_manual_task / "8.json").exists()

    def test_dependencies_use_translated_ids(self, task_dir_with_manual_task, skill_dir):
        """SCN-THS-5.3: Dependencies use translated IDs."""
        fsm_json = [
            {"id": 1, "subject": "Task 1"},
            {"id": 2, "subject": "Task 2", "blockedBy": [1]}
        ]
        (skill_dir / "fsm.json").write_text(json.dumps(fsm_json))

        run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir_with_manual_task.parent)
        )

        # Local 1 -> Actual 6, Local 2 -> Actual 7
        task7 = json.loads((task_dir_with_manual_task / "7.json").read_text())
        assert task7["blockedBy"] == ["6"]  # String IDs


class TestFsmMetadata:
    """REQ-THS-6: Hook tags tasks with FSM metadata."""

    def test_fsm_tag_added(self, task_dir, skill_dir):
        """SCN-THS-6.1: Created task includes fsm tag."""
        fsm_json = [{"id": 1, "subject": "Task"}]
        (skill_dir / "fsm.json").write_text(json.dumps(fsm_json))

        run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        task = json.loads((task_dir / "1.json").read_text())
        assert task["metadata"]["fsm"] == "test-skill"

    def test_custom_metadata_preserved(self, task_dir, skill_dir):
        """SCN-THS-6.2: Custom metadata preserved."""
        fsm_json = [{"id": 1, "subject": "Task", "metadata": {"custom": "value"}}]
        (skill_dir / "fsm.json").write_text(json.dumps(fsm_json))

        run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        task = json.loads((task_dir / "1.json").read_text())
        assert task["metadata"]["custom"] == "value"
        assert task["metadata"]["fsm"] == "test-skill"


class TestFsmTaskDeletion:
    """REQ-THS-7: Hook deletes FSM-tagged tasks before writing."""

    def test_fsm_tasks_deleted(self, task_dir_with_fsm_tasks, skill_dir):
        """SCN-THS-7.1: Previous FSM tasks deleted."""
        fsm_json = [{"id": 1, "subject": "New task"}]
        (skill_dir / "fsm.json").write_text(json.dumps(fsm_json))

        run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir_with_fsm_tasks.parent)
        )

        # Old FSM tasks (1, 2) should be deleted, new task should be 1
        task_files = list(task_dir_with_fsm_tasks.glob("*.json"))
        assert len(task_files) == 1
        assert task_files[0].name == "1.json"

    def test_manual_tasks_preserved(self, tmp_path, skill_dir):
        """SCN-THS-7.2: Manual tasks preserved."""
        # Create task dir with both manual and FSM tasks
        task_dir = tmp_path / "tasks" / "test-session"
        task_dir.mkdir(parents=True)

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
        (task_dir / "1.json").write_text(json.dumps({
            "id": "1",
            "subject": "FSM task",
            "description": "",
            "activeForm": "",
            "owner": "",
            "status": "pending",
            "blocks": [],
            "blockedBy": [],
            "metadata": {"fsm": "old-skill"}
        }))

        fsm_json = [{"id": 1, "subject": "New FSM task"}]
        (skill_dir / "fsm.json").write_text(json.dumps(fsm_json))

        run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        # Manual task 5 should still exist
        assert (task_dir / "5.json").exists()
        manual = json.loads((task_dir / "5.json").read_text())
        assert manual["subject"] == "Manual task"

        # New FSM task should be 6 (offset by manual task 5)
        assert (task_dir / "6.json").exists()


class TestAtomicBehavior:
    """REQ-THS-4/7: Atomic fail-closed behavior."""

    def test_validation_error_preserves_tasks(self, task_dir_with_fsm_tasks, skill_dir):
        """SCN-THS-7.3: Deletion blocked by validation failure."""
        original_files = {f.name: f.read_text() for f in task_dir_with_fsm_tasks.glob("*.json")}

        # Invalid fsm.json
        fsm_json = [{"id": 1}]  # Missing subject
        (skill_dir / "fsm.json").write_text(json.dumps(fsm_json))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir_with_fsm_tasks.parent)
        )

        assert exit_code != 0

        # Verify nothing changed
        current_files = {f.name: f.read_text() for f in task_dir_with_fsm_tasks.glob("*.json")}
        assert current_files == original_files


class TestScopePrecedence:
    """REQ-THS-3: Hook prefers specific plugin scopes."""

    def test_local_over_project(self, task_dir, tmp_path, installed_plugins_file):
        """SCN-THS-3.1: Local scope preferred over project."""
        local_dir = tmp_path / "local-plugin" / "skills" / "my-skill"
        local_dir.mkdir(parents=True)
        (local_dir / "fsm.json").write_text(json.dumps([{"id": 1, "subject": "FROM LOCAL"}]))

        project_dir = tmp_path / "project-plugin" / "skills" / "my-skill"
        project_dir.mkdir(parents=True)
        (project_dir / "fsm.json").write_text(json.dumps([{"id": 1, "subject": "FROM PROJECT"}]))

        project_path = str(tmp_path / "myproject")

        installed_plugins_file.write_text(json.dumps([
            {
                "name": "my-plugin@1.0.0",
                "scope": "local",
                "projectPath": project_path,
                "installPath": str(tmp_path / "local-plugin")
            },
            {
                "name": "my-plugin@1.0.0",
                "scope": "project",
                "projectPath": project_path,
                "installPath": str(tmp_path / "project-plugin")
            }
        ]))

        run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=project_path,
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "FROM LOCAL"

    def test_project_over_user(self, task_dir, tmp_path, installed_plugins_file):
        """SCN-THS-3.1: Project scope preferred over user."""
        project_dir = tmp_path / "project-plugin" / "skills" / "my-skill"
        project_dir.mkdir(parents=True)
        (project_dir / "fsm.json").write_text(json.dumps([{"id": 1, "subject": "FROM PROJECT"}]))

        user_dir = tmp_path / "user-plugin" / "skills" / "my-skill"
        user_dir.mkdir(parents=True)
        (user_dir / "fsm.json").write_text(json.dumps([{"id": 1, "subject": "FROM USER"}]))

        project_path = str(tmp_path / "myproject")

        installed_plugins_file.write_text(json.dumps([
            {
                "name": "my-plugin@1.0.0",
                "scope": "project",
                "projectPath": project_path,
                "installPath": str(tmp_path / "project-plugin")
            },
            {
                "name": "my-plugin@1.0.0",
                "scope": "user",
                "installPath": str(tmp_path / "user-plugin")
            }
        ]))

        run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=project_path,
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "FROM PROJECT"

    def test_plugin_not_found_falls_back(self, task_dir, tmp_path, installed_plugins_file):
        """SCN-THS-3.7: Plugin not in installed_plugins.json falls back."""
        # installed_plugins.json with different plugin
        installed_plugins_file.write_text(json.dumps([
            {"name": "other-plugin@1.0.0", "scope": "user", "installPath": "/tmp/other"}
        ]))

        # Non-plugin skill location
        project_skill = tmp_path / "project" / ".claude" / "skills" / "my-skill"
        project_skill.mkdir(parents=True)
        (project_skill / "fsm.json").write_text(json.dumps([{"id": 1, "subject": "FROM FALLBACK"}]))

        run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",  # Plugin not found
            cwd=str(tmp_path / "project"),
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "FROM FALLBACK"


class TestHookResponse:
    """REQ-THS-8: Hook returns continue on completion."""

    def test_success_returns_continue(self, task_dir, skill_dir):
        """SCN-THS-8.1: Successful hydration returns continue."""
        fsm_json = [{"id": 1, "subject": "Task"}]
        (skill_dir / "fsm.json").write_text(json.dumps(fsm_json))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        assert exit_code == 0
        assert json.loads(stdout) == {"continue": True}

    def test_no_fsm_returns_continue(self, task_dir, tmp_path):
        """SCN-THS-8.2: No-op completion returns continue."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="skill-without-fsm",
            cwd=str(project_dir),
            task_root=str(task_dir.parent)
        )

        assert exit_code == 0
        assert json.loads(stdout) == {"continue": True}


class TestFormatDetection:
    """@v2-registry-parsing:1 — Format detection from root JSON structure."""

    def test_v2_format_detected(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:1.1 — Object with version 2 detected as v2."""
        # Create plugin install directory with fsm.json
        install_dir = tmp_path / "plugin-install" / "skills" / "my-skill"
        install_dir.mkdir(parents=True)
        (install_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "V2 task"}
        ]))

        # Write v2 registry
        installed_plugins_file.write_text(json.dumps({
            "version": 2,
            "plugins": {
                "my-plugin@chaos-theory": [
                    {"scope": "user", "installPath": str(tmp_path / "plugin-install")}
                ]
            }
        }))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=str(tmp_path),
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code == 0
        assert json.loads(stdout) == {"continue": True}
        assert (task_dir / "1.json").exists()
        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "V2 task"

    def test_v1_format_detected(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:1.2 — Array at root detected as v1."""
        # Create plugin install directory with fsm.json
        install_dir = tmp_path / "plugin-install" / "skills" / "my-skill"
        install_dir.mkdir(parents=True)
        (install_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "V1 task"}
        ]))

        # Write v1 array
        installed_plugins_file.write_text(json.dumps([
            {
                "name": "my-plugin@1.0.0",
                "scope": "user",
                "installPath": str(tmp_path / "plugin-install")
            }
        ]))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=str(tmp_path),
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code == 0
        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "V1 task"

    def test_malformed_object_exits_nonzero(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:1.3 — Object without version field is malformed."""
        installed_plugins_file.write_text(json.dumps({"plugins": {}}))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=str(tmp_path),
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code != 0
        assert "version" in stderr.lower() or "malformed" in stderr.lower()

    def test_unknown_version_exits_nonzero(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:1.4 — Unknown version number is unsupported."""
        installed_plugins_file.write_text(json.dumps({"version": 3, "plugins": {}}))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=str(tmp_path),
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code != 0
        assert "version" in stderr.lower() or "unsupported" in stderr.lower()


class TestV2KeyMatching:
    """@v2-registry-parsing:2 — Plugin key matching in v2 plugins object."""

    def test_plugin_key_matched(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:2.1 — Plugin key matched by name portion."""
        # Create plugin install directory
        install_dir = tmp_path / "my-plugin-install" / "skills" / "my-skill"
        install_dir.mkdir(parents=True)
        (install_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "MATCHED"}
        ]))

        # Write v2 registry with key my-plugin@chaos-theory
        installed_plugins_file.write_text(json.dumps({
            "version": 2,
            "plugins": {
                "my-plugin@chaos-theory": [
                    {"scope": "user", "installPath": str(tmp_path / "my-plugin-install")}
                ]
            }
        }))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=str(tmp_path),
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code == 0
        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "MATCHED"

    def test_no_matching_key_falls_through(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:2.2 — No matching key falls through."""
        # V2 registry has different plugin
        installed_plugins_file.write_text(json.dumps({
            "version": 2,
            "plugins": {
                "other-plugin@marketplace": [
                    {"scope": "user", "installPath": "/tmp/other"}
                ]
            }
        }))

        # Non-plugin fallback
        fallback = tmp_path / "project" / ".claude" / "skills" / "my-skill"
        fallback.mkdir(parents=True)
        (fallback / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "FROM FALLBACK"}
        ]))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=str(tmp_path / "project"),
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code == 0
        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "FROM FALLBACK"

    def test_empty_plugins_falls_through(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:2.3 — Empty plugins falls through."""
        installed_plugins_file.write_text(json.dumps({
            "version": 2,
            "plugins": {}
        }))

        # Non-plugin fallback
        fallback = tmp_path / "project" / ".claude" / "skills" / "my-skill"
        fallback.mkdir(parents=True)
        (fallback / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "FROM FALLBACK"}
        ]))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=str(tmp_path / "project"),
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code == 0
        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "FROM FALLBACK"

    def test_multiple_keys_only_match_used(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:2.4 — Multiple keys, only matching used."""
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

        installed_plugins_file.write_text(json.dumps({
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

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="beta:my-skill",
            cwd=str(tmp_path),
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code == 0
        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "FROM BETA"  # Not FROM ALPHA


class TestV2ScopePrecedence:
    """@v2-registry-parsing:3 — Scope precedence over v2 entry arrays."""

    def test_scope_ordering(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:3.1 — Local > project > user."""
        # Create two plugin install dirs
        local_dir = tmp_path / "local-plugin" / "skills" / "my-skill"
        local_dir.mkdir(parents=True)
        (local_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "FROM LOCAL"}
        ]))

        project_dir = tmp_path / "project-plugin" / "skills" / "my-skill"
        project_dir.mkdir(parents=True)
        (project_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "FROM PROJECT"}
        ]))

        project_path = str(tmp_path / "myproject")

        # Write v2 registry with both entries for same plugin key
        installed_plugins_file.write_text(json.dumps({
            "version": 2,
            "plugins": {
                "my-plugin@chaos-theory": [
                    {
                        "scope": "local",
                        "projectPath": project_path,
                        "installPath": str(tmp_path / "local-plugin")
                    },
                    {
                        "scope": "project",
                        "projectPath": project_path,
                        "installPath": str(tmp_path / "project-plugin")
                    }
                ]
            }
        }))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=project_path,
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code == 0
        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "FROM LOCAL"  # Local wins

    def test_single_entry_used(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:3.2 — Single entry used directly."""
        install_dir = tmp_path / "plugin-install" / "skills" / "my-skill"
        install_dir.mkdir(parents=True)
        (install_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "SINGLE ENTRY"}
        ]))

        project_path = str(tmp_path / "myproject")

        installed_plugins_file.write_text(json.dumps({
            "version": 2,
            "plugins": {
                "my-plugin@chaos-theory": [
                    {
                        "scope": "project",
                        "projectPath": project_path,
                        "installPath": str(tmp_path / "plugin-install")
                    }
                ]
            }
        }))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=project_path,
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code == 0
        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "SINGLE ENTRY"

    def test_projectpath_matching(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:3.3 — cwd under projectPath matches."""
        install_dir = tmp_path / "plugin-install" / "skills" / "my-skill"
        install_dir.mkdir(parents=True)
        (install_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "PATH MATCHED"}
        ]))

        project_path = str(tmp_path / "myproject")
        cwd = str(tmp_path / "myproject" / "src" / "components")  # Under projectPath

        installed_plugins_file.write_text(json.dumps({
            "version": 2,
            "plugins": {
                "my-plugin@chaos-theory": [
                    {
                        "scope": "project",
                        "projectPath": project_path,
                        "installPath": str(tmp_path / "plugin-install")
                    }
                ]
            }
        }))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=cwd,
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code == 0
        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "PATH MATCHED"

    def test_projectpath_nonmatch_excludes(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:3.4 — projectPath non-matching excludes entry."""
        install_dir = tmp_path / "plugin-install" / "skills" / "my-skill"
        install_dir.mkdir(parents=True)
        (install_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "SHOULD NOT SEE"}
        ]))

        # Fallback skill
        fallback = tmp_path / "otherapp" / ".claude" / "skills" / "my-skill"
        fallback.mkdir(parents=True)
        (fallback / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "FROM FALLBACK"}
        ]))

        installed_plugins_file.write_text(json.dumps({
            "version": 2,
            "plugins": {
                "my-plugin@chaos-theory": [
                    {
                        "scope": "project",
                        "projectPath": str(tmp_path / "myapp"),
                        "installPath": str(tmp_path / "plugin-install")
                    }
                ]
            }
        }))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=str(tmp_path / "otherapp"),  # Different project
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code == 0
        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "FROM FALLBACK"

    def test_missing_installpath_skipped(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:3.5 — Entry without installPath skipped."""
        install_dir = tmp_path / "valid-install" / "skills" / "my-skill"
        install_dir.mkdir(parents=True)
        (install_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "VALID ENTRY"}
        ]))

        installed_plugins_file.write_text(json.dumps({
            "version": 2,
            "plugins": {
                "my-plugin@chaos-theory": [
                    {"scope": "user"},  # No installPath — should be skipped
                    {"scope": "user", "installPath": str(tmp_path / "valid-install")}
                ]
            }
        }))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=str(tmp_path),
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code == 0
        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "VALID ENTRY"


class TestV2MalformedRegistry:
    """@v2-registry-parsing:4 — Fail-closed for malformed v2 registries."""

    def test_plugin_absent_falls_back(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:4.1 — Plugin not in registry falls back."""
        installed_plugins_file.write_text(json.dumps({
            "version": 2,
            "plugins": {
                "other-plugin@marketplace": [
                    {"scope": "user", "installPath": "/tmp/other"}
                ]
            }
        }))

        fallback = tmp_path / "project" / ".claude" / "skills" / "my-skill"
        fallback.mkdir(parents=True)
        (fallback / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "FROM FALLBACK"}
        ]))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=str(tmp_path / "project"),
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code == 0
        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "FROM FALLBACK"

    def test_invalid_json_exits_nonzero(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:4.2 — Invalid JSON fails the hook."""
        installed_plugins_file.write_text("not valid json {{{")

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=str(tmp_path),
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code != 0
        assert "json" in stderr.lower() or "parse" in stderr.lower() or "malformed" in stderr.lower()

    def test_plugins_not_object_exits(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:4.3 — plugins field not object fails."""
        installed_plugins_file.write_text(json.dumps({
            "version": 2,
            "plugins": []
        }))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=str(tmp_path),
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code != 0
        assert "plugins" in stderr.lower() or "object" in stderr.lower()

    def test_missing_plugins_key_exits(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:4.4 — Missing plugins key fails."""
        installed_plugins_file.write_text(json.dumps({"version": 2}))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=str(tmp_path),
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code != 0
        assert "plugins" in stderr.lower()


class TestV1Deprecation:
    """@task-hydration-skill:2 — V1 format deprecation notice."""

    def test_v1_emits_deprecation(self, task_dir, tmp_path, installed_plugins_file):
        """@task-hydration-skill:2.6 — v1 format emits deprecation to stderr."""
        install_dir = tmp_path / "plugin-install" / "skills" / "my-skill"
        install_dir.mkdir(parents=True)
        (install_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "Task"}
        ]))

        installed_plugins_file.write_text(json.dumps([
            {
                "name": "my-plugin@1.0.0",
                "scope": "user",
                "installPath": str(tmp_path / "plugin-install")
            }
        ]))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=str(tmp_path),
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code == 0
        assert "deprecat" in stderr.lower()  # Matches DEPRECATION or deprecated
        # Verify stdout is still clean
        assert json.loads(stdout) == {"continue": True}

    def test_deprecation_message_content(self, task_dir, tmp_path, installed_plugins_file):
        """@task-hydration-skill:2.7 — Message advises v2 update, stderr only."""
        install_dir = tmp_path / "plugin-install" / "skills" / "my-skill"
        install_dir.mkdir(parents=True)
        (install_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "Task"}
        ]))

        installed_plugins_file.write_text(json.dumps([
            {
                "name": "my-plugin@1.0.0",
                "scope": "user",
                "installPath": str(tmp_path / "plugin-install")
            }
        ]))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=str(tmp_path),
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        # Message content
        assert "v2" in stderr.lower() or "v2" in stderr
        assert "deprecat" in stderr.lower()

        # Channel: deprecation is on stderr, stdout has only the hook response
        assert json.loads(stdout) == {"continue": True}
        assert "deprecat" not in stdout.lower()  # Not on stdout
