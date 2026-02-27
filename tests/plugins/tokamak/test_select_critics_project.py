"""Tests for select_critics.py project awareness features."""

import json
import subprocess
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[3] / "plugins" / "tokamak" / "scripts" / "select_critics.py"


@pytest.fixture
def change_dir(tmp_path):
    """Change directory placed 3 levels deep so openspec_root resolves to tmp_path/openspec."""
    d = tmp_path / "openspec" / "changes" / "test-change"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def project_dir(tmp_path):
    """Project directory matching 'project: my-project' (resolved under openspec/)."""
    d = tmp_path / "openspec" / "my-project"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def config_with_project_critics(tmp_path):
    """Minimal critics config that includes requires_project critics."""
    config = {
        "output_template": "## OUTPUT\n",
        "critics": [
            {
                "name": "Functional",
                "files": ["functional.md"],
                "model": "sonnet",
                "skills": [],
                "evaluate": "evaluate functional.md"
            },
            {
                "name": "Functional Consistency",
                "files": ["functional.md"],
                "project_files": ["functional.md"],
                "requires_project": True,
                "model": "sonnet",
                "skills": [],
                "evaluate": "cross-reference functional.md"
            },
            {
                "name": "Technical Consistency",
                "files": ["technical.md", "requirements"],
                "project_files": ["technical.md", "requirements"],
                "requires_project": True,
                "model": "sonnet",
                "skills": [],
                "evaluate": "cross-reference technical artifacts"
            }
        ]
    }
    config_path = tmp_path / "test-critics.json"
    config_path.write_text(json.dumps(config))
    return config_path


def run_select_critics(change_dir: Path, extra_args: list[str] | None = None,
                       config: Path | None = None) -> tuple[int, str, str]:
    """Run select_critics.py and return (exit_code, stdout, stderr)."""
    cmd = ["python3", str(SCRIPT_PATH), str(change_dir)]
    if config:
        cmd.extend(["--config", str(config)])
    if extra_args:
        cmd.extend(extra_args)

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


class TestNoProjectField:
    """Behavior when .openspec.yaml has no project field."""

    def test_no_project_field_behaves_identically(self, change_dir, config_with_project_critics):
        """No project field means project_files empty, requires_project critics skipped."""
        # Create .openspec.yaml without project field
        (change_dir / ".openspec.yaml").write_text("schema: chaos-theory\n")
        # Create the change files that regular critics need
        (change_dir / "functional.md").write_text("# Functional\n")

        exit_code, stdout, stderr = run_select_critics(
            change_dir, ["--force"], config=config_with_project_critics
        )

        assert exit_code == 0
        result = json.loads(stdout)

        # Regular Functional critic should be selected
        names = [c["name"] for c in result["critics"]]
        assert "Functional" in names

        # Project consistency critics should be skipped
        assert "Functional Consistency" not in names
        assert "Technical Consistency" not in names

        # Verify skip reason in stderr
        assert "project docs not available" in stderr

    def test_no_project_field_empty_project_files(self, change_dir, config_with_project_critics):
        """Output should have empty project_files arrays when no project."""
        (change_dir / ".openspec.yaml").write_text("schema: chaos-theory\n")
        (change_dir / "functional.md").write_text("# Functional\n")

        exit_code, stdout, stderr = run_select_critics(
            change_dir, ["--force"], config=config_with_project_critics
        )

        assert exit_code == 0
        result = json.loads(stdout)
        for critic in result["critics"]:
            assert critic["project_files"] == []


