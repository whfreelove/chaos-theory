"""Tests for run_critics.py parallel critic orchestrator."""

import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Import module under test
import sys
sys_path_script = Path(__file__).resolve().parents[3] / "plugins" / "tokamak" / "scripts"
if str(sys_path_script) not in sys.path:
    sys.path.insert(0, str(sys_path_script))
import importlib.util
spec = importlib.util.spec_from_file_location(
    "run_critics", sys_path_script / "run_critics.py"
)
run_critics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_critics)


# --- Fixtures ---

@pytest.fixture
def change_dir(tmp_path):
    """Change directory placed 3 levels deep so openspec_root resolves to tmp_path/openspec."""
    d = tmp_path / "openspec" / "changes" / "test-change"
    d.mkdir(parents=True)
    (d / "gaps.md").write_text("# Gaps\n")
    (d / "resolved.md").write_text("# Resolved\n")
    return d


@pytest.fixture
def project_dir(tmp_path):
    """Project directory matching 'project: my-project' (resolved under openspec/)."""
    d = tmp_path / "openspec" / "my-project"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def standard_critic():
    return {
        'name': 'Functional',
        'model': 'opus',
        'files': ['functional.md'],
        'project_files': [],
        'skills': ['tokamak:writing-functional-specs'],
    }


@pytest.fixture
def accuracy_critic():
    return {
        'name': 'Capability Accuracy',
        'model': 'opus',
        'files': ['functional.md'],
        'project_files': [],
        'skills': [],
    }


@pytest.fixture
def consistency_critic():
    return {
        'name': 'Functional Consistency',
        'model': 'opus',
        'files': ['functional.md'],
        'project_files': ['functional.md'],
        'skills': [],
    }


@pytest.fixture
def critics_data(standard_critic, accuracy_critic):
    return {
        'output_template': '## CRITIC OUTPUT FORMAT\nFor each issue...',
        'critics': [standard_critic, accuracy_critic],
        'schema': 'chaos-theory',
    }


# --- Accuracy critic detection ---

class TestAccuracyCriticDetection:

    @pytest.mark.parametrize("name", [
        "Capability Accuracy",
        "Requirement Accuracy",
        "Architecture Accuracy",
        "Decision Plausibility",
        "Infrastructure Accuracy",
    ])
    def test_accuracy_critics_detected(self, name):
        assert run_critics.is_accuracy_critic(name) is True

    @pytest.mark.parametrize("name", [
        "Functional",
        "Design",
        "Technical",
        "Requirements",
        "Functional Consistency",
    ])
    def test_non_accuracy_critics(self, name):
        assert run_critics.is_accuracy_critic(name) is False


# --- Skillbook loading ---

class TestLoadSkillbook:

    def test_load_skillbook_valid(self, tmp_path):
        sb_path = tmp_path / "test.json"
        sb_path.write_text(json.dumps({
            'skills': {
                'eval-1': {'id': 'eval-1', 'section': 'evaluation-criteria',
                           'content': 'Check for leakage.'},
                'eval-2': {'id': 'eval-2', 'section': 'evaluation-criteria',
                           'content': 'Check for consistency.'},
            },
            'sections': {'evaluation-criteria': ['eval-1', 'eval-2']},
            'next_id': 2,
            'metadata': {'version': '0.1.0'},
        }))
        result = run_critics._load_skillbook(sb_path)
        assert 'Check for leakage.' in result
        assert 'Check for consistency.' in result

    def test_load_skillbook_missing(self, tmp_path):
        sb_path = tmp_path / "nonexistent.json"
        result = run_critics._load_skillbook(sb_path)
        assert result == ''

    def test_load_skillbook_empty_skills(self, tmp_path):
        for empty in ([], {}):
            sb_path = tmp_path / "empty.json"
            sb_path.write_text(json.dumps({
                'skills': empty, 'metadata': {'version': '0.1.0'},
            }))
            result = run_critics._load_skillbook(sb_path)
            assert result == ''

    def test_load_skillbook_corrupt_json(self, tmp_path):
        sb_path = tmp_path / "corrupt.json"
        sb_path.write_text("{invalid json")
        result = run_critics._load_skillbook(sb_path)
        assert result == ''

    def test_load_skillbook_legacy_list_format(self, tmp_path):
        sb_path = tmp_path / "legacy.json"
        sb_path.write_text(json.dumps({
            'skills': [{'id': 'eval-1', 'content': 'Check for leakage.'}],
            'metadata': {'version': '0.1.0'},
        }))
        result = run_critics._load_skillbook(sb_path)
        assert 'Check for leakage.' in result


