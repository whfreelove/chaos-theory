"""Tests for run_critique_specs.py helper functions."""

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

from run_critique_specs import _check_clean_change_dir  # noqa: E402


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