class TestProjectFieldWithExistingDir:
    """Behavior when project field points to an existing project directory."""

    def test_project_files_in_output(self, change_dir, project_dir, config_with_project_critics):
        """Project files appear in output when project dir exists."""
        (change_dir / ".openspec.yaml").write_text(
            "schema: chaos-theory\nproject: my-project\n"
        )
        (change_dir / "functional.md").write_text("# Change Functional\n")
        (project_dir / "functional.md").write_text("# Project Functional\n")

        exit_code, stdout, stderr = run_select_critics(
            change_dir, ["--force"], config=config_with_project_critics
        )

        assert exit_code == 0
        result = json.loads(stdout)
        names = {c["name"]: c for c in result["critics"]}

        # Both regular and project consistency critics should be selected
        assert "Functional" in names
        assert "Functional Consistency" in names

        # Project files should be populated
        assert names["Functional Consistency"]["project_files"] == ["functional.md"]

        # Regular critic should have empty project_files
        assert names["Functional"]["project_files"] == []

    def test_project_file_hashes_tracked(self, change_dir, project_dir, config_with_project_critics):
        """Project file hashes are stored under project: prefix in .hashes.json."""
        (change_dir / ".openspec.yaml").write_text(
            "schema: chaos-theory\nproject: my-project\n"
        )
        (change_dir / "functional.md").write_text("# Change Functional\n")
        (project_dir / "functional.md").write_text("# Project Functional\n")

        # First run: update hashes
        exit_code, _, _ = run_select_critics(
            change_dir, ["--update-hashes"], config=config_with_project_critics
        )
        assert exit_code == 0

        # Check hash file
        hashes = json.loads((change_dir / ".hashes.json").read_text())
        assert "functional.md" in hashes, "Change file hash should be tracked"
        assert "project:functional.md" in hashes, "Project file hash should be tracked with prefix"

        # The two hashes should be different (different file content)
        assert hashes["functional.md"] != hashes["project:functional.md"]

    def test_project_file_change_triggers_critic(self, change_dir, project_dir, config_with_project_critics):
        """A change to a project file triggers the requires_project critic."""
        (change_dir / ".openspec.yaml").write_text(
            "schema: chaos-theory\nproject: my-project\n"
        )
        (change_dir / "functional.md").write_text("# Change Functional\n")
        (project_dir / "functional.md").write_text("# Project Functional v1\n")

        # First run: store hashes
        run_select_critics(change_dir, ["--update-hashes"], config=config_with_project_critics)

        # Now change the project file (not the change file)
        (project_dir / "functional.md").write_text("# Project Functional v2 - updated\n")

        # Second run: should detect the change
        exit_code, stdout, stderr = run_select_critics(
            change_dir, config=config_with_project_critics
        )

        assert exit_code == 0
        result = json.loads(stdout)
        names = [c["name"] for c in result["critics"]]

        # Functional Consistency should be selected due to project file change
        assert "Functional Consistency" in names
        assert "changed: project:functional.md" in stderr

    def test_requires_project_critics_appear_in_selection(self, change_dir, project_dir, config_with_project_critics):
        """requires_project critics are included when project dir is available."""
        (change_dir / ".openspec.yaml").write_text(
            "schema: chaos-theory\nproject: my-project\n"
        )
        (change_dir / "functional.md").write_text("# Functional\n")
        (project_dir / "functional.md").write_text("# Project Functional\n")
        (change_dir / "technical.md").write_text("# Technical\n")
        (project_dir / "technical.md").write_text("# Project Technical\n")

        # Create requirements dirs
        req_dir = change_dir / "requirements"
        req_dir.mkdir()
        (req_dir / "test.feature.md").write_text("Feature: test\n")
        proj_req_dir = project_dir / "requirements"
        proj_req_dir.mkdir()
        (proj_req_dir / "test.feature.md").write_text("Feature: project test\n")

        exit_code, stdout, stderr = run_select_critics(
            change_dir, ["--force"], config=config_with_project_critics
        )

        assert exit_code == 0
        result = json.loads(stdout)
        names = [c["name"] for c in result["critics"]]

        assert "Functional Consistency" in names
        assert "Technical Consistency" in names


class TestProjectFieldWithMissingDir:
    """Behavior when project field points to a non-existent directory."""

    def test_project_files_skipped(self, change_dir, config_with_project_critics):
        """Project files are skipped when project dir doesn't exist."""
        (change_dir / ".openspec.yaml").write_text(
            "schema: chaos-theory\nproject: nonexistent-project\n"
        )
        (change_dir / "functional.md").write_text("# Functional\n")

        exit_code, stdout, stderr = run_select_critics(
            change_dir, ["--force"], config=config_with_project_critics
        )

        assert exit_code == 0
        assert "does not exist yet" in stderr

        result = json.loads(stdout)
        names = [c["name"] for c in result["critics"]]

        # requires_project critics should be skipped
        assert "Functional Consistency" not in names
        assert "Technical Consistency" not in names

        # Regular critics should still work
        assert "Functional" in names

    def test_requires_project_critics_filtered(self, change_dir, config_with_project_critics):
        """requires_project critics are filtered out when project dir is missing."""
        (change_dir / ".openspec.yaml").write_text(
            "schema: chaos-theory\nproject: nonexistent\n"
        )
        (change_dir / "functional.md").write_text("# Functional\n")

        exit_code, stdout, stderr = run_select_critics(
            change_dir, ["--force"], config=config_with_project_critics
        )

        assert exit_code == 0
        assert "project docs not available" in stderr