# --- Prompt construction ---

class TestBuildPrompt:

    def test_includes_skillbook_context(self, standard_critic, change_dir):
        prompt = run_critics.build_prompt(
            standard_critic, change_dir, None,
            skillbook_context='Evaluate functional.md for implementation leakage.',
        )
        assert "## Evaluation Criteria" in prompt
        assert "implementation leakage" in prompt

    def test_includes_team_context(self, standard_critic, change_dir):
        prompt = run_critics.build_prompt(
            standard_critic, change_dir, None,
            skillbook_context='Check quality.',
            team_context='Avoid duplicating findings across critics.',
        )
        assert "## Team Coordination Guidance" in prompt
        assert "Avoid duplicating" in prompt

    def test_no_team_section_when_empty(self, standard_critic, change_dir):
        prompt = run_critics.build_prompt(
            standard_critic, change_dir, None,
            skillbook_context='Check quality.',
        )
        assert "Team Coordination Guidance" not in prompt

    def test_empty_skillbook_produces_valid_prompt(self, standard_critic, change_dir):
        prompt = run_critics.build_prompt(
            standard_critic, change_dir, None,
            skillbook_context='',
        )
        assert "## Evaluation Criteria" in prompt
        assert "## Files to evaluate" in prompt

    def test_file_purpose_sentinel(self, standard_critic, change_dir):
        """FILE PURPOSE in skillbook_context triggers schema artifacts (no KeyError)."""
        prompt = run_critics.build_prompt(
            standard_critic, change_dir, None,
            skillbook_context='Use the FILE PURPOSE INSTRUCTIONS provided above.',
        )
        assert "## Evaluation Criteria" in prompt
        assert "FILE PURPOSE" in prompt

    def test_includes_file_paths(self, standard_critic, change_dir):
        prompt = run_critics.build_prompt(
            standard_critic, change_dir, None,
            skillbook_context='Check quality.',
        )
        assert f"`{change_dir}/functional.md`" in prompt

    def test_includes_gaps_paths(self, standard_critic, change_dir):
        prompt = run_critics.build_prompt(
            standard_critic, change_dir, None,
            skillbook_context='Check quality.',
        )
        assert f"`{change_dir}/gaps.md`" in prompt
        assert f"`{change_dir}/resolved.md`" in prompt
        assert "do not duplicate" in prompt.lower()

    def test_no_project_section_when_no_project_files(self, standard_critic, change_dir):
        prompt = run_critics.build_prompt(
            standard_critic, change_dir, None,
            skillbook_context='Check quality.',
        )
        assert "Project Reference Files" not in prompt

    def test_includes_project_section(self, consistency_critic, change_dir, project_dir):
        prompt = run_critics.build_prompt(
            consistency_critic, change_dir, project_dir,
            skillbook_context='Check quality.',
        )
        assert "## Project Reference Files" in prompt
        assert "living project documentation" in prompt
        assert f"`{project_dir}/functional.md`" in prompt

    def test_no_project_section_when_project_dir_none(self, consistency_critic, change_dir):
        prompt = run_critics.build_prompt(
            consistency_critic, change_dir, None,
            skillbook_context='Check quality.',
        )
        assert "Project Reference Files" not in prompt

    def test_accuracy_critic_gets_exploration_section(self, accuracy_critic, change_dir):
        prompt = run_critics.build_prompt(
            accuracy_critic, change_dir, None,
            skillbook_context='Check quality.',
        )
        assert "## Codebase Exploration" in prompt
        assert "Read, Glob, and Grep" in prompt
        project_root = change_dir.parent.parent.parent
        assert str(project_root) in prompt

    def test_standard_critic_no_exploration_section(self, standard_critic, change_dir):
        prompt = run_critics.build_prompt(
            standard_critic, change_dir, None,
            skillbook_context='Check quality.',
        )
        assert "Codebase Exploration" not in prompt

    def test_templates_not_in_prompt(self, standard_critic, change_dir):
        """Templates are metadata only — no longer injected into prompts."""
        standard_critic['templates'] = {
            'functional.md': '<!-- Template instructions for functional -->'
        }
        prompt = run_critics.build_prompt(
            standard_critic, change_dir, None,
            skillbook_context='Check quality.',
        )
        assert "Schema Template Instructions" not in prompt
        assert "<!-- Template instructions for functional -->" not in prompt

    def test_artifact_guidance_loaded(self, standard_critic, change_dir):
        """Artifact skillbooks inject shared evaluation guidance by file type."""
        prompt = run_critics.build_prompt(
            standard_critic, change_dir, None,
            skillbook_context='Check quality.',
        )
        assert "## Artifact Guidance: functional" in prompt

    def test_artifact_guidance_deduplicates(self, standard_critic, change_dir):
        """Multiple files mapping to the same stem produce one guidance section."""
        standard_critic['files'] = ['functional.md', 'functional.md']
        prompt = run_critics.build_prompt(
            standard_critic, change_dir, None,
            skillbook_context='Check quality.',
        )
        count = prompt.count("## Artifact Guidance: functional")
        assert count == 1

    def test_missing_artifact_skillbook_skipped(self, standard_critic, change_dir):
        """Files without artifact skillbooks are silently skipped."""
        standard_critic['files'] = ['tasks.yaml']
        prompt = run_critics.build_prompt(
            standard_critic, change_dir, None,
            skillbook_context='Check quality.',
        )
        assert "## Artifact Guidance: tasks" not in prompt


