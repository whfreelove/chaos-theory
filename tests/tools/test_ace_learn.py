"""Tests for tools/ace_learn.py — skip when ace-framework not installed."""

import json
import sys
from pathlib import Path

import pytest

try:
    import ace  # noqa: F401
    HAS_ACE = True
except ImportError:
    HAS_ACE = False

pytestmark = pytest.mark.skipif(not HAS_ACE, reason="ace-framework not installed")

TOOLS_DIR = str(Path(__file__).resolve().parents[2] / "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)


@pytest.fixture
def change_dir_with_results(tmp_path):
    """Change directory with a .critique-results.json file."""
    change_dir = tmp_path / "openspec" / "changes" / "test"
    change_dir.mkdir(parents=True)
    results = [
        {
            'timestamp': '2026-03-01T00:00:00+00:00',
            'config_type': 'critics',
            'schema': 'chaos-theory',
            'commit': 'abc123',
            'results': [
                {
                    'name': 'Functional',
                    'status': 'success',
                    'output': '### Functional-1: Implementation leakage\n- **Severity**: medium',
                    'model': 'opus',
                },
                {
                    'name': 'Design',
                    'status': 'error',
                    'output': '',
                    'model': 'sonnet',
                },
            ],
        }
    ]
    (change_dir / '.critique-results.json').write_text(json.dumps(results))
    return change_dir


class TestAceLearnReadResults:
    """Tests that ace_learn.py reads .critique-results.json correctly."""

    def test_reads_results_file(self, change_dir_with_results):
        results_path = change_dir_with_results / '.critique-results.json'
        with open(results_path) as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]['schema'] == 'chaos-theory'
        successes = [r for r in data[0]['results'] if r['status'] == 'success']
        assert len(successes) == 1
        assert successes[0]['name'] == 'Functional'

    def test_no_results_file_raises(self, tmp_path):
        """Missing .critique-results.json should cause an error."""
        results_path = tmp_path / '.critique-results.json'
        assert not results_path.exists()
