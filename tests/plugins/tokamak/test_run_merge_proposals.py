"""Tests for run_merge_proposals.py merge proposal generator."""

import json
from pathlib import Path

import pytest

# Import module under test
import sys
sys_path_script = Path(__file__).resolve().parents[3] / "plugins" / "tokamak" / "scripts"
if str(sys_path_script) not in sys.path:
    sys.path.insert(0, str(sys_path_script))
import importlib.util
spec = importlib.util.spec_from_file_location(
    "run_merge_proposals", sys_path_script / "run_merge_proposals.py"
)
run_merge_proposals = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_merge_proposals)


# --- Fixtures ---

@pytest.fixture
def plugin_root(tmp_path):
    """Create a fake plugin root with merge-rules configs."""
    root = tmp_path / "plugin"
    root.mkdir()
    scripts = root / "scripts"
    scripts.mkdir()
    return root


@pytest.fixture
def change_dir(tmp_path):
    """Change directory placed 3 levels deep so openspec_root resolves."""
    d = tmp_path / "openspec" / "changes" / "test-change"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def project_dir(tmp_path):
    """Project directory matching 'project: my-project'."""
    d = tmp_path / "openspec" / "my-project"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def chaos_theory_config():
    """Standard chaos-theory merge-rules config."""
    return {
        "version": 1,
        "artifacts": [
            {
                "name": "functional",
                "change_source": "functional.md",
                "project_target": "functional.md",
                "rules": "Append capabilities, merge scope.",
            },
            {
                "name": "requirements",
                "change_source": "requirements",
                "project_target": "requirements",
                "rules": "ADDED/MODIFIED/REMOVED scenarios.",
            },
            {
                "name": "technical",
                "change_source": "technical.md",
                "project_target": "technical.md",
                "rules": "Merge components, interfaces, decisions.",
            },
        ],
    }


# --- _has_substantive_content ---

class TestHasSubstantiveContent:

    def test_missing_file(self, tmp_path):
        assert run_merge_proposals._has_substantive_content(
            tmp_path / "nonexistent.md", "functional"
        ) is False

    def test_empty_file(self, tmp_path):
        f = tmp_path / "functional.md"
        f.write_text("")
        assert run_merge_proposals._has_substantive_content(f, "functional") is False

    def test_yaml_stub_name_only(self, tmp_path):
        f = tmp_path / "functional.yaml"
        f.write_text("functional:")
        assert run_merge_proposals._has_substantive_content(f, "functional") is False

    def test_yaml_stub_empty_dict(self, tmp_path):
        f = tmp_path / "functional.yaml"
        f.write_text("functional: {}")
        assert run_merge_proposals._has_substantive_content(f, "functional") is False

    def test_yaml_stub_extra_whitespace(self, tmp_path):
        """M-2 fix: whitespace-tolerant stub detection."""
        f = tmp_path / "functional.yaml"
        f.write_text("functional:  {}")
        assert run_merge_proposals._has_substantive_content(f, "functional") is False

    def test_non_yaml_empty_content(self, tmp_path):
        f = tmp_path / "functional.md"
        f.write_text("   \n  \n  ")
        assert run_merge_proposals._has_substantive_content(f, "functional") is False

    def test_substantive_yaml(self, tmp_path):
        f = tmp_path / "functional.yaml"
        f.write_text("functional:\n  capabilities:\n    - CAP-1: Do things")
        assert run_merge_proposals._has_substantive_content(f, "functional") is True

    def test_substantive_md(self, tmp_path):
        f = tmp_path / "functional.md"
        f.write_text("# Functional\n\nThis system does X.")
        assert run_merge_proposals._has_substantive_content(f, "functional") is True

    def test_empty_directory(self, tmp_path):
        d = tmp_path / "requirements"
        d.mkdir()
        assert run_merge_proposals._has_substantive_content(d, "requirements") is False

    def test_non_empty_directory(self, tmp_path):
        d = tmp_path / "requirements"
        d.mkdir()
        (d / "auth.feature.md").write_text("# Auth requirements")
        assert run_merge_proposals._has_substantive_content(d, "requirements") is True