# --- Command construction ---

class TestBuildCommand:

    @patch('shutil.which', return_value='/usr/local/bin/claude')
    def test_standard_critic_tools(self, mock_which, standard_critic, change_dir):
        cmd = run_critics.build_command(
            standard_critic, change_dir, None, '', None
        )
        # Find --tools flag and its value
        tools_idx = cmd.index('--tools')
        assert cmd[tools_idx + 1] == 'Read'

    @patch('shutil.which', return_value='/usr/local/bin/claude')
    def test_accuracy_critic_tools(self, mock_which, accuracy_critic, change_dir):
        cmd = run_critics.build_command(
            accuracy_critic, change_dir, None, '', None
        )
        tools_idx = cmd.index('--tools')
        assert cmd[tools_idx + 1] == 'Read,Glob,Grep'

    @patch('shutil.which', return_value='/usr/local/bin/claude')
    def test_model_passed(self, mock_which, standard_critic, change_dir):
        cmd = run_critics.build_command(
            standard_critic, change_dir, None, '', None
        )
        model_idx = cmd.index('--model')
        assert cmd[model_idx + 1] == 'opus'

    @patch('shutil.which', return_value='/usr/local/bin/claude')
    def test_permission_mode(self, mock_which, standard_critic, change_dir):
        cmd = run_critics.build_command(
            standard_critic, change_dir, None, '', None
        )
        assert '--permission-mode' in cmd
        pm_idx = cmd.index('--permission-mode')
        assert cmd[pm_idx + 1] == 'bypassPermissions'

    @patch('shutil.which', return_value='/usr/local/bin/claude')
    def test_no_session_persistence(self, mock_which, standard_critic, change_dir):
        cmd = run_critics.build_command(
            standard_critic, change_dir, None, '', None
        )
        assert '--no-session-persistence' in cmd

    @patch('shutil.which', return_value='/usr/local/bin/claude')
    def test_add_dir_change(self, mock_which, standard_critic, change_dir):
        cmd = run_critics.build_command(
            standard_critic, change_dir, None, '', None
        )
        add_dir_indices = [i for i, v in enumerate(cmd) if v == '--add-dir']
        dirs = [cmd[i + 1] for i in add_dir_indices]
        assert str(change_dir) in dirs

    @patch('shutil.which', return_value='/usr/local/bin/claude')
    def test_add_dir_project(self, mock_which, standard_critic, change_dir, project_dir):
        cmd = run_critics.build_command(
            standard_critic, change_dir, project_dir, '', None
        )
        add_dir_indices = [i for i, v in enumerate(cmd) if v == '--add-dir']
        dirs = [cmd[i + 1] for i in add_dir_indices]
        assert str(project_dir) in dirs

    @patch('shutil.which', return_value='/usr/local/bin/claude')
    def test_accuracy_critic_add_dir_project_root(self, mock_which, accuracy_critic, change_dir):
        cmd = run_critics.build_command(
            accuracy_critic, change_dir, None, '', None
        )
        add_dir_indices = [i for i, v in enumerate(cmd) if v == '--add-dir']
        dirs = [cmd[i + 1] for i in add_dir_indices]
        project_root = str(change_dir.parent.parent.parent)
        assert project_root in dirs

    @patch('shutil.which', return_value='/usr/local/bin/claude')
    def test_output_template_appended(self, mock_which, standard_critic, change_dir):
        template = "## OUTPUT FORMAT\nFor each issue..."
        cmd = run_critics.build_command(
            standard_critic, change_dir, None, template, None
        )
        assert '--append-system-prompt' in cmd
        sp_idx = cmd.index('--append-system-prompt')
        assert cmd[sp_idx + 1] == template

    @patch('shutil.which', return_value='/usr/local/bin/claude')
    def test_no_template_no_flag(self, mock_which, standard_critic, change_dir):
        cmd = run_critics.build_command(
            standard_critic, change_dir, None, '', None
        )
        assert '--append-system-prompt' not in cmd

    @patch('shutil.which', return_value='/usr/local/bin/claude')
    def test_budget_passed(self, mock_which, standard_critic, change_dir):
        cmd = run_critics.build_command(
            standard_critic, change_dir, None, '', 0.50
        )
        assert '--max-budget-usd' in cmd
        b_idx = cmd.index('--max-budget-usd')
        assert cmd[b_idx + 1] == '0.5'

    @patch('shutil.which', return_value='/usr/local/bin/claude')
    def test_no_budget_no_flag(self, mock_which, standard_critic, change_dir):
        cmd = run_critics.build_command(
            standard_critic, change_dir, None, '', None
        )
        assert '--max-budget-usd' not in cmd