class TestSeparateHashKeyNamespacing:
    """Change and project files use separate hash key namespaces."""

    def test_same_filename_different_keys(self, change_dir, project_dir, config_with_project_critics):
        """functional.md and project:functional.md are tracked as separate hash keys."""
        (change_dir / ".openspec.yaml").write_text(
            "schema: chaos-theory\nproject: my-project\n"
        )
        # Write identical content to both
        content = "# Identical Functional Content\n"
        (change_dir / "functional.md").write_text(content)
        (project_dir / "functional.md").write_text(content)

        # Update hashes
        run_select_critics(change_dir, ["--update-hashes"], config=config_with_project_critics)

        hashes = json.loads((change_dir / ".hashes.json").read_text())

        # Both keys should exist
        assert "functional.md" in hashes
        assert "project:functional.md" in hashes

        # Same content = same hash value, but different keys
        assert hashes["functional.md"] == hashes["project:functional.md"]

    def test_changing_change_file_doesnt_affect_project_hash(self, change_dir, project_dir, config_with_project_critics):
        """Changing the change's functional.md doesn't affect project:functional.md hash."""
        (change_dir / ".openspec.yaml").write_text(
            "schema: chaos-theory\nproject: my-project\n"
        )
        (change_dir / "functional.md").write_text("# v1\n")
        (project_dir / "functional.md").write_text("# Project stable\n")

        # Store initial hashes
        run_select_critics(change_dir, ["--update-hashes"], config=config_with_project_critics)
        hashes_v1 = json.loads((change_dir / ".hashes.json").read_text())

        # Modify only the change file
        (change_dir / "functional.md").write_text("# v2 modified\n")

        # Run again with --update-hashes
        run_select_critics(change_dir, ["--update-hashes"], config=config_with_project_critics)
        hashes_v2 = json.loads((change_dir / ".hashes.json").read_text())

        # Change file hash should differ
        assert hashes_v1["functional.md"] != hashes_v2["functional.md"]

        # Project file hash should be unchanged
        assert hashes_v1["project:functional.md"] == hashes_v2["project:functional.md"]


class TestCriticsWithoutProjectFiles:
    """Regular critics (no project_files) are unaffected by project awareness."""

    def test_regular_critics_unaffected(self, change_dir, project_dir, config_with_project_critics):
        """Critics without project_files behave identically regardless of project state."""
        (change_dir / ".openspec.yaml").write_text(
            "schema: chaos-theory\nproject: my-project\n"
        )
        (change_dir / "functional.md").write_text("# Functional\n")
        (project_dir / "functional.md").write_text("# Project Functional\n")

        exit_code, stdout, _ = run_select_critics(
            change_dir, ["--force"], config=config_with_project_critics
        )

        assert exit_code == 0
        result = json.loads(stdout)

        # Find the regular Functional critic
        regular = next(c for c in result["critics"] if c["name"] == "Functional")

        # It should have empty project_files
        assert regular["project_files"] == []

        # Its files should be the change-local files only
        assert regular["files"] == ["functional.md"]


class TestProjectDirExpansion:
    """Project directory files are expanded correctly in output."""

    def test_project_directory_files_expanded(self, change_dir, project_dir, config_with_project_critics):
        """Project directory (e.g., requirements/) expands to individual files."""
        (change_dir / ".openspec.yaml").write_text(
            "schema: chaos-theory\nproject: my-project\n"
        )
        (change_dir / "functional.md").write_text("# Functional\n")
        (change_dir / "technical.md").write_text("# Technical\n")
        (project_dir / "technical.md").write_text("# Project Technical\n")

        # Create requirements as a directory with files
        change_req = change_dir / "requirements"
        change_req.mkdir()
        (change_req / "cap-a").mkdir(parents=True)
        (change_req / "cap-a" / "requirements.feature.md").write_text("Feature: A\n")

        project_req = project_dir / "requirements"
        project_req.mkdir()
        (project_req / "cap-x").mkdir()
        (project_req / "cap-x" / "requirements.feature.md").write_text("Feature: X\n")
        (project_req / "cap-y").mkdir()
        (project_req / "cap-y" / "requirements.feature.md").write_text("Feature: Y\n")

        exit_code, stdout, _ = run_select_critics(
            change_dir, ["--force"], config=config_with_project_critics
        )

        assert exit_code == 0
        result = json.loads(stdout)

        # Find Technical Consistency critic
        tech = next(c for c in result["critics"] if c["name"] == "Technical Consistency")

        # Project files should be expanded from the requirements directory
        assert "technical.md" in tech["project_files"]
        # Requirements directory should expand to individual files
        project_files = tech["project_files"]
        req_files = [f for f in project_files if "requirements" in f]
        assert len(req_files) >= 2, f"Expected expanded requirement files, got: {project_files}"