# --- load_merge_config ---

class TestLoadMergeConfig:

    def test_schema_with_matching_config(self, change_dir, tmp_path, monkeypatch):
        """Schema-specific config is loaded when it exists."""
        (change_dir / '.openspec.yaml').write_text("schema: chaos-theory-lite\n")

        plugin_root = tmp_path / "plugin"
        plugin_root.mkdir()
        scripts_dir = plugin_root / "scripts"
        scripts_dir.mkdir()

        config_data = {"version": 1, "artifacts": [{"name": "test"}]}
        (plugin_root / "merge-rules.chaos-theory-lite.json").write_text(
            json.dumps(config_data)
        )

        monkeypatch.setattr(
            run_merge_proposals, "__file__",
            str(scripts_dir / "run_merge_proposals.py"),
        )
        result = run_merge_proposals.load_merge_config(change_dir)
        assert result == config_data

    def test_unknown_schema_falls_back(self, change_dir, tmp_path, monkeypatch):
        """Unknown schema falls back to chaos-theory default."""
        (change_dir / '.openspec.yaml').write_text("schema: unknown-schema\n")

        plugin_root = tmp_path / "plugin"
        plugin_root.mkdir()
        scripts_dir = plugin_root / "scripts"
        scripts_dir.mkdir()

        fallback_data = {"version": 1, "artifacts": [{"name": "fallback"}]}
        (plugin_root / "merge-rules.chaos-theory.json").write_text(
            json.dumps(fallback_data)
        )

        monkeypatch.setattr(
            run_merge_proposals, "__file__",
            str(scripts_dir / "run_merge_proposals.py"),
        )
        result = run_merge_proposals.load_merge_config(change_dir)
        assert result == fallback_data

    def test_no_openspec_yaml_falls_back(self, change_dir, tmp_path, monkeypatch):
        """No .openspec.yaml falls back to chaos-theory default."""
        plugin_root = tmp_path / "plugin"
        plugin_root.mkdir()
        scripts_dir = plugin_root / "scripts"
        scripts_dir.mkdir()

        fallback_data = {"version": 1, "artifacts": [{"name": "default"}]}
        (plugin_root / "merge-rules.chaos-theory.json").write_text(
            json.dumps(fallback_data)
        )

        monkeypatch.setattr(
            run_merge_proposals, "__file__",
            str(scripts_dir / "run_merge_proposals.py"),
        )
        result = run_merge_proposals.load_merge_config(change_dir)
        assert result == fallback_data

    def test_no_config_files_raises(self, change_dir, tmp_path, monkeypatch):
        """I-4 fix: raises FileNotFoundError instead of sys.exit."""
        (change_dir / '.openspec.yaml').write_text("schema: missing\n")

        plugin_root = tmp_path / "plugin"
        plugin_root.mkdir()
        scripts_dir = plugin_root / "scripts"
        scripts_dir.mkdir()

        monkeypatch.setattr(
            run_merge_proposals, "__file__",
            str(scripts_dir / "run_merge_proposals.py"),
        )
        with pytest.raises(FileNotFoundError, match="No merge-rules config found"):
            run_merge_proposals.load_merge_config(change_dir)


# --- resolve_artifact_pairs ---

