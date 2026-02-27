"""Tests for record_findings.py git commit auto-detection."""

import json
import subprocess
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[3] / "plugins" / "tokamak" / "scripts" / "record_findings.py"


@pytest.fixture
def git_repo(tmp_path):
    """Create a real git repo with an initial commit and a change subdirectory."""
    subprocess.run(['git', 'init'], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ['git', 'config', 'user.email', 'test@test.com'],
        cwd=tmp_path, capture_output=True, check=True,
    )
    subprocess.run(
        ['git', 'config', 'user.name', 'Test'],
        cwd=tmp_path, capture_output=True, check=True,
    )
    change_dir = tmp_path / "openspec" / "changes" / "test-change"
    change_dir.mkdir(parents=True)
    readme = tmp_path / "README.md"
    readme.write_text("# Test\n")
    subprocess.run(['git', 'add', '.'], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ['git', 'commit', '-m', 'init'],
        cwd=tmp_path, capture_output=True, check=True,
    )
    return tmp_path, change_dir


class TestRecordFindingsCommit:
    """record_findings.py includes git commit hash in round entries."""

    def test_includes_commit_hash(self, git_repo):
        """Round entry has 'commit' field matching HEAD."""
        repo_root, change_dir = git_repo

        # Get expected commit hash
        head = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=repo_root, capture_output=True, text=True, check=True,
        ).stdout.strip()

        # Prepare validation JSON (minimal valid input)
        validation = json.dumps([
            {'finding': 'Test-1: sample finding', 'status': 'UNCOVERED',
             'matched_gaps': [], 'match_reason': ''},
        ])

        # Run record_findings.py with the validation JSON on stdin
        result = subprocess.run(
            ['python3', str(SCRIPT_PATH), str(change_dir)],
            input=validation, capture_output=True, text=True,
            cwd=repo_root,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        # Read findings.json
        findings_path = change_dir / 'findings.json'
        assert findings_path.exists()
        rounds = json.loads(findings_path.read_text())
        assert len(rounds) == 1

        # Verify commit field
        assert 'commit' in rounds[0], f"Round entry missing 'commit': {rounds[0].keys()}"
        assert rounds[0]['commit'] == head

    def test_commit_absent_outside_git(self, tmp_path):
        """Round entry has empty or missing commit when not in a git repo."""
        change_dir = tmp_path / "no-repo-change"
        change_dir.mkdir(parents=True)

        validation = json.dumps([
            {'finding': 'Test-1: no-repo finding', 'status': 'UNCOVERED',
             'matched_gaps': [], 'match_reason': ''},
        ])

        result = subprocess.run(
            ['python3', str(SCRIPT_PATH), str(change_dir)],
            input=validation, capture_output=True, text=True,
            cwd=str(tmp_path),
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        rounds = json.loads((change_dir / 'findings.json').read_text())
        # commit should be empty string when not in a git repo
        assert rounds[0].get('commit', '') == ''