class TestListMode:
    """--list mode includes project consistency critics when available."""

    def test_list_includes_project_critics(self, change_dir, project_dir, config_with_project_critics):
        """--list output includes project consistency critic names."""
        (change_dir / ".openspec.yaml").write_text(
            "schema: chaos-theory\nproject: my-project\n"
        )
        (change_dir / "functional.md").write_text("# Functional\n")
        (project_dir / "functional.md").write_text("# Project Functional\n")

        exit_code, stdout, _ = run_select_critics(
            change_dir, ["--force", "--list"], config=config_with_project_critics
        )

        assert exit_code == 0
        names = json.loads(stdout)
        assert "Functional Consistency" in names

    def test_list_excludes_project_critics_when_no_project(self, change_dir, config_with_project_critics):
        """--list output excludes project consistency critics when no project."""
        (change_dir / ".openspec.yaml").write_text("schema: chaos-theory\n")
        (change_dir / "functional.md").write_text("# Functional\n")

        exit_code, stdout, _ = run_select_critics(
            change_dir, ["--force", "--list"], config=config_with_project_critics
        )

        assert exit_code == 0
        names = json.loads(stdout)
        assert "Functional Consistency" not in names
        assert "Technical Consistency" not in names


class TestSelectionReport:
    """Output includes selection_report with all critics and selection status."""

    def test_report_includes_all_critics(self, change_dir, config_with_project_critics):
        """selection_report lists every critic, selected or not."""
        (change_dir / ".openspec.yaml").write_text("schema: chaos-theory\n")
        # Only create functional.md — Technical Consistency will be skipped (missing files)
        (change_dir / "functional.md").write_text("# Functional\n")

        exit_code, stdout, stderr = run_select_critics(
            change_dir, ["--force"], config=config_with_project_critics
        )

        assert exit_code == 0
        result = json.loads(stdout)

        # selection_report should be present
        assert "selection_report" in result
        report = result["selection_report"]

        # Should have an entry for every critic in the config (3 total)
        assert len(report) == 3

        # Each entry should have name, selected, and reason
        for entry in report:
            assert "name" in entry
            assert "selected" in entry
            assert isinstance(entry["selected"], bool)
            assert "reason" in entry

    def test_report_reflects_selection_status(self, change_dir, config_with_project_critics):
        """Selected critics have selected=True, skipped ones have selected=False."""
        (change_dir / ".openspec.yaml").write_text("schema: chaos-theory\n")
        (change_dir / "functional.md").write_text("# Functional\n")

        exit_code, stdout, _ = run_select_critics(
            change_dir, ["--force"], config=config_with_project_critics
        )

        assert exit_code == 0
        result = json.loads(stdout)
        report = {e["name"]: e for e in result["selection_report"]}

        # Functional should be selected (file exists, --force)
        assert report["Functional"]["selected"] is True

        # Project critics should be skipped (no project field)
        assert report["Functional Consistency"]["selected"] is False
        assert report["Technical Consistency"]["selected"] is False

    def test_report_absent_in_list_mode(self, change_dir, config_with_project_critics):
        """--list mode outputs just names, no selection_report."""
        (change_dir / ".openspec.yaml").write_text("schema: chaos-theory\n")
        (change_dir / "functional.md").write_text("# Functional\n")

        exit_code, stdout, _ = run_select_critics(
            change_dir, ["--force", "--list"], config=config_with_project_critics
        )

        assert exit_code == 0
        # --list mode outputs a plain JSON list of names
        result = json.loads(stdout)
        assert isinstance(result, list)


