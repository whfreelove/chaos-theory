"""Tests for change_dashboard.sh — lifecycle status dashboard."""

import json
import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "plugins"
    / "tokamak"
    / "scripts"
    / "change_dashboard.sh"
)


class DashboardRunner:
    """Helper to run change_dashboard.sh with a mocked openspec CLI."""

    def __init__(self, tmp_path):
        self.tmp_path = tmp_path
        self.bin_dir = tmp_path / "bin"
        self.bin_dir.mkdir()
        self.openspec_root = tmp_path / "openspec"
        self.openspec_root.mkdir()
        self.changes_root = self.openspec_root / "changes"
        self.changes_root.mkdir()
        self._schema_entries = []

    def add_change(self, name, fields=None, archived=False):
        """Create a change directory with optional .openspec.yaml fields."""
        parent = self.changes_root / "archive" if archived else self.changes_root
        d = parent / name
        d.mkdir(parents=True, exist_ok=True)
        if fields:
            lines = [f"{k}: {v}" for k, v in fields.items()]
            (d / ".openspec.yaml").write_text("\n".join(lines) + "\n")
        return d

    def add_schema(self, name, version, source="project"):
        """Create a schema directory and register it for openspec output."""
        d = self.openspec_root / "schemas" / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "schema.yaml").write_text(f"name: {name}\nversion: {version}\n")
        self._schema_entries.append(
            {"name": name, "source": source, "path": str(d), "shadows": []}
        )

    def add_project(self, name):
        """Create a project directory under openspec_root."""
        d = self.openspec_root / name
        d.mkdir(parents=True, exist_ok=True)
        return d

    def run(self, archive=False):
        """Execute change_dashboard.sh with fake openspec in PATH."""
        json_file = self.bin_dir / "schema_output.json"
        json_file.write_text(json.dumps(self._schema_entries))

        fake_openspec = self.bin_dir / "openspec"
        fake_openspec.write_text(f'#!/bin/bash\ncat "{json_file}"\n')
        fake_openspec.chmod(0o755)

        env = dict(os.environ)
        env["PATH"] = f"{self.bin_dir}:{env['PATH']}"

        cmd = ["bash", str(SCRIPT)]
        if archive:
            cmd.append("--archive")
        cmd.append(str(self.changes_root))

        return subprocess.run(
            cmd, capture_output=True, text=True, env=env, timeout=30
        )


@pytest.fixture
def runner(tmp_path):
    return DashboardRunner(tmp_path)


def data_rows(output):
    """Extract data rows from dashboard output (skip header + separator)."""
    lines = output.strip().split("\n")
    return [l for l in lines[2:] if l.strip() and not l.startswith("No ") and not l.startswith("Projects ") and not l.startswith("All projects")]


def parse_row(line):
    """Parse a pipe-delimited dashboard row into a dict."""
    cells = [c.strip() for c in line.split("|") if c.strip()]
    return {
        "change": cells[0] if len(cells) > 0 else "",
        "project": cells[1] if len(cells) > 1 else "",
        "schema": cells[2] if len(cells) > 2 else "",
        "version": cells[3] if len(cells) > 3 else "",
        "specs_status": cells[4] if len(cells) > 4 else "",
        "code_status": cells[5] if len(cells) > 5 else "",
        "created": cells[6] if len(cells) > 6 else "",
    }


# --- Test cases ---


class TestHappyPath:
    """Full dashboard with 3 changes, all fields populated, versions resolved."""

    def test_all_rows_and_fields(self, runner):
        runner.add_schema("chaos-theory", 2)
        runner.add_schema("spec-driven", 1, source="package")

        runner.add_change(
            "alpha",
            {
                "schema": "chaos-theory",
                "specs-status": "new",
                "code-status": "waiting",
                "created": "2026-02-14",
            },
        )
        runner.add_change(
            "beta",
            {
                "schema": "spec-driven",
                "specs-status": "draft",
                "code-status": "ready",
                "created": "2026-02-10",
            },
        )
        runner.add_change(
            "gamma",
            {
                "schema": "chaos-theory",
                "specs-status": "ratified",
                "code-status": "done",
                "created": "2026-02-01",
            },
        )

        result = runner.run()
        assert result.returncode == 0

        rows = data_rows(result.stdout)
        assert len(rows) == 3

        alpha = parse_row(rows[0])
        assert alpha["change"] == "alpha"
        assert alpha["project"] == "-"
        assert alpha["schema"] == "chaos-theory"
        assert alpha["version"] == "2"
        assert alpha["specs_status"] == "new"
        assert alpha["code_status"] == "waiting"
        assert alpha["created"] == "2026-02-14"

        beta = parse_row(rows[1])
        assert beta["project"] == "-"
        assert beta["schema"] == "spec-driven"
        assert beta["version"] == "1"
        assert beta["specs_status"] == "draft"

        gamma = parse_row(rows[2])
        assert gamma["version"] == "2"
        assert gamma["code_status"] == "done"


class TestMissingOpenspecYaml:
    """Directory exists but has no .openspec.yaml → all dashes."""

    def test_all_fields_are_dashes(self, runner):
        runner.add_schema("chaos-theory", 1)
        runner.add_change("orphan")  # no .openspec.yaml

        result = runner.run()
        assert result.returncode == 0

        rows = data_rows(result.stdout)
        assert len(rows) == 1

        row = parse_row(rows[0])
        assert row["change"] == "orphan"
        assert row["project"] == "-"
        assert row["schema"] == "-"
        assert row["version"] == "-"
        assert row["specs_status"] == "-"
        assert row["code_status"] == "-"
        assert row["created"] == "-"


