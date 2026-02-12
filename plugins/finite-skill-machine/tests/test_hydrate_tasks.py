"""Tests for the FSM hydrate-tasks hook."""

import json
from pathlib import Path

import pytest

from conftest import run_hook, _make_task_file


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
        assert "json" in stderr.lower() or "malformed" in stderr.lower()

    def test_not_array_fails(self, task_dir, skill_dir):
        """SCN-THS-4.3: fsm.json that's not an array fails."""
        (skill_dir / "fsm.json").write_text(json.dumps({"id": 1}))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        assert exit_code != 0
        assert "array" in stderr.lower()

    def test_missing_id_fails(self, task_dir, skill_dir):
        """SCN-THS-4.4: Task without 'id' fails validation."""
        (skill_dir / "fsm.json").write_text(json.dumps([
            {"subject": "No ID here"}
        ]))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        assert exit_code != 0
        assert "id" in stderr.lower()

    def test_missing_subject_fails(self, task_dir, skill_dir):
        """SCN-THS-4.5: Task without 'subject' fails validation."""
        (skill_dir / "fsm.json").write_text(json.dumps([
            {"id": 1}
        ]))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        assert exit_code != 0
        assert "subject" in stderr.lower()

    def test_duplicate_id_fails(self, task_dir, skill_dir):
        """SCN-THS-4.6: Duplicate task IDs fail validation."""
        (skill_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "First"},
            {"id": 1, "subject": "Duplicate"}
        ]))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        assert exit_code != 0
        assert "duplicate" in stderr.lower()

    def test_invalid_dependency_ref_fails(self, task_dir, skill_dir):
        """SCN-THS-4.7: Dependency referencing non-existent ID fails."""
        (skill_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "Task", "blockedBy": [999]}
        ]))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        assert exit_code != 0
        assert "999" in stderr


class TestIdTranslation:
    """REQ-THS-5: Hook translates local IDs to global IDs."""

    def test_empty_task_dir_no_offset(self, task_dir, skill_dir):
        """SCN-THS-5.1: Empty task directory starts IDs at 1."""
        fsm_json = [
            {"id": 1, "subject": "First task"},
            {"id": 2, "subject": "Second task"}
        ]
        (skill_dir / "fsm.json").write_text(json.dumps(fsm_json))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        assert exit_code == 0
        assert (task_dir / "1.json").exists()
        assert (task_dir / "2.json").exists()

        task1 = json.loads((task_dir / "1.json").read_text())
        assert task1["id"] == "1"
        assert task1["subject"] == "First task"

    def test_existing_tasks_offset_ids(self, task_dir_with_manual_task, skill_dir):
        """SCN-THS-5.2: Existing manual tasks offset new task IDs."""
        task_dir = task_dir_with_manual_task

        fsm_json = [
            {"id": 1, "subject": "FSM task 1"},
            {"id": 2, "subject": "FSM task 2"},
            {"id": 3, "subject": "FSM task 3"}
        ]
        (skill_dir / "fsm.json").write_text(json.dumps(fsm_json))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        assert exit_code == 0

        # Manual task 5 preserved, new tasks at 6, 7, 8
        assert (task_dir / "5.json").exists()
        assert (task_dir / "6.json").exists()
        assert (task_dir / "7.json").exists()
        assert (task_dir / "8.json").exists()

    def test_dependencies_use_translated_ids(self, task_dir_with_manual_task, skill_dir):
        """SCN-THS-5.3: Dependencies reference translated IDs."""
        task_dir = task_dir_with_manual_task

        fsm_json = [
            {"id": 1, "subject": "Task 1"},
            {"id": 2, "subject": "Task 2", "blockedBy": [1]},
            {"id": 3, "subject": "Task 3", "blocks": [2]}
        ]
        (skill_dir / "fsm.json").write_text(json.dumps(fsm_json))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        assert exit_code == 0

        # Manual at 5, new at 6,7,8 — deps should ref translated IDs
        task7 = json.loads((task_dir / "7.json").read_text())
        assert task7["blockedBy"] == ["6"]

        task8 = json.loads((task_dir / "8.json").read_text())
        assert task8["blocks"] == ["7"]


class TestFsmTaskDeletion:
    """REQ-THS-7: Hook deletes existing FSM tasks before writing new ones."""

    def test_fsm_tasks_deleted(self, task_dir_with_fsm_tasks, skill_dir):
        """SCN-THS-7.1: Existing FSM tasks deleted on re-invocation."""
        task_dir = task_dir_with_fsm_tasks

        fsm_json = [
            {"id": 1, "subject": "New FSM task 1"},
            {"id": 2, "subject": "New FSM task 2"}
        ]
        (skill_dir / "fsm.json").write_text(json.dumps(fsm_json))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        assert exit_code == 0

        # Old tasks deleted, new tasks at 1,2
        task1 = json.loads((task_dir / "1.json").read_text())
        task2 = json.loads((task_dir / "2.json").read_text())

        assert task1["subject"] == "New FSM task 1"
        assert task2["subject"] == "New FSM task 2"

    def test_manual_tasks_preserved(self, task_dir_with_manual_task, task_dir_with_fsm_tasks, skill_dir):
        """SCN-THS-7.2: Manual tasks preserved during FSM deletion."""
        # Start with manual task and FSM tasks
        task_dir = task_dir_with_manual_task

        # Add FSM task
        (task_dir / "1.json").write_text(json.dumps({
            "id": "1",
            "subject": "Old FSM",
            "description": "",
            "activeForm": "",
            "owner": "",
            "status": "pending",
            "blocks": [],
            "blockedBy": [],
            "metadata": {"fsm": "test-skill"}
        }))

        fsm_json = [
            {"id": 1, "subject": "New FSM task"}
        ]
        (skill_dir / "fsm.json").write_text(json.dumps(fsm_json))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        assert exit_code == 0

        # Manual task 5 still exists
        assert (task_dir / "5.json").exists()
        task5 = json.loads((task_dir / "5.json").read_text())
        assert task5["subject"] == "Manual task"
        assert "fsm" not in task5.get("metadata", {})

        # New FSM task at 6 (offset past 5)
        assert (task_dir / "6.json").exists()
        task6 = json.loads((task_dir / "6.json").read_text())
        assert task6["subject"] == "New FSM task"


class TestAtomicBehavior:
    """REQ-THS-7: Atomic operation requirements."""

    def test_validation_error_preserves_tasks(self, task_dir_with_fsm_tasks, skill_dir):
        """SCN-THS-7.3: Validation failure leaves existing tasks unchanged."""
        task_dir = task_dir_with_fsm_tasks

        # Invalid fsm.json
        (skill_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "Task", "blockedBy": [999]}
        ]))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="test-skill",
            cwd=str(skill_dir.parent.parent.parent),
            task_root=str(task_dir.parent)
        )

        assert exit_code != 0

        # Old FSM tasks still exist
        assert (task_dir / "1.json").exists()
        assert (task_dir / "2.json").exists()

        task1 = json.loads((task_dir / "1.json").read_text())
        assert task1["subject"] == "FSM task 1"