class TestResolveArtifactPairs:

    def test_all_artifacts_with_content(self, change_dir, project_dir, chaos_theory_config):
        """All artifacts present with content → returns all."""
        (change_dir / "functional.md").write_text("# Functional\nContent here.")
        reqs = change_dir / "requirements"
        reqs.mkdir()
        (reqs / "auth.feature.md").write_text("# Auth")
        (change_dir / "technical.md").write_text("# Technical\nContent here.")

        pairs = run_merge_proposals.resolve_artifact_pairs(
            change_dir, project_dir, chaos_theory_config
        )
        assert len(pairs) == 3
        names = [p['name'] for p in pairs]
        assert 'functional' in names
        assert 'requirements' in names
        assert 'technical' in names

    def test_missing_artifacts_skipped(self, change_dir, project_dir, chaos_theory_config):
        """Only existing artifacts with content are returned."""
        (change_dir / "functional.md").write_text("# Functional\nContent here.")
        # requirements and technical are missing

        pairs = run_merge_proposals.resolve_artifact_pairs(
            change_dir, project_dir, chaos_theory_config
        )
        assert len(pairs) == 1
        assert pairs[0]['name'] == 'functional'

    def test_yaml_stubs_skipped(self, change_dir, project_dir):
        """YAML stubs are not included in output."""
        config = {
            "artifacts": [
                {
                    "name": "functional",
                    "change_source": ".sections/functional.yaml",
                    "project_target": "functional.md",
                    "rules": "Merge rules.",
                },
            ],
        }
        sections = change_dir / ".sections"
        sections.mkdir()
        (sections / "functional.yaml").write_text("functional: {}")

        pairs = run_merge_proposals.resolve_artifact_pairs(
            change_dir, project_dir, config
        )
        assert len(pairs) == 0

    def test_pair_has_expected_keys(self, change_dir, project_dir, chaos_theory_config):
        """Each pair dict has name, change_file, project_file, rules keys."""
        (change_dir / "functional.md").write_text("# Functional\nContent here.")

        pairs = run_merge_proposals.resolve_artifact_pairs(
            change_dir, project_dir, chaos_theory_config
        )
        assert len(pairs) == 1
        pair = pairs[0]
        assert set(pair.keys()) == {'name', 'change_file', 'project_file', 'rules'}
        assert pair['name'] == 'functional'
        assert isinstance(pair['change_file'], Path)
        assert isinstance(pair['project_file'], Path)


# --- build_merge_prompt ---

class TestBuildMergePrompt:

    def test_rules_appear_in_output(self, change_dir, project_dir):
        pair = {
            'name': 'technical',
            'change_file': change_dir / 'technical.md',
            'project_file': project_dir / 'technical.md',
            'rules': 'Merge components, interfaces, decisions.',
        }
        (project_dir / 'technical.md').write_text("# Technical")

        prompt = run_merge_proposals.build_merge_prompt(
            pair, change_dir, project_dir, 'test-change'
        )
        assert 'Merge components, interfaces, decisions.' in prompt

    def test_directory_artifact_gets_read_all(self, change_dir, project_dir):
        """I-2 fix: artifacts without suffix get 'Read all files under' treatment."""
        reqs_dir = project_dir / 'requirements'
        reqs_dir.mkdir()

        pair = {
            'name': 'requirements',
            'change_file': change_dir / 'requirements',
            'project_file': reqs_dir,
            'rules': 'ADDED/MODIFIED rules.',
        }

        prompt = run_merge_proposals.build_merge_prompt(
            pair, change_dir, project_dir, 'test-change'
        )
        assert 'Read all files under' in prompt

    def test_no_suffix_nonexistent_gets_read_all(self, change_dir, project_dir):
        """I-2 fix: non-existent path without suffix also gets directory treatment."""
        pair = {
            'name': 'requirements',
            'change_file': change_dir / 'requirements',
            'project_file': project_dir / 'requirements',
            'rules': 'Rules.',
        }
        # project_dir/requirements does NOT exist

        prompt = run_merge_proposals.build_merge_prompt(
            pair, change_dir, project_dir, 'test-change'
        )
        assert 'Read all files under' in prompt

    def test_nonexistent_project_file_gets_first_merge(self, change_dir, project_dir):
        """Non-existent .md project file gets 'first merge' message."""
        pair = {
            'name': 'technical',
            'change_file': change_dir / 'technical.md',
            'project_file': project_dir / 'technical.md',
            'rules': 'Merge rules.',
        }
        # project_dir/technical.md does NOT exist

        prompt = run_merge_proposals.build_merge_prompt(
            pair, change_dir, project_dir, 'test-change'
        )
        assert 'first merge' in prompt
        assert 'does not exist yet' in prompt