# --- Argument parsing ---

class TestParseArgs:

    def test_defaults(self, tmp_path):
        args = run_critics.parse_args([str(tmp_path)])
        assert args.max_concurrent == 6
        assert args.timeout == 600
        assert args.dry_run is False
        assert args.budget is None

    def test_overrides(self, tmp_path):
        args = run_critics.parse_args([
            str(tmp_path),
            '--max-concurrent', '10',
            '--timeout', '600',
            '--dry-run',
            '--budget', '0.25',
        ])
        assert args.max_concurrent == 10
        assert args.timeout == 600
        assert args.dry_run is True
        assert args.budget == 0.25


# --- Result aggregation ---

class TestResultAggregation:

    @pytest.mark.asyncio
    async def test_empty_critics(self):
        result = await run_critics.run_all_critics(
            {'output_template': '', 'critics': []},
            Path('/tmp/fake'), None, 5, 300, None, False,
        )
        assert result['critics_run'] == 0
        assert result['critics_succeeded'] == 0
        assert result['critics_failed'] == 0
        assert result['results'] == []

    @pytest.mark.asyncio
    async def test_dry_run_returns_empty(self, standard_critic, change_dir):
        result = await run_critics.run_all_critics(
            {'output_template': '', 'critics': [standard_critic],
             'schema': 'chaos-theory'},
            change_dir, None, 5, 300, None, dry_run=True,
        )
        assert result.get('dry_run') is True
        assert result['critics_run'] == 0


# --- Project dir resolution ---

class TestResolveProjectDir:

    def test_no_openspec_yaml(self, change_dir):
        assert run_critics.resolve_project_dir(change_dir) is None

    def test_no_project_field(self, change_dir):
        (change_dir / '.openspec.yaml').write_text("schema: chaos-theory\n")
        assert run_critics.resolve_project_dir(change_dir) is None

    def test_project_dir_exists(self, change_dir, project_dir):
        (change_dir / '.openspec.yaml').write_text(
            "schema: chaos-theory\nproject: my-project\n"
        )
        result = run_critics.resolve_project_dir(change_dir)
        assert result == project_dir

    def test_project_dir_missing(self, change_dir):
        (change_dir / '.openspec.yaml').write_text(
            "schema: chaos-theory\nproject: nonexistent\n"
        )
        assert run_critics.resolve_project_dir(change_dir) is None


# --- CLAUDECODE env removal ---

class TestEnvBypass:
    """Verify CLAUDECODE is removed from subprocess environment."""

    @pytest.mark.asyncio
    @patch('shutil.which', return_value='/usr/local/bin/claude')
    async def test_claudecode_removed(self, mock_which, standard_critic, change_dir):
        """The run_one_critic function should strip CLAUDECODE from env."""
        import asyncio
        captured_env = {}

        async def fake_create_subprocess_exec(*args, **kwargs):
            captured_env.update(kwargs.get('env', {}))
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(
                return_value=(b'### NO ISSUES FOUND', b'')
            )
            mock_proc.returncode = 0
            mock_proc.kill = AsyncMock()
            mock_proc.wait = AsyncMock()
            return mock_proc

        cmd = run_critics.build_command(
            standard_critic, change_dir, None, '', None
        )

        with patch.dict(os.environ, {'CLAUDECODE': '1', 'HOME': '/tmp'}):
            with patch('asyncio.create_subprocess_exec', fake_create_subprocess_exec):
                semaphore = asyncio.Semaphore(5)
                result = await run_critics.run_one_critic(
                    standard_critic, cmd, 'test prompt', 300, semaphore,
                )

        assert 'CLAUDECODE' not in captured_env
        assert result['status'] == 'success'
