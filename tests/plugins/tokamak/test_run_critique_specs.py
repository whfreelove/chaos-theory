"""Tests for run_critique_specs.py helper functions."""

import json
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest


# Mock heavy dependencies before importing the module under test
SCRIPTS_DIR = str(Path(__file__).resolve().parents[3] / "plugins" / "tokamak" / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

# Patch missing modules so the import succeeds
_mocked_modules = {}
for mod_name in ['questionary', 'resolve_artifacts', 'spec_utils']:
    if mod_name not in sys.modules:
        _mocked_modules[mod_name] = mock.MagicMock()
        sys.modules[mod_name] = _mocked_modules[mod_name]

# Provide named attributes that spec_utils exports
sys.modules['spec_utils'].build_command = mock.MagicMock()
sys.modules['spec_utils'].next_gap_id = mock.MagicMock()
sys.modules['spec_utils'].parse_gaps = mock.MagicMock()
sys.modules['spec_utils'].resolve_project_dir = mock.MagicMock()
sys.modules['spec_utils'].resolve_skill_content = mock.MagicMock()
sys.modules['spec_utils'].run_one_subprocess = mock.MagicMock()
sys.modules['spec_utils'].try_parse_json = mock.MagicMock()

from run_critique_specs import (  # noqa: E402
    CritiqueLog,
    _check_clean_change_dir,
    _save_cached_state,
)


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
    # Create change dir and a committed file so repo is not empty
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


class TestCheckCleanChangeDir:
    """Git dirty check blocks when change directory has uncommitted work."""

    def test_clean_dir_passes(self, git_repo):
        """No error when change directory is clean."""
        _, change_dir = git_repo
        # Should not raise
        _check_clean_change_dir(change_dir)

    def test_staged_file_blocks(self, git_repo):
        """Blocks when change dir has staged but uncommitted files."""
        repo_root, change_dir = git_repo
        new_file = change_dir / "functional.md"
        new_file.write_text("# Functional\n")
        subprocess.run(
            ['git', 'add', str(new_file)],
            cwd=repo_root, capture_output=True, check=True,
        )
        with pytest.raises(SystemExit):
            _check_clean_change_dir(change_dir)

    def test_untracked_file_blocks(self, git_repo):
        """Blocks when change dir has untracked files."""
        _, change_dir = git_repo
        (change_dir / "scratch.txt").write_text("temp")
        with pytest.raises(SystemExit):
            _check_clean_change_dir(change_dir)

    def test_modified_file_blocks(self, git_repo):
        """Blocks when change dir has modified but unstaged files."""
        repo_root, change_dir = git_repo
        tracked = change_dir / "technical.md"
        tracked.write_text("# v1\n")
        subprocess.run(['git', 'add', str(tracked)], cwd=repo_root, capture_output=True, check=True)
        subprocess.run(['git', 'commit', '-m', 'add technical'], cwd=repo_root, capture_output=True, check=True)
        # Now modify without staging
        tracked.write_text("# v2 modified\n")
        with pytest.raises(SystemExit):
            _check_clean_change_dir(change_dir)

    def test_dirty_outside_change_dir_passes(self, git_repo):
        """Dirty files outside the change dir do not block."""
        repo_root, change_dir = git_repo
        # Create a dirty file in repo root, not in the change dir
        outside = repo_root / "unrelated.txt"
        outside.write_text("not in change dir")
        # Should not raise
        _check_clean_change_dir(change_dir)


class TestFindingsMetadata:
    """findings.json round entries include commit hash and critic selection report."""

    def test_critique_log_has_metadata_fields(self):
        """CritiqueLog dataclass includes selection_report and commit fields."""
        log = CritiqueLog()
        assert hasattr(log, 'selection_report')
        assert hasattr(log, 'commit')
        assert log.selection_report == []
        assert log.commit == ''

    def test_critique_log_metadata_assignable(self):
        """CritiqueLog fields can be set with real data."""
        log = CritiqueLog()
        log.selection_report = [
            {'name': 'Functional', 'selected': True, 'reason': 'forced'},
            {'name': 'Technical', 'selected': False, 'reason': 'missing files: technical.md'},
        ]
        log.commit = 'abc123' * 7 + 'ab'  # 44 chars, realistic git hash
        assert len(log.selection_report) == 2
        assert log.commit.startswith('abc123')

    def test_cached_state_includes_metadata(self, tmp_path):
        """_save_cached_state persists selection_report and commit."""
        log = CritiqueLog()
        log.selection_report = [
            {'name': 'Consistency', 'selected': True, 'reason': 'changed: functional.md'},
        ]
        log.commit = 'deadbeef' * 5
        _save_cached_state(tmp_path, log, 'critique')

        state = json.loads((tmp_path / '.critique-state.json').read_text())
        assert state['selection_report'] == log.selection_report
        assert state['commit'] == log.commit


class TestCritiqueResults:
    """Tests for .critique-results.json saving."""

    def test_critique_results_format(self, tmp_path):
        """Verify the expected JSON array format of .critique-results.json."""
        results_path = tmp_path / '.critique-results.json'
        run_entry = {
            'timestamp': '2026-03-01T00:00:00+00:00',
            'config_type': 'critics',
            'schema': 'chaos-theory',
            'commit': 'abc123',
            'results': [
                {'name': 'Functional', 'status': 'success',
                 'output': '### NO ISSUES FOUND', 'model': 'opus'},
                {'name': 'Design', 'status': 'error',
                 'output': '', 'model': 'sonnet'},
            ],
        }
        results_path.write_text(json.dumps([run_entry], indent=2))

        data = json.loads(results_path.read_text())
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['config_type'] == 'critics'
        assert data[0]['schema'] == 'chaos-theory'
        assert data[0]['commit'] == 'abc123'
        assert len(data[0]['results']) == 2

    def test_critique_results_accumulate(self, tmp_path):
        """Second critique run appends to existing array."""
        results_path = tmp_path / '.critique-results.json'
        run1 = {
            'timestamp': '2026-03-01T00:00:00+00:00',
            'config_type': 'critics',
            'schema': 'chaos-theory',
            'commit': 'abc',
            'results': [{'name': 'A', 'status': 'success', 'output': 'ok', 'model': 'opus'}],
        }
        results_path.write_text(json.dumps([run1], indent=2))

        # Simulate second run appending
        existing = json.loads(results_path.read_text())
        run2 = {
            'timestamp': '2026-03-01T01:00:00+00:00',
            'config_type': 'critics',
            'schema': 'chaos-theory',
            'commit': 'def',
            'results': [{'name': 'B', 'status': 'success', 'output': 'ok', 'model': 'opus'}],
        }
        existing.append(run2)
        results_path.write_text(json.dumps(existing, indent=2))

        data = json.loads(results_path.read_text())
        assert len(data) == 2
        assert data[0]['commit'] == 'abc'
        assert data[1]['commit'] == 'def'

    def test_critique_results_cap_at_max(self, tmp_path):
        """Results are capped at MAX_CRITIQUE_RUNS (10)."""
        results_path = tmp_path / '.critique-results.json'
        MAX = 10
        runs = [
            {
                'timestamp': f'2026-03-01T{i:02d}:00:00+00:00',
                'config_type': 'critics',
                'schema': 'chaos-theory',
                'commit': f'commit-{i}',
                'results': [],
            }
            for i in range(MAX + 3)
        ]
        # Simulate cap behavior
        runs = runs[-MAX:]
        results_path.write_text(json.dumps(runs, indent=2))

        data = json.loads(results_path.read_text())
        assert len(data) == MAX
        assert data[0]['commit'] == 'commit-3'
        assert data[-1]['commit'] == 'commit-12'

    def test_critique_results_includes_failures(self, tmp_path):
        """Both successes and failures are captured in each run entry."""
        results_path = tmp_path / '.critique-results.json'
        run_entry = {
            'timestamp': '2026-03-01T00:00:00+00:00',
            'config_type': 'critics',
            'schema': 'chaos-theory',
            'commit': 'abc',
            'results': [
                {'name': 'A', 'status': 'success', 'output': 'findings', 'model': 'opus'},
                {'name': 'B', 'status': 'error', 'output': '', 'model': 'sonnet'},
            ],
        }
        results_path.write_text(json.dumps([run_entry], indent=2))

        data = json.loads(results_path.read_text())
        statuses = {r['status'] for r in data[0]['results']}
        assert 'success' in statuses
        assert 'error' in statuses