class TestScopePrecedence:
    """REQ-THS-3: Skill location search."""

    def test_project_skill_precedes_user_skill(self, task_dir, tmp_path):
        """SCN-THS-3.2: Project skill takes precedence over user skill."""
        # Project skill
        project_skill = tmp_path / "project" / ".claude" / "skills" / "my-skill"
        project_skill.mkdir(parents=True)
        (project_skill / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "FROM PROJECT"}
        ]))

        # User skill
        user_skill = tmp_path / "user-skills" / "my-skill"
        user_skill.mkdir(parents=True)
        (user_skill / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "FROM USER"}
        ]))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-skill",
            cwd=str(tmp_path / "project"),
            task_root=str(task_dir.parent),
            user_skills_root=str(user_skill.parent)
        )

        assert exit_code == 0
        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "FROM PROJECT"

    def test_plugin_local_precedes_project_and_user(self, task_dir, tmp_path, installed_plugins_file):
        """SCN-THS-3.1: Local plugin scope has highest precedence."""
        project_path = str(tmp_path / "myproject")

        # Local install
        local_install = tmp_path / "local-install" / "skills" / "my-skill"
        local_install.mkdir(parents=True)
        (local_install / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "FROM LOCAL"}
        ]))

        # User install
        user_install = tmp_path / "user-install" / "skills" / "my-skill"
        user_install.mkdir(parents=True)
        (user_install / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "FROM USER"}
        ]))

        installed_plugins_file.write_text(json.dumps([
            {
                "name": "my-plugin@1.0.0",
                "scope": "local",
                "projectPath": project_path,
                "installPath": str(tmp_path / "local-install")
            },
            {
                "name": "my-plugin@1.0.0",
                "scope": "user",
                "installPath": str(tmp_path / "user-install")
            }
        ]))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=project_path,
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code == 0
        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "FROM LOCAL"

    def test_plugin_not_found_falls_back_to_non_plugin(self, task_dir, tmp_path, installed_plugins_file):
        """SCN-THS-3.3: Plugin not in registry falls back to non-plugin lookup."""
        # Empty installed_plugins.json
        installed_plugins_file.write_text(json.dumps([]))

        # Project skill
        project_dir = tmp_path / "myproject"
        skill_dir = project_dir / ".claude" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "FROM PROJECT"}
        ]))

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

        # Write v1 registry (array)
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
        assert json.loads(stdout) == {"continue": True}
        assert (task_dir / "1.json").exists()
        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "V1 task"


class TestV2Scoping:
    """@v2-registry-parsing:2 — Scope precedence in v2 format."""

    def test_v2_local_precedes_project(self, task_dir, tmp_path):
        """@v2-registry-parsing:2.1 — local > project precedence."""
        plugins_file = tmp_path / "installed_plugins.json"
        project_path = str(tmp_path / "myproject")

        # Local install
        local_dir = tmp_path / "local-install" / "skills" / "my-skill"
        local_dir.mkdir(parents=True)
        (local_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "FROM LOCAL"}
        ]))

        # Project install
        proj_dir = tmp_path / "proj-install" / "skills" / "my-skill"
        proj_dir.mkdir(parents=True)
        (proj_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "FROM PROJECT"}
        ]))

        # V2 registry with both
        plugins_file.write_text(json.dumps({
            "version": 2,
            "plugins": {
                "my-plugin@chaos": [
                    {"scope": "project", "projectPath": project_path, "installPath": str(tmp_path / "proj-install")},
                    {"scope": "local", "projectPath": project_path, "installPath": str(tmp_path / "local-install")}
                ]
            }
        }))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=project_path,
            task_root=str(task_dir.parent),
            plugins_file=str(plugins_file)
        )

        assert exit_code == 0
        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "FROM LOCAL"

    def test_v2_project_precedes_user(self, task_dir, tmp_path):
        """@v2-registry-parsing:2.2 — project > user precedence."""
        plugins_file = tmp_path / "installed_plugins.json"
        project_path = str(tmp_path / "myproject")

        # Project install
        proj_dir = tmp_path / "proj-install" / "skills" / "my-skill"
        proj_dir.mkdir(parents=True)
        (proj_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "FROM PROJECT"}
        ]))

        # User install
        user_dir = tmp_path / "user-install" / "skills" / "my-skill"
        user_dir.mkdir(parents=True)
        (user_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "FROM USER"}
        ]))

        plugins_file.write_text(json.dumps({
            "version": 2,
            "plugins": {
                "my-plugin@chaos": [
                    {"scope": "user", "installPath": str(tmp_path / "user-install")},
                    {"scope": "project", "projectPath": project_path, "installPath": str(tmp_path / "proj-install")}
                ]
            }
        }))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=project_path,
            task_root=str(task_dir.parent),
            plugins_file=str(plugins_file)
        )

        assert exit_code == 0
        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "FROM PROJECT"

    def test_v2_user_scope_no_project_path_filter(self, task_dir, tmp_path):
        """@v2-registry-parsing:2.3 — user scope ignores projectPath."""
        plugins_file = tmp_path / "installed_plugins.json"

        user_dir = tmp_path / "user-install" / "skills" / "my-skill"
        user_dir.mkdir(parents=True)
        (user_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "USER SCOPED"}
        ]))

        plugins_file.write_text(json.dumps({
            "version": 2,
            "plugins": {
                "my-plugin@chaos": [
                    {"scope": "user", "installPath": str(tmp_path / "user-install")}
                ]
            }
        }))

        # Invoke from ANY cwd
        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=str(tmp_path / "different-project"),
            task_root=str(task_dir.parent),
            plugins_file=str(plugins_file)
        )

        assert exit_code == 0
        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "USER SCOPED"


class TestV2MultiKeyRegistry:
    """@v2-registry-parsing:3 — Multiple plugins in v2 registry."""

    def test_v2_multi_key_plugin_resolution(self, task_dir, tmp_path, v2_multi_key_plugins):
        """@v2-registry-parsing:3.1 — Resolve correct plugin from multi-key registry."""
        # Invoke alpha
        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="alpha:my-skill",
            cwd=str(tmp_path),
            task_root=str(task_dir.parent),
            plugins_file=str(v2_multi_key_plugins)
        )

        assert exit_code == 0
        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "FROM ALPHA"

        # Clear for beta test
        (task_dir / "1.json").unlink()

        # Invoke beta
        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="beta:my-skill",
            cwd=str(tmp_path),
            task_root=str(task_dir.parent),
            plugins_file=str(v2_multi_key_plugins)
        )

        assert exit_code == 0
        task = json.loads((task_dir / "1.json").read_text())
        assert task["subject"] == "FROM BETA"


class TestV2Validation:
    """@v2-registry-parsing:4 — Error handling for malformed v2 structure."""

    def test_v2_missing_version_field_fails(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:4.1 — Object without version field fails."""
        installed_plugins_file.write_text(json.dumps({
            "plugins": {}
        }))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=str(tmp_path),
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code != 0
        assert "version" in stderr.lower()

    def test_v2_unsupported_version_fails(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:4.2 — Version other than 2 fails."""
        installed_plugins_file.write_text(json.dumps({
            "version": 99,
            "plugins": {}
        }))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=str(tmp_path),
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code != 0
        assert "version" in stderr.lower() or "unsupported" in stderr.lower()

    def test_v2_missing_plugins_field_fails(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:4.3 — Object without plugins field fails."""
        installed_plugins_file.write_text(json.dumps({
            "version": 2
        }))

        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="my-plugin:my-skill",
            cwd=str(tmp_path),
            task_root=str(task_dir.parent),
            plugins_file=str(installed_plugins_file)
        )

        assert exit_code != 0
        assert "plugins" in stderr.lower()

    def test_v2_plugins_not_object_fails(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:4.4 — plugins field must be object."""
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
        assert "plugins" in stderr.lower()


class TestV2DeprecationNotice:
    """@v2-registry-parsing:5 — Deprecation notice for v1 format."""

    def test_v1_emits_deprecation_warning(self, task_dir, tmp_path, installed_plugins_file):
        """@v2-registry-parsing:5.1 — V1 registry logs deprecation to stderr."""
        install_dir = tmp_path / "plugin-install" / "skills" / "my-skill"
        install_dir.mkdir(parents=True)
        (install_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "Task"}
        ]))

        # V1 array format
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


