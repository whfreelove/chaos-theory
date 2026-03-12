"""Tests for tools/migrate_evaluate_to_skillbooks.py."""

import json
import sys
from pathlib import Path

import pytest

TOOLS_DIR = str(Path(__file__).resolve().parents[2] / "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import importlib.util
spec = importlib.util.spec_from_file_location(
    "migrate_evaluate_to_skillbooks",
    Path(TOOLS_DIR) / "migrate_evaluate_to_skillbooks.py",
)
migrate_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migrate_mod)


class TestMigrationHelpers:

    def test_slugify(self):
        assert migrate_mod.slugify("Requirements Coverage") == "requirements-coverage"
        assert migrate_mod.slugify("Functional") == "functional"
        assert migrate_mod.slugify("Design for Test") == "design-for-test"

    def test_make_skillbook_structure(self):
        sb = migrate_mod.make_skillbook(
            "Evaluate for leakage.",
            "Functional",
            "critics.chaos-theory.json",
        )
        assert 'skills' in sb
        assert 'metadata' in sb
        assert 'sections' in sb
        assert 'next_id' in sb
        assert isinstance(sb['skills'], dict)
        assert len(sb['skills']) == 1

        skill = sb['skills']['eval-criteria-1']
        assert skill['id'] == 'eval-criteria-1'
        assert skill['section'] == 'evaluation-criteria'
        assert skill['content'] == 'Evaluate for leakage.'
        assert skill['helpful'] == 0
        assert skill['status'] == 'active'
        assert skill['sources'] == []
        assert sb['metadata']['source'] == 'migrated from critics.chaos-theory.json'
        assert sb['metadata']['critic'] == 'Functional'
        assert sb['sections'] == {'evaluation-criteria': ['eval-criteria-1']}

    def test_make_skillbook_valid_json(self):
        """Skillbook JSON can be serialized and deserialized."""
        sb = migrate_mod.make_skillbook("content", "Test", "config.json")
        serialized = json.dumps(sb)
        deserialized = json.loads(serialized)
        assert deserialized['skills']['eval-criteria-1']['content'] == 'content'


class TestMigrationIntegration:
    """Verify the actual migrated skillbook files exist and are valid."""

    PLUGIN_ROOT = Path(__file__).resolve().parents[2] / 'plugins' / 'tokamak'

    def test_skillbook_files_exist(self):
        """At least one skillbook file exists per schema."""
        ace_dir = self.PLUGIN_ROOT / '.ace' / 'critics' / 'chaos-theory'
        assert ace_dir.exists(), f"Expected {ace_dir} to exist"
        files = list(ace_dir.glob('*.json'))
        assert len(files) > 0

    def test_all_skillbooks_valid_json(self):
        """Every skillbook file is valid JSON with expected structure."""
        ace_dir = self.PLUGIN_ROOT / '.ace'
        for sb_file in ace_dir.rglob('*.json'):
            with open(sb_file) as f:
                data = json.load(f)
            assert 'skills' in data, f"{sb_file} missing 'skills'"
            assert 'metadata' in data, f"{sb_file} missing 'metadata'"
            assert isinstance(data['skills'], dict), f"{sb_file} skills should be dict"
            for sid, skill in data['skills'].items():
                assert 'id' in skill, f"{sb_file} skill missing 'id'"
                assert 'content' in skill, f"{sb_file} skill missing 'content'"
                assert skill['id'] == sid, f"{sb_file} skill id mismatch"

    def test_configs_have_no_evaluate(self):
        """Config JSONs no longer contain 'evaluate' key after migration."""
        for pattern in ('critics.*.json', 'gap-detectors.*.json'):
            for config_file in self.PLUGIN_ROOT.glob(pattern):
                with open(config_file) as f:
                    config = json.load(f)
                for critic in config.get('critics', []):
                    assert 'evaluate' not in critic, (
                        f"{config_file.name}: critic '{critic.get('name')}' "
                        f"still has 'evaluate'"
                    )

    def test_team_skillbook_exists(self):
        """Team skillbook exists with populated skills."""
        team_path = self.PLUGIN_ROOT / '.ace' / 'team' / 'critique.json'
        assert team_path.exists()
        with open(team_path) as f:
            data = json.load(f)
        assert isinstance(data['skills'], dict)
        assert len(data['skills']) > 0

    def test_skillbook_content_nonempty(self):
        """Migrated skillbooks have non-empty content."""
        sb_path = self.PLUGIN_ROOT / '.ace' / 'critics' / 'chaos-theory' / 'functional.json'
        with open(sb_path) as f:
            data = json.load(f)
        assert len(data['skills']) > 0
        first_skill = list(data['skills'].values())[0]
        assert len(first_skill['content']) > 10