class TestTemplateResolution:
    """Schema templates are resolved and included in critic output."""

    def test_templates_resolved_from_schema(self, change_dir, tmp_path, config_with_project_critics):
        """Critics get template content when schema has a templates directory."""
        (change_dir / ".openspec.yaml").write_text("schema: test-schema\n")
        (change_dir / "functional.md").write_text("# Functional\n")

        # Create schema templates directory
        templates_dir = tmp_path / "openspec" / "schemas" / "test-schema" / "templates"
        templates_dir.mkdir(parents=True)
        (templates_dir / "functional.md").write_text("<!-- functional template instructions -->")

        exit_code, stdout, stderr = run_select_critics(
            change_dir, ["--force"], config=config_with_project_critics
        )

        assert exit_code == 0
        result = json.loads(stdout)
        func = next(c for c in result["critics"] if c["name"] == "Functional")
        assert "functional.md" in func["templates"]
        assert "functional template instructions" in func["templates"]["functional.md"]

    def test_templates_empty_when_no_schema_dir(self, change_dir, tmp_path, config_with_project_critics):
        """Templates dict is empty when schema has no templates directory."""
        (change_dir / ".openspec.yaml").write_text("schema: nonexistent-schema\n")
        (change_dir / "functional.md").write_text("# Functional\n")

        exit_code, stdout, stderr = run_select_critics(
            change_dir, ["--force"], config=config_with_project_critics
        )

        assert exit_code == 0
        result = json.loads(stdout)
        func = next(c for c in result["critics"] if c["name"] == "Functional")
        assert func["templates"] == {}

    def test_templates_directory_maps_to_feature_template(self, change_dir, tmp_path, config_with_project_critics):
        """A 'requirements' file entry resolves to 'requirements.feature.md' template."""
        (change_dir / ".openspec.yaml").write_text(
            "schema: test-schema\nproject: my-project\n"
        )
        (change_dir / "functional.md").write_text("# Functional\n")
        (change_dir / "technical.md").write_text("# Technical\n")

        # requirements as a directory (the artifact type)
        req_dir = change_dir / "requirements"
        req_dir.mkdir()
        (req_dir / "cap-a").mkdir()
        (req_dir / "cap-a" / "requirements.feature.md").write_text("Feature: A\n")

        # Project dir for requires_project critics
        project_dir = tmp_path / "openspec" / "my-project"
        project_dir.mkdir(parents=True)
        (project_dir / "technical.md").write_text("# Project Technical\n")
        proj_req = project_dir / "requirements"
        proj_req.mkdir()
        (proj_req / "cap-x").mkdir()
        (proj_req / "cap-x" / "requirements.feature.md").write_text("Feature: X\n")

        # Create templates
        templates_dir = tmp_path / "openspec" / "schemas" / "test-schema" / "templates"
        templates_dir.mkdir(parents=True)
        (templates_dir / "requirements.feature.md").write_text("<!-- requirements template -->")
        (templates_dir / "technical.md").write_text("<!-- technical template -->")

        exit_code, stdout, stderr = run_select_critics(
            change_dir, ["--force"], config=config_with_project_critics
        )

        assert exit_code == 0
        result = json.loads(stdout)
        tech = next(c for c in result["critics"] if c["name"] == "Technical Consistency")
        assert "requirements" in tech["templates"]
        assert "requirements template" in tech["templates"]["requirements"]
        assert "technical.md" in tech["templates"]

    def test_templates_skip_missing_files(self, change_dir, tmp_path, config_with_project_critics):
        """Files without a matching template are omitted from the templates dict."""
        (change_dir / ".openspec.yaml").write_text("schema: test-schema\n")
        (change_dir / "functional.md").write_text("# Functional\n")

        # Create templates dir with NO functional.md template
        templates_dir = tmp_path / "openspec" / "schemas" / "test-schema" / "templates"
        templates_dir.mkdir(parents=True)
        (templates_dir / "other.md").write_text("<!-- other template -->")

        exit_code, stdout, stderr = run_select_critics(
            change_dir, ["--force"], config=config_with_project_critics
        )

        assert exit_code == 0
        result = json.loads(stdout)
        func = next(c for c in result["critics"] if c["name"] == "Functional")
        assert "functional.md" not in func["templates"]
        assert func["templates"] == {}