# ============================================================================
# NEW TDD TESTS FOR fsm-anti-clobber
# ============================================================================


class TestSharedUtility:
    """Tests for find_skill_tasks shared utility."""

    def test_returns_only_matching_command_name(self, task_dir, hydrate_module):
        """@per-skill-deletion:1.1 — Only tasks with matching fsm value are returned."""
        # Create tasks with different fsm values
        (task_dir / "1.json").write_text(json.dumps({
            "id": "1", "subject": "Skill-A task", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "plugin-a:skill-a"}
        }))
        (task_dir / "3.json").write_text(json.dumps({
            "id": "3", "subject": "Skill-B task", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "plugin-b:skill-b"}
        }))
        (task_dir / "5.json").write_text(json.dumps({
            "id": "5", "subject": "Manual task", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {}
        }))

        # Call find_skill_tasks for plugin-a:skill-a
        result = hydrate_module.find_skill_tasks(task_dir, "plugin-a:skill-a")
        names = sorted(p.name for p in result)

        # Should only return 1.json
        assert names == ["1.json"]

    def test_preserves_tasks_with_different_fsm_values(self, task_dir, hydrate_module):
        """Tasks with different fsm values are not returned."""
        # Create tasks with different fsm values
        (task_dir / "1.json").write_text(json.dumps({
            "id": "1", "subject": "Skill-A task", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "plugin-a:skill-a"}
        }))
        (task_dir / "3.json").write_text(json.dumps({
            "id": "3", "subject": "Skill-B task", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "plugin-b:skill-b"}
        }))
        (task_dir / "5.json").write_text(json.dumps({
            "id": "5", "subject": "Manual task", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {}
        }))

        # Call find_skill_tasks for plugin-a:skill-a
        result = hydrate_module.find_skill_tasks(task_dir, "plugin-a:skill-a")
        names = [p.name for p in result]

        # Verify other tasks are NOT returned
        assert "3.json" not in names  # skill-b
        assert "5.json" not in names  # manual

    def test_non_string_fsm_values_not_matched(self, task_dir, hydrate_module):
        """Non-string fsm values (null, 42, '') are treated as non-matching."""
        # Create tasks with non-string fsm values
        for i, fsm_val in enumerate([None, 42, ""], start=1):
            (task_dir / f"{i}.json").write_text(json.dumps({
                "id": str(i), "subject": f"Task {i}", "description": "",
                "activeForm": "", "owner": "", "status": "pending",
                "blocks": [], "blockedBy": [],
                "metadata": {"fsm": fsm_val}
            }))

        # Call find_skill_tasks - none should match
        result = hydrate_module.find_skill_tasks(task_dir, "real-skill")
        assert result == []

    def test_aborts_on_malformed_task_file(self, task_dir, hydrate_module):
        """Malformed task file causes abort, not silent skip."""
        # Invalid JSON
        (task_dir / "1.json").write_text("not valid json{{{")

        with pytest.raises(SystemExit) as exc_info:
            hydrate_module.find_skill_tasks(task_dir, "any-skill")
        assert exc_info.value.code == 1

    def test_aborts_on_missing_required_fields(self, task_dir, hydrate_module):
        """Task file missing id/status/metadata causes abort."""
        (task_dir / "1.json").write_text(json.dumps({"only": "data"}))

        with pytest.raises(SystemExit) as exc_info:
            hydrate_module.find_skill_tasks(task_dir, "any-skill")
        assert exc_info.value.code == 1

    def test_aborts_on_wrong_field_types(self, task_dir, hydrate_module):
        """Task file with wrong field types causes abort."""
        (task_dir / "1.json").write_text(json.dumps({
            "id": ["not", "a", "string"],  # Wrong type
            "status": "pending",
            "metadata": {}
        }))

        with pytest.raises(SystemExit) as exc_info:
            hydrate_module.find_skill_tasks(task_dir, "any-skill")
        assert exc_info.value.code == 1


class TestActiveTaskGuard:
    """Tests for check_active_tasks guard function."""

    def test_passes_no_matching_tasks(self, task_dir, hydrate_module):
        """@active-task-guard:1.4 — Guard passes when no tasks match."""
        # Create tasks for other skills
        (task_dir / "1.json").write_text(json.dumps({
            "id": "1", "subject": "Other skill task", "description": "",
            "activeForm": "", "owner": "", "status": "in_progress",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "other-skill"}
        }))

        # Should not raise — "test-skill" matches nothing
        hydrate_module.check_active_tasks(task_dir, "test-skill")

    def test_passes_all_pending(self, task_dir, hydrate_module):
        """@active-task-guard:1.3 — Guard passes when all tasks pending."""
        (task_dir / "1.json").write_text(json.dumps({
            "id": "1", "subject": "Task 1", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "test-skill"}
        }))
        (task_dir / "2.json").write_text(json.dumps({
            "id": "2", "subject": "Task 2", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "test-skill"}
        }))

        # Should not raise
        hydrate_module.check_active_tasks(task_dir, "test-skill")

    def test_aborts_in_progress(self, task_dir, hydrate_module):
        """@active-task-guard:1.1 — Guard aborts on in_progress tasks."""
        (task_dir / "1.json").write_text(json.dumps({
            "id": "1", "subject": "Task 1", "description": "",
            "activeForm": "", "owner": "", "status": "in_progress",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "test-skill"}
        }))

        with pytest.raises(SystemExit) as exc_info:
            hydrate_module.check_active_tasks(task_dir, "test-skill")
        assert exc_info.value.code == 1

    def test_passes_all_completed(self, task_dir_all_completed, hydrate_module):
        """@active-task-guard:1.2 — Guard passes when all tasks completed."""
        hydrate_module.check_active_tasks(task_dir_all_completed, "test-skill")

    def test_aborts_mixed_completed_pending(self, task_dir_mixed_completed_pending, hydrate_module):
        """@active-task-guard:1.5 — Guard aborts on mixed completed+pending."""
        with pytest.raises(SystemExit) as exc_info:
            hydrate_module.check_active_tasks(task_dir_mixed_completed_pending, "test-skill")
        assert exc_info.value.code == 1

    def test_aborts_mixed_in_progress_completed(self, task_dir_mixed_in_progress_completed, hydrate_module):
        """@active-task-guard:1.6 — Guard aborts on mixed in_progress+completed."""
        with pytest.raises(SystemExit) as exc_info:
            hydrate_module.check_active_tasks(task_dir_mixed_in_progress_completed, "test-skill")
        assert exc_info.value.code == 1

    def test_aborts_unrecognized_status(self, task_dir, hydrate_module):
        """@active-task-guard:1.8 — Unrecognized status 'blocked' causes abort."""
        (task_dir / "1.json").write_text(json.dumps({
            "id": "1", "subject": "Task", "description": "",
            "activeForm": "", "owner": "", "status": "blocked",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "test-skill"}
        }))

        with pytest.raises(SystemExit) as exc_info:
            hydrate_module.check_active_tasks(task_dir, "test-skill")
        assert exc_info.value.code == 1

    def test_aborts_corrupted_task_file(self, task_dir, hydrate_module):
        """@active-task-guard:1.7 — Corrupted task file causes guard abort."""
        # Create one valid pending task
        _make_task_file(task_dir, 1, "pending", "test-skill")
        # Create one corrupted task file
        (task_dir / "2.json").write_text("corrupted{{{not json")

        # Guard should abort - corrupted file could hide in_progress task
        with pytest.raises(SystemExit) as exc_info:
            hydrate_module.check_active_tasks(task_dir, "test-skill")
        assert exc_info.value.code == 1