class TestPartialFields:
    """Only schema + created in .openspec.yaml → status fields are dashes, version resolved."""

    def test_missing_status_fields(self, runner):
        runner.add_schema("chaos-theory", 3)
        runner.add_change("partial", {"schema": "chaos-theory", "created": "2026-01-01"})

        result = runner.run()
        assert result.returncode == 0

        rows = data_rows(result.stdout)
        row = parse_row(rows[0])
        assert row["project"] == "-"
        assert row["schema"] == "chaos-theory"
        assert row["version"] == "3"
        assert row["specs_status"] == "-"
        assert row["code_status"] == "-"
        assert row["created"] == "2026-01-01"


class TestUnknownSchema:
    """Schema name not in openspec output → version is dash."""

    def test_version_is_dash(self, runner):
        runner.add_schema("chaos-theory", 1)
        runner.add_change("mystery", {"schema": "foo", "created": "2026-01-15"})

        result = runner.run()
        assert result.returncode == 0

        rows = data_rows(result.stdout)
        row = parse_row(rows[0])
        assert row["schema"] == "foo"
        assert row["version"] == "-"


class TestEmptyChangesDir:
    """No change directories → 'No active changes' message."""

    def test_shows_no_changes_message(self, runner):
        result = runner.run()
        assert result.returncode == 0
        assert "No active changes found." in result.stdout


class TestArchiveFlag:
    """--archive includes both active and archived changes."""

    def test_archive_includes_both(self, runner):
        runner.add_schema("chaos-theory", 1)
        runner.add_change(
            "active-one", {"schema": "chaos-theory", "created": "2026-02-01"}
        )
        runner.add_change(
            "old-one",
            {"schema": "chaos-theory", "created": "2025-12-01"},
            archived=True,
        )

        result = runner.run(archive=True)
        assert result.returncode == 0

        rows = data_rows(result.stdout)
        assert len(rows) == 2
        names = [parse_row(r)["change"] for r in rows]
        assert "active-one" in names
        assert "old-one" in names

    def test_without_archive_excludes_archived(self, runner):
        runner.add_change("active-one", {"schema": "x", "created": "2026-02-01"})
        runner.add_change(
            "old-one", {"schema": "x", "created": "2025-12-01"}, archived=True
        )

        result = runner.run(archive=False)
        rows = data_rows(result.stdout)
        assert len(rows) == 1
        assert parse_row(rows[0])["change"] == "active-one"


class TestArchiveWithoutDir:
    """--archive when no archive/ subdirectory exists → no error."""

    def test_no_error(self, runner):
        runner.add_change("only-active", {"schema": "x", "created": "2026-02-01"})

        result = runner.run(archive=True)
        assert result.returncode == 0

        rows = data_rows(result.stdout)
        assert len(rows) == 1
        assert parse_row(rows[0])["change"] == "only-active"


class TestProjectColumn:
    """PROJECT column shows basename of the project field."""

    def test_project_shows_basename(self, runner):
        runner.add_change(
            "with-proj",
            {
                "schema": "chaos-theory",
                "project": "openspec/my-proj",
                "created": "2026-02-14",
            },
        )

        result = runner.run()
        assert result.returncode == 0

        rows = data_rows(result.stdout)
        assert len(rows) == 1
        row = parse_row(rows[0])
        assert row["change"] == "with-proj"
        assert row["project"] == "my-proj"

    def test_no_project_shows_dash(self, runner):
        runner.add_change("no-proj", {"schema": "chaos-theory", "created": "2026-02-14"})

        result = runner.run()
        assert result.returncode == 0

        rows = data_rows(result.stdout)
        row = parse_row(rows[0])
        assert row["project"] == "-"


class TestProjectsFooter:
    """Projects footer shows idle projects."""

    def test_idle_project_shown(self, runner):
        runner.add_project("my-app")
        runner.add_change("some-change", {"schema": "x", "created": "2026-02-01"})

        result = runner.run()
        assert result.returncode == 0
        assert "Projects without active changes: my-app" in result.stdout

    def test_multiple_idle_projects(self, runner):
        runner.add_project("app-a")
        runner.add_project("app-b")
        runner.add_change("some-change", {"schema": "x", "created": "2026-02-01"})

        result = runner.run()
        assert result.returncode == 0
        assert "Projects without active changes:" in result.stdout
        assert "app-a" in result.stdout
        assert "app-b" in result.stdout


class TestProjectsFooterAllActive:
    """All projects have active changes → 'All projects have active changes.'"""

    def test_all_active(self, runner):
        runner.add_project("my-proj")
        runner.add_change(
            "change-a",
            {"schema": "x", "project": "openspec/my-proj", "created": "2026-02-01"},
        )

        result = runner.run()
        assert result.returncode == 0
        assert "All projects have active changes." in result.stdout


class TestProjectsFooterNoProjects:
    """No project dirs → no footer printed."""

    def test_no_footer(self, runner):
        runner.add_change("some-change", {"schema": "x", "created": "2026-02-01"})

        result = runner.run()
        assert result.returncode == 0
        assert "Projects without active changes" not in result.stdout
        assert "All projects have active changes" not in result.stdout


class TestEmptyChangesWithProjects:
    """No changes but project dirs exist → shows 'No active changes' + footer."""

    def test_no_changes_with_project_footer(self, runner):
        runner.add_project("idle-proj")

        result = runner.run()
        assert result.returncode == 0
        assert "No active changes found." in result.stdout
        assert "Projects without active changes: idle-proj" in result.stdout