class TestActiveTaskGuardMessage:
    """Tests for guard abort message format."""

    def test_abort_json_format(self, task_dir_all_in_progress, hydrate_module):
        """@active-task-guard:2.1 — Abort error is JSON with tasks and message."""
        import io
        import contextlib

        stderr_capture = io.StringIO()
        with pytest.raises(SystemExit):
            with contextlib.redirect_stderr(stderr_capture):
                hydrate_module.check_active_tasks(task_dir_all_in_progress, "test-skill")

        stderr_output = stderr_capture.getvalue()
        # error_exit prefixes with "[fsm] ERROR: " — extract JSON after that
        json_str = stderr_output.split("[fsm] ERROR: ", 1)[1].strip()
        payload = json.loads(json_str)

        assert "tasks" in payload
        assert isinstance(payload["tasks"], list)
        assert all(isinstance(t, int) for t in payload["tasks"])
        assert payload["message"] == "Related active task(s) must be resolved and verified first."

    def test_abort_excludes_forbidden_terms(self, task_dir_all_in_progress, hydrate_module):
        """@active-task-guard:2.2 — Message contains no internal mechanism terms."""
        import io
        import contextlib

        stderr_capture = io.StringIO()
        with pytest.raises(SystemExit):
            with contextlib.redirect_stderr(stderr_capture):
                hydrate_module.check_active_tasks(task_dir_all_in_progress, "test-skill")

        stderr_output = stderr_capture.getvalue()
        json_str = stderr_output.split("[fsm] ERROR: ", 1)[1].strip()
        payload = json.loads(json_str)
        message = payload["message"]

        forbidden = ["hydration", "re-hydration", "re-hydrate", "delete", "just complete"]
        for term in forbidden:
            assert term.lower() not in message.lower(), f"Forbidden term '{term}' in message"


class TestActiveTaskGuardScope:
    """Tests for guard cross-skill isolation."""

    def test_ignores_other_skill_active_tasks(self, task_dir, hydrate_module):
        """@active-task-guard:3.1 — Other skill's active tasks don't trigger guard."""
        (task_dir / "1.json").write_text(json.dumps({
            "id": "1", "subject": "Other task", "description": "",
            "activeForm": "", "owner": "", "status": "in_progress",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "other-skill"}
        }))

        # Should not raise — "test-skill" has no matching tasks
        hydrate_module.check_active_tasks(task_dir, "test-skill")

    def test_aborts_only_for_invoking_skill(self, task_dir, hydrate_module):
        """@active-task-guard:3.2 — Abort scoped to invoking skill only."""
        (task_dir / "1.json").write_text(json.dumps({
            "id": "1", "subject": "A task", "description": "",
            "activeForm": "", "owner": "", "status": "in_progress",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "skill-a"}
        }))
        (task_dir / "2.json").write_text(json.dumps({
            "id": "2", "subject": "B task", "description": "",
            "activeForm": "", "owner": "", "status": "in_progress",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "skill-b"}
        }))

        # Guard for skill-a: aborts (has in_progress tasks)
        with pytest.raises(SystemExit):
            hydrate_module.check_active_tasks(task_dir, "skill-a")

        # Guard for skill-c: passes (no matching tasks)
        hydrate_module.check_active_tasks(task_dir, "skill-c")


class TestPerSkillDeletion:
    """Integration tests for per-skill scoped deletion."""

    def test_skill_b_preserves_skill_a_tasks(self, tmp_path):
        """@per-skill-deletion:1.1 — Invoking skill-b preserves skill-a tasks."""
        # Set up task directory with multi-skill tasks
        task_dir = tmp_path / "tasks" / "test-session"
        task_dir.mkdir(parents=True)

        # Create skill-a task
        (task_dir / "1.json").write_text(json.dumps({
            "id": "1", "subject": "Skill-A task", "description": "",
            "activeForm": "", "owner": "", "status": "completed",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "plugin-a:skill-a"}
        }))

        # Create skill-b task (will be deleted and replaced)
        (task_dir / "3.json").write_text(json.dumps({
            "id": "3", "subject": "Old Skill-B task", "description": "",
            "activeForm": "", "owner": "", "status": "completed",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "skill-b"}
        }))

        # Create manual task
        (task_dir / "5.json").write_text(json.dumps({
            "id": "5", "subject": "Manual task", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {}
        }))

        # Create skill-b directory with fsm.json (user skill format)
        skill_dir = tmp_path / "project" / ".claude" / "skills" / "skill-b"
        skill_dir.mkdir(parents=True)
        (skill_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "New B task 1"},
            {"id": 2, "subject": "New B task 2"}
        ]))

        # Run hook as skill-b
        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="skill-b",
            cwd=str(tmp_path / "project"),
            task_root=str(tmp_path / "tasks"),
            user_skills_root=str(tmp_path / "project" / ".claude" / "skills")
        )

        # Debug: Check what happened
        if exit_code != 0:
            print(f"STDERR: {stderr}")
            print(f"STDOUT: {stdout}")
        assert exit_code == 0, f"Hook failed: {stderr}"

        # Verify skill-a task preserved
        assert (task_dir / "1.json").exists()
        skill_a_data = json.loads((task_dir / "1.json").read_text())
        assert skill_a_data["subject"] == "Skill-A task"
        assert skill_a_data["metadata"]["fsm"] == "plugin-a:skill-a"

        # Verify manual task preserved
        assert (task_dir / "5.json").exists()
        manual_data = json.loads((task_dir / "5.json").read_text())
        assert manual_data["subject"] == "Manual task"
        assert manual_data["metadata"] == {}

        # Verify old skill-b task deleted
        assert not (task_dir / "3.json").exists()

        # Verify new skill-b tasks created with correct offset (after max preserved ID = 5)
        assert (task_dir / "6.json").exists()
        assert (task_dir / "7.json").exists()
        new_b1 = json.loads((task_dir / "6.json").read_text())
        assert new_b1["subject"] == "New B task 1"
        assert new_b1["metadata"]["fsm"] == "skill-b"

    def test_skill_a_deletes_only_its_tasks(self, tmp_path):
        """@per-skill-deletion:1.2 — Invoking skill-a deletes only skill-a tasks."""
        # Set up task directory with multi-skill tasks
        task_dir = tmp_path / "tasks" / "test-session"
        task_dir.mkdir(parents=True)

        # Create skill-a task (will be deleted and replaced)
        (task_dir / "1.json").write_text(json.dumps({
            "id": "1", "subject": "Old Skill-A task", "description": "",
            "activeForm": "", "owner": "", "status": "completed",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "skill-a"}
        }))

        # Create skill-b task (should be preserved)
        (task_dir / "3.json").write_text(json.dumps({
            "id": "3", "subject": "Skill-B task", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "skill-b"}
        }))

        # Create manual task (should be preserved)
        (task_dir / "5.json").write_text(json.dumps({
            "id": "5", "subject": "Manual task", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {}
        }))

        # Create skill-a directory with fsm.json
        skill_dir = tmp_path / "project" / ".claude" / "skills" / "skill-a"
        skill_dir.mkdir(parents=True)
        (skill_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "New A task 1"},
            {"id": 2, "subject": "New A task 2"}
        ]))

        # Run hook as skill-a
        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="skill-a",
            cwd=str(tmp_path / "project"),
            task_root=str(tmp_path / "tasks"),
            user_skills_root=str(tmp_path / "project" / ".claude" / "skills")
        )

        assert exit_code == 0, f"Hook failed: {stderr}"

        # Verify skill-b task preserved
        assert (task_dir / "3.json").exists()
        skill_b_data = json.loads((task_dir / "3.json").read_text())
        assert skill_b_data["subject"] == "Skill-B task"
        assert skill_b_data["metadata"]["fsm"] == "skill-b"

        # Verify manual task preserved
        assert (task_dir / "5.json").exists()
        manual_data = json.loads((task_dir / "5.json").read_text())
        assert manual_data["subject"] == "Manual task"
        assert manual_data["metadata"] == {}

        # Verify old skill-a task deleted
        assert not (task_dir / "1.json").exists()

        # Verify new skill-a tasks created with correct offset (after max preserved ID = 5)
        assert (task_dir / "6.json").exists()
        assert (task_dir / "7.json").exists()
        new_a1 = json.loads((task_dir / "6.json").read_text())
        assert new_a1["subject"] == "New A task 1"
        assert new_a1["metadata"]["fsm"] == "skill-a"

    def test_manual_tasks_preserved_in_deletion(self, tmp_path):
        """@per-skill-deletion:1.3 — Manual tasks preserved during per-skill deletion."""
        # Set up task directory
        task_dir = tmp_path / "tasks" / "test-session"
        task_dir.mkdir(parents=True)

        # Create skill-a task (will be deleted)
        (task_dir / "1.json").write_text(json.dumps({
            "id": "1", "subject": "Old Skill-A task", "description": "",
            "activeForm": "", "owner": "", "status": "completed",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "skill-a"}
        }))

        # Create manual task with no fsm key (should be preserved)
        (task_dir / "3.json").write_text(json.dumps({
            "id": "3", "subject": "Manual task", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {}
        }))

        # Create another manual task (should be preserved)
        (task_dir / "5.json").write_text(json.dumps({
            "id": "5", "subject": "Another manual task", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {"other": "data"}  # has metadata but no fsm key
        }))

        # Create skill-a directory with fsm.json
        skill_dir = tmp_path / "project" / ".claude" / "skills" / "skill-a"
        skill_dir.mkdir(parents=True)
        (skill_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "New A task"}
        ]))

        # Run hook as skill-a
        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="skill-a",
            cwd=str(tmp_path / "project"),
            task_root=str(tmp_path / "tasks"),
            user_skills_root=str(tmp_path / "project" / ".claude" / "skills")
        )

        assert exit_code == 0, f"Hook failed: {stderr}"

        # Verify old skill-a task deleted
        assert not (task_dir / "1.json").exists()

        # Verify both manual tasks preserved and unchanged
        assert (task_dir / "3.json").exists()
        manual1 = json.loads((task_dir / "3.json").read_text())
        assert manual1["subject"] == "Manual task"
        assert manual1["metadata"] == {}

        assert (task_dir / "5.json").exists()
        manual2 = json.loads((task_dir / "5.json").read_text())
        assert manual2["subject"] == "Another manual task"
        assert manual2["metadata"] == {"other": "data"}

        # Verify new skill-a task created with correct offset (after max preserved ID = 5)
        assert (task_dir / "6.json").exists()
        new_a1 = json.loads((task_dir / "6.json").read_text())
        assert new_a1["subject"] == "New A task"
        assert new_a1["metadata"]["fsm"] == "skill-a"

    def test_non_string_fsm_metadata_preserved(self, tmp_path):
        """@per-skill-deletion:1.4 — Tasks with non-string fsm values preserved."""
        # Set up task directory
        task_dir = tmp_path / "tasks" / "test-session"
        task_dir.mkdir(parents=True)

        # Create skill-a task (will be deleted)
        (task_dir / "1.json").write_text(json.dumps({
            "id": "1", "subject": "Skill-A task", "description": "",
            "activeForm": "", "owner": "", "status": "completed",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "skill-a"}
        }))

        # Create task with null fsm value (should be preserved)
        (task_dir / "2.json").write_text(json.dumps({
            "id": "2", "subject": "Task with null fsm", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": None}
        }))

        # Create task with integer fsm value (should be preserved)
        (task_dir / "3.json").write_text(json.dumps({
            "id": "3", "subject": "Task with int fsm", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": 42}
        }))

        # Create task with empty string fsm value (should be preserved)
        (task_dir / "4.json").write_text(json.dumps({
            "id": "4", "subject": "Task with empty string fsm", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": ""}
        }))

        # Create skill-a directory with fsm.json
        skill_dir = tmp_path / "project" / ".claude" / "skills" / "skill-a"
        skill_dir.mkdir(parents=True)
        (skill_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "New A task"}
        ]))

        # Run hook as skill-a
        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="skill-a",
            cwd=str(tmp_path / "project"),
            task_root=str(tmp_path / "tasks"),
            user_skills_root=str(tmp_path / "project" / ".claude" / "skills")
        )

        assert exit_code == 0, f"Hook failed: {stderr}"

        # Verify skill-a task deleted
        assert not (task_dir / "1.json").exists()

        # Verify all non-string fsm tasks preserved
        assert (task_dir / "2.json").exists()
        null_task = json.loads((task_dir / "2.json").read_text())
        assert null_task["subject"] == "Task with null fsm"
        assert null_task["metadata"]["fsm"] is None

        assert (task_dir / "3.json").exists()
        int_task = json.loads((task_dir / "3.json").read_text())
        assert int_task["subject"] == "Task with int fsm"
        assert int_task["metadata"]["fsm"] == 42

        assert (task_dir / "4.json").exists()
        empty_task = json.loads((task_dir / "4.json").read_text())
        assert empty_task["subject"] == "Task with empty string fsm"
        assert empty_task["metadata"]["fsm"] == ""

        # Verify new skill-a task created with correct offset (after max preserved ID = 4)
        assert (task_dir / "5.json").exists()
        new_a1 = json.loads((task_dir / "5.json").read_text())
        assert new_a1["subject"] == "New A task"
        assert new_a1["metadata"]["fsm"] == "skill-a"


class TestPerSkillIdOffset:
    """Tests for ID offset calculation with per-skill scoping."""

    def test_offset_includes_other_fsm_tasks(self, tmp_path):
        """@per-skill-deletion:2.1 — ID offset includes other skills' FSM tasks."""
        # Set up task directory with tasks from multiple skills
        task_dir = tmp_path / "tasks" / "test-session"
        task_dir.mkdir(parents=True)

        # Create skill-a task at ID 2 (will be deleted)
        (task_dir / "2.json").write_text(json.dumps({
            "id": "2", "subject": "Skill-A task", "description": "",
            "activeForm": "", "owner": "", "status": "completed",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "skill-a"}
        }))

        # Create manual task at ID 3 (preserved)
        (task_dir / "3.json").write_text(json.dumps({
            "id": "3", "subject": "Manual task", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {}
        }))

        # Create skill-b task at ID 5 (preserved - highest ID)
        (task_dir / "5.json").write_text(json.dumps({
            "id": "5", "subject": "Skill-B task", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "skill-b"}
        }))

        # Create skill-a directory with fsm.json
        skill_dir = tmp_path / "project" / ".claude" / "skills" / "skill-a"
        skill_dir.mkdir(parents=True)
        (skill_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "New A task"}
        ]))

        # Run hook as skill-a
        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="skill-a",
            cwd=str(tmp_path / "project"),
            task_root=str(tmp_path / "tasks"),
            user_skills_root=str(tmp_path / "project" / ".claude" / "skills")
        )

        assert exit_code == 0, f"Hook failed: {stderr}"

        # Verify old skill-a task deleted
        assert not (task_dir / "2.json").exists()

        # Verify preserved tasks still exist
        assert (task_dir / "3.json").exists()
        assert (task_dir / "5.json").exists()

        # New task should start at ID 6 (offset from max preserved = 5, which is skill-b's task)
        assert (task_dir / "6.json").exists()
        new_a1 = json.loads((task_dir / "6.json").read_text())
        assert new_a1["subject"] == "New A task"
        assert new_a1["metadata"]["fsm"] == "skill-a"

    def test_offset_starts_at_1_with_no_tasks(self, tmp_path):
        """@per-skill-deletion:2.2 — Empty task directory starts IDs at 1."""
        # Set up empty task directory
        task_dir = tmp_path / "tasks" / "test-session"
        task_dir.mkdir(parents=True)

        # Create skill-a directory with fsm.json
        skill_dir = tmp_path / "project" / ".claude" / "skills" / "skill-a"
        skill_dir.mkdir(parents=True)
        (skill_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "First task"},
            {"id": 2, "subject": "Second task"}
        ]))

        # Run hook as skill-a
        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="skill-a",
            cwd=str(tmp_path / "project"),
            task_root=str(tmp_path / "tasks"),
            user_skills_root=str(tmp_path / "project" / ".claude" / "skills")
        )

        assert exit_code == 0, f"Hook failed: {stderr}"

        # Tasks should start at ID 1 (offset = 0 when no tasks exist)
        assert (task_dir / "1.json").exists()
        assert (task_dir / "2.json").exists()

        task1 = json.loads((task_dir / "1.json").read_text())
        assert task1["subject"] == "First task"
        assert task1["metadata"]["fsm"] == "skill-a"

        task2 = json.loads((task_dir / "2.json").read_text())
        assert task2["subject"] == "Second task"
        assert task2["metadata"]["fsm"] == "skill-a"

    def test_corrupted_task_file_aborts_offset(self, tmp_path):
        """@per-skill-deletion:2.3 — Corrupted task file aborts offset calculation."""
        # Set up task directory with valid and corrupted tasks
        task_dir = tmp_path / "tasks" / "test-session"
        task_dir.mkdir(parents=True)

        # Create valid task
        (task_dir / "1.json").write_text(json.dumps({
            "id": "1", "subject": "Valid task", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {}
        }))

        # Create corrupted task file (invalid JSON)
        (task_dir / "2.json").write_text("corrupted{{{not json")

        # Create skill-a directory with fsm.json
        skill_dir = tmp_path / "project" / ".claude" / "skills" / "skill-a"
        skill_dir.mkdir(parents=True)
        (skill_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "New task"}
        ]))

        # Run hook as skill-a - should abort
        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="skill-a",
            cwd=str(tmp_path / "project"),
            task_root=str(tmp_path / "tasks"),
            user_skills_root=str(tmp_path / "project" / ".claude" / "skills")
        )

        # Hook should fail due to corrupted file
        assert exit_code != 0, "Hook should have failed on corrupted task file"
        assert "Failed to read task file" in stderr or "ERROR" in stderr

        # No new tasks should be written
        assert not (task_dir / "3.json").exists()


class TestErrorHandling:
    """Tests for error handling during hydration."""

    def test_deletion_abort_on_fs_error(self, tmp_path):
        """@task-hydration-skill:7.4 — FS error during deletion aborts with no new tasks."""
        import os

        # Set up task directory
        task_dir = tmp_path / "tasks" / "test-session"
        task_dir.mkdir(parents=True)

        # Create skill-a task (will attempt deletion)
        (task_dir / "1.json").write_text(json.dumps({
            "id": "1", "subject": "Skill-A task", "description": "",
            "activeForm": "", "owner": "", "status": "completed",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "skill-a"}
        }))

        # Create skill-a directory with fsm.json
        skill_dir = tmp_path / "project" / ".claude" / "skills" / "skill-a"
        skill_dir.mkdir(parents=True)
        (skill_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "New task"}
        ]))

        # Make task directory read-only to prevent deletion
        os.chmod(task_dir, 0o555)

        try:
            # Run hook as skill-a - should abort on deletion failure
            exit_code, stdout, stderr = run_hook(
                session_id="test-session",
                command_name="skill-a",
                cwd=str(tmp_path / "project"),
                task_root=str(tmp_path / "tasks"),
                user_skills_root=str(tmp_path / "project" / ".claude" / "skills")
            )

            # Hook should fail
            assert exit_code != 0, "Hook should have failed on deletion error"
            assert "ERROR" in stderr

            # Original task should still exist (deletion failed)
            assert (task_dir / "1.json").exists()

            # No new tasks written
            assert not (task_dir / "2.json").exists()
        finally:
            # Restore permissions for cleanup
            os.chmod(task_dir, 0o755)

    def test_write_failure_leaves_zero_tasks(self, tmp_path, hydrate_module):
        """@task-hydration-skill:7.5 — Write failure after deletion leaves zero matching tasks."""
        from unittest.mock import patch

        # Set up task directory
        task_dir = tmp_path / "tasks" / "test-session"
        task_dir.mkdir(parents=True)

        # Create skill-a task (will be deleted)
        (task_dir / "1.json").write_text(json.dumps({
            "id": "1", "subject": "Old task", "description": "",
            "activeForm": "", "owner": "", "status": "completed",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "test-skill"}
        }))

        # Delete the matching task
        hydrate_module.delete_skill_tasks(task_dir, "test-skill")
        assert not (task_dir / "1.json").exists()

        # Attempt to write new tasks but simulate write failure
        new_tasks = [
            {"id": 1, "subject": "New task", "description": "",
             "activeForm": "", "owner": "", "status": "pending",
             "blocks": [], "blockedBy": []}
        ]

        with pytest.raises(SystemExit):
            with patch("builtins.open", side_effect=OSError("disk full")):
                hydrate_module.write_tasks(task_dir, new_tasks, "test-skill")

        # Verify zero matching tasks remain
        matching = [f for f in task_dir.glob("*.json")
                    if json.loads(f.read_text()).get("metadata", {}).get("fsm") == "test-skill"]
        assert len(matching) == 0, "Should have zero matching tasks after write failure"


class TestIntegration:
    """End-to-end integration tests for multi-skill scenarios."""

    def test_invoke_skill_b_with_skill_a_active(self, tmp_path):
        """@integration:1.1 — Invoke skill-b while skill-a has in_progress tasks."""
        # Set up task directory
        task_dir = tmp_path / "tasks" / "test-session"
        task_dir.mkdir(parents=True)

        # Create skill-a task with in_progress status
        (task_dir / "1.json").write_text(json.dumps({
            "id": "1", "subject": "Skill-A in progress", "description": "",
            "activeForm": "", "owner": "", "status": "in_progress",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "skill-a"}
        }))

        # Create old skill-b task (will be deleted)
        (task_dir / "2.json").write_text(json.dumps({
            "id": "2", "subject": "Old Skill-B task", "description": "",
            "activeForm": "", "owner": "", "status": "completed",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "skill-b"}
        }))

        # Create skill-b directory with fsm.json
        skill_dir = tmp_path / "project" / ".claude" / "skills" / "skill-b"
        skill_dir.mkdir(parents=True)
        (skill_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "New B task"}
        ]))

        # Run hook as skill-b - should pass (skill-a's active tasks don't block skill-b)
        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="skill-b",
            cwd=str(tmp_path / "project"),
            task_root=str(tmp_path / "tasks"),
            user_skills_root=str(tmp_path / "project" / ".claude" / "skills")
        )

        assert exit_code == 0, f"Hook should succeed for skill-b: {stderr}"

        # Verify skill-a task preserved (not deleted, not modified)
        assert (task_dir / "1.json").exists()
        skill_a_task = json.loads((task_dir / "1.json").read_text())
        assert skill_a_task["subject"] == "Skill-A in progress"
        assert skill_a_task["status"] == "in_progress"
        assert skill_a_task["metadata"]["fsm"] == "skill-a"

        # Verify new skill-b task created (old was deleted, new created at ID 2)
        # Offset is from max preserved (skill-a at 1), so new task is at 2
        assert (task_dir / "2.json").exists()
        new_b_task = json.loads((task_dir / "2.json").read_text())
        assert new_b_task["subject"] == "New B task", "Task content should be NEW task, not old"
        assert new_b_task["metadata"]["fsm"] == "skill-b"
        assert new_b_task["status"] == "pending", "New task should be pending, not completed"

    def test_re_invoke_skill_a_all_completed(self, tmp_path):
        """@integration:1.2 — Re-invoke skill-a when all tasks completed while skill-b exists."""
        # Set up task directory
        task_dir = tmp_path / "tasks" / "test-session"
        task_dir.mkdir(parents=True)

        # Create completed skill-a tasks
        (task_dir / "1.json").write_text(json.dumps({
            "id": "1", "subject": "Old A task 1", "description": "",
            "activeForm": "", "owner": "", "status": "completed",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "skill-a"}
        }))
        (task_dir / "2.json").write_text(json.dumps({
            "id": "2", "subject": "Old A task 2", "description": "",
            "activeForm": "", "owner": "", "status": "completed",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "skill-a"}
        }))

        # Create pending skill-b task (should be preserved)
        (task_dir / "3.json").write_text(json.dumps({
            "id": "3", "subject": "Skill-B task", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "skill-b"}
        }))

        # Create skill-a directory with fsm.json
        skill_dir = tmp_path / "project" / ".claude" / "skills" / "skill-a"
        skill_dir.mkdir(parents=True)
        (skill_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "New A task"}
        ]))

        # Run hook as skill-a - should pass (all completed)
        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="skill-a",
            cwd=str(tmp_path / "project"),
            task_root=str(tmp_path / "tasks"),
            user_skills_root=str(tmp_path / "project" / ".claude" / "skills")
        )

        assert exit_code == 0, f"Hook should succeed: {stderr}"

        # Verify old skill-a tasks deleted
        assert not (task_dir / "1.json").exists()
        assert not (task_dir / "2.json").exists()

        # Verify skill-b task preserved
        assert (task_dir / "3.json").exists()
        skill_b_task = json.loads((task_dir / "3.json").read_text())
        assert skill_b_task["subject"] == "Skill-B task"

        # Verify new skill-a task with correct offset (after skill-b at 3)
        assert (task_dir / "4.json").exists()
        new_a_task = json.loads((task_dir / "4.json").read_text())
        assert new_a_task["subject"] == "New A task"
        assert new_a_task["metadata"]["fsm"] == "skill-a"

    def test_sequential_skill_a_then_skill_b(self, tmp_path):
        """@integration:2.1 — Sequential invocation produces combined task set."""
        # Set up empty task directory
        task_dir = tmp_path / "tasks" / "test-session"
        task_dir.mkdir(parents=True)

        # Create skill-a directory
        skill_a_dir = tmp_path / "project" / ".claude" / "skills" / "skill-a"
        skill_a_dir.mkdir(parents=True)
        (skill_a_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "A task 1"},
            {"id": 2, "subject": "A task 2", "blockedBy": [1]}
        ]))

        # First: invoke skill-a
        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="skill-a",
            cwd=str(tmp_path / "project"),
            task_root=str(tmp_path / "tasks"),
            user_skills_root=str(tmp_path / "project" / ".claude" / "skills")
        )

        assert exit_code == 0, f"Skill-a hook failed: {stderr}"
        assert (task_dir / "1.json").exists()
        assert (task_dir / "2.json").exists()

        # Create skill-b directory
        skill_b_dir = tmp_path / "project" / ".claude" / "skills" / "skill-b"
        skill_b_dir.mkdir(parents=True)
        (skill_b_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "B task 1"},
            {"id": 2, "subject": "B task 2"},
            {"id": 3, "subject": "B task 3"}
        ]))

        # Second: invoke skill-b
        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="skill-b",
            cwd=str(tmp_path / "project"),
            task_root=str(tmp_path / "tasks"),
            user_skills_root=str(tmp_path / "project" / ".claude" / "skills")
        )

        assert exit_code == 0, f"Skill-b hook failed: {stderr}"

        # Verify all 5 tasks exist (skill-a: 1,2; skill-b: 3,4,5)
        assert (task_dir / "1.json").exists()
        assert (task_dir / "2.json").exists()
        assert (task_dir / "3.json").exists()
        assert (task_dir / "4.json").exists()
        assert (task_dir / "5.json").exists()

        # Verify task ownership
        task1 = json.loads((task_dir / "1.json").read_text())
        assert task1["metadata"]["fsm"] == "skill-a"

        task3 = json.loads((task_dir / "3.json").read_text())
        assert task3["metadata"]["fsm"] == "skill-b"

    def test_re_invoke_skill_a_after_skill_b(self, tmp_path):
        """@integration:2.2 — Re-invoke skill-a after skill-b with all pending."""
        # Set up task directory with initial skill-a tasks
        task_dir = tmp_path / "tasks" / "test-session"
        task_dir.mkdir(parents=True)

        # Create skill directories
        skill_a_dir = tmp_path / "project" / ".claude" / "skills" / "skill-a"
        skill_a_dir.mkdir(parents=True)
        skill_b_dir = tmp_path / "project" / ".claude" / "skills" / "skill-b"
        skill_b_dir.mkdir(parents=True)

        # First: invoke skill-a
        (skill_a_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "A task 1"},
            {"id": 2, "subject": "A task 2"}
        ]))

        exit_code, _, stderr = run_hook(
            session_id="test-session",
            command_name="skill-a",
            cwd=str(tmp_path / "project"),
            task_root=str(tmp_path / "tasks"),
            user_skills_root=str(tmp_path / "project" / ".claude" / "skills")
        )
        assert exit_code == 0, f"Failed: {stderr}"

        # Second: invoke skill-b
        (skill_b_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "B task 1"},
            {"id": 2, "subject": "B task 2"},
            {"id": 3, "subject": "B task 3"}
        ]))

        exit_code, _, stderr = run_hook(
            session_id="test-session",
            command_name="skill-b",
            cwd=str(tmp_path / "project"),
            task_root=str(tmp_path / "tasks"),
            user_skills_root=str(tmp_path / "project" / ".claude" / "skills")
        )
        assert exit_code == 0, f"Failed: {stderr}"

        # Now we have: skill-a (1,2) and skill-b (3,4,5)
        # Third: re-invoke skill-a (all pending - should pass guard)
        (skill_a_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "New A task"}
        ]))

        exit_code, _, stderr = run_hook(
            session_id="test-session",
            command_name="skill-a",
            cwd=str(tmp_path / "project"),
            task_root=str(tmp_path / "tasks"),
            user_skills_root=str(tmp_path / "project" / ".claude" / "skills")
        )
        assert exit_code == 0, f"Failed: {stderr}"

        # Verify old skill-a tasks deleted
        old_a1 = json.loads((task_dir / "1.json").read_text()) if (task_dir / "1.json").exists() else None
        old_a2 = json.loads((task_dir / "2.json").read_text()) if (task_dir / "2.json").exists() else None

        # Either deleted or overwritten
        if old_a1:
            assert old_a1["subject"] != "A task 1", "Old task should be replaced"

        # Verify skill-b tasks preserved
        assert (task_dir / "3.json").exists()
        assert (task_dir / "4.json").exists()
        assert (task_dir / "5.json").exists()

        skill_b1 = json.loads((task_dir / "3.json").read_text())
        assert skill_b1["metadata"]["fsm"] == "skill-b"

        # Verify new skill-a task starts at 6 (offset from max preserved = 5)
        assert (task_dir / "6.json").exists()
        new_a = json.loads((task_dir / "6.json").read_text())
        assert new_a["subject"] == "New A task"
        assert new_a["metadata"]["fsm"] == "skill-a"

    def test_re_invoke_after_agent_starts_work(self, tmp_path):
        """@integration:2.3 — Re-invoke skill-a after agent starts - guard aborts."""
        # Set up task directory
        task_dir = tmp_path / "tasks" / "test-session"
        task_dir.mkdir(parents=True)

        # Create skill directories
        skill_a_dir = tmp_path / "project" / ".claude" / "skills" / "skill-a"
        skill_a_dir.mkdir(parents=True)
        skill_b_dir = tmp_path / "project" / ".claude" / "skills" / "skill-b"
        skill_b_dir.mkdir(parents=True)

        # First: invoke skill-a
        (skill_a_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "A task 1"}
        ]))

        run_hook(
            session_id="test-session",
            command_name="skill-a",
            cwd=str(tmp_path / "project"),
            task_root=str(tmp_path / "tasks"),
            user_skills_root=str(tmp_path / "project" / ".claude" / "skills")
        )

        # Second: invoke skill-b
        (skill_b_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "B task 1"}
        ]))

        run_hook(
            session_id="test-session",
            command_name="skill-b",
            cwd=str(tmp_path / "project"),
            task_root=str(tmp_path / "tasks"),
            user_skills_root=str(tmp_path / "project" / ".claude" / "skills")
        )

        # Simulate agent starting work on skill-a task
        task1_path = task_dir / "1.json"
        task1 = json.loads(task1_path.read_text())
        task1["status"] = "in_progress"
        task1_path.write_text(json.dumps(task1))

        # Third: attempt to re-invoke skill-a - should abort
        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="skill-a",
            cwd=str(tmp_path / "project"),
            task_root=str(tmp_path / "tasks"),
            user_skills_root=str(tmp_path / "project" / ".claude" / "skills")
        )

        # Guard should abort
        assert exit_code != 0, "Hook should fail when skill-a has in_progress tasks"
        assert "ERROR" in stderr

        # Verify all tasks unchanged
        task1_after = json.loads((task_dir / "1.json").read_text())
        assert task1_after["status"] == "in_progress", "Task should remain unchanged"
        assert task1_after["subject"] == "A task 1"

        task2_after = json.loads((task_dir / "2.json").read_text())
        assert task2_after["metadata"]["fsm"] == "skill-b"

    def test_offset_after_scoped_deletion_with_gaps(self, tmp_path):
        """@integration:3.1 — ID offset with non-contiguous preserved IDs."""
        # Set up task directory with gaps
        task_dir = tmp_path / "tasks" / "test-session"
        task_dir.mkdir(parents=True)

        # skill-a at 1 (will be deleted)
        (task_dir / "1.json").write_text(json.dumps({
            "id": "1", "subject": "Skill-A task", "description": "",
            "activeForm": "", "owner": "", "status": "completed",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "skill-a"}
        }))

        # manual at 5 (preserved)
        (task_dir / "5.json").write_text(json.dumps({
            "id": "5", "subject": "Manual task", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {}
        }))

        # skill-b at 10 (preserved - highest ID)
        (task_dir / "10.json").write_text(json.dumps({
            "id": "10", "subject": "Skill-B task", "description": "",
            "activeForm": "", "owner": "", "status": "pending",
            "blocks": [], "blockedBy": [],
            "metadata": {"fsm": "skill-b"}
        }))

        # Create skill-a with 2 tasks
        skill_dir = tmp_path / "project" / ".claude" / "skills" / "skill-a"
        skill_dir.mkdir(parents=True)
        (skill_dir / "fsm.json").write_text(json.dumps([
            {"id": 1, "subject": "New A task 1"},
            {"id": 2, "subject": "New A task 2"}
        ]))

        # Run hook as skill-a
        exit_code, stdout, stderr = run_hook(
            session_id="test-session",
            command_name="skill-a",
            cwd=str(tmp_path / "project"),
            task_root=str(tmp_path / "tasks"),
            user_skills_root=str(tmp_path / "project" / ".claude" / "skills")
        )

        assert exit_code == 0, f"Hook failed: {stderr}"

        # Verify old skill-a deleted
        assert not (task_dir / "1.json").exists()

        # Verify preserved tasks unchanged
        assert (task_dir / "5.json").exists()
        assert (task_dir / "10.json").exists()

        # New tasks should start at 11,12 (offset from max preserved = 10)
        assert (task_dir / "11.json").exists()
        assert (task_dir / "12.json").exists()

        task11 = json.loads((task_dir / "11.json").read_text())
        assert task11["subject"] == "New A task 1"
        assert task11["metadata"]["fsm"] == "skill-a"

        task12 = json.loads((task_dir / "12.json").read_text())
        assert task12["subject"] == "New A task 2"
        assert task12["metadata"]["fsm"] == "skill-a"
