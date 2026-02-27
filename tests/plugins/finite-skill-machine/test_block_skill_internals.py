"""Tests for the block-skill-internals PreToolUse hook."""

import json
import os
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[3] / "plugins" / "finite-skill-machine" / "scripts" / "block-skill-internals.sh"


def run_block_hook(tool_input: dict, env_overrides: dict | None = None) -> tuple[int, str, str]:
    """Execute block-skill-internals.sh with JSON stdin, return (exit_code, stdout, stderr)."""
    env = os.environ.copy()
    # Ensure FSM_BYPASS is not inherited from the test runner's environment
    env.pop("FSM_BYPASS", None)
    if env_overrides:
        for k, v in env_overrides.items():
            if v is None:
                env.pop(k, None)
            else:
                env[k] = v

    result = subprocess.run(
        ["bash", str(SCRIPT)],
        input=json.dumps(tool_input),
        capture_output=True,
        text=True,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


def assert_deny_structure(output: dict):
    """Verify deny JSON matches INT-deny-response structure."""
    assert "systemMessage" in output
    hso = output["hookSpecificOutput"]
    assert hso["hookEventName"] == "PreToolUse"
    assert hso["permissionDecision"] == "deny"
    assert "permissionDecisionReason" in hso


class TestBypassGuard:
    """REQ-env-var-bypass: FSM_BYPASS env var allows skill file access."""

    def test_bypass_active_read_skill_md(self):
        """SCN-bypass-active: FSM_BYPASS=1, Read SKILL.md — exits 0, empty stdout."""
        payload = {"tool_name": "Read", "tool_input": {"file_path": "/path/to/skills/SKILL.md"}}
        exit_code, stdout, _ = run_block_hook(payload, env_overrides={"FSM_BYPASS": "1"})

        assert exit_code == 0
        assert stdout.strip() == ""

    def test_bypass_active_glob(self):
        """SCN-bypass-active-glob: FSM_BYPASS=1, Glob **/SKILL.md — exits 0, empty stdout."""
        payload = {"tool_name": "Glob", "tool_input": {"pattern": "**/SKILL.md"}}
        exit_code, stdout, _ = run_block_hook(payload, env_overrides={"FSM_BYPASS": "1"})

        assert exit_code == 0
        assert stdout.strip() == ""

    def test_bypass_active_grep(self):
        """SCN-bypass-active-grep: FSM_BYPASS=1, Grep path to SKILL.md — exits 0, empty stdout."""
        payload = {"tool_name": "Grep", "tool_input": {"pattern": "some_regex", "path": "/path/to/skills/SKILL.md"}}
        exit_code, stdout, _ = run_block_hook(payload, env_overrides={"FSM_BYPASS": "1"})

        assert exit_code == 0
        assert stdout.strip() == ""

    def test_bypass_active_hooks_json(self):
        """SCN-bypass-active-hooks-json: FSM_BYPASS=1, Read hooks.json — exits 0, empty stdout."""
        payload = {"tool_name": "Read", "tool_input": {"file_path": "/path/to/skills/hooks.json"}}
        exit_code, stdout, _ = run_block_hook(payload, env_overrides={"FSM_BYPASS": "1"})

        assert exit_code == 0
        assert stdout.strip() == ""

    def test_bypass_active_fsm_json(self):
        """SCN-bypass-active-fsm-json: FSM_BYPASS=1, Read fsm.json — exits 0, empty stdout."""
        payload = {"tool_name": "Read", "tool_input": {"file_path": "/path/to/skills/fsm.json"}}
        exit_code, stdout, _ = run_block_hook(payload, env_overrides={"FSM_BYPASS": "1"})

        assert exit_code == 0
        assert stdout.strip() == ""

class TestDenialResponse:
    """REQ-env-var-bypass denial paths + REQ-updated-denial-message content constraints."""

    def test_bypass_not_set_denies(self):
        """SCN-bypass-not-set: FSM_BYPASS unset, Read SKILL.md — deny JSON emitted."""
        payload = {"tool_name": "Read", "tool_input": {"file_path": "/path/to/skills/SKILL.md"}}
        exit_code, stdout, _ = run_block_hook(payload, env_overrides={"FSM_BYPASS": None})

        assert exit_code == 0
        output = json.loads(stdout)
        assert_deny_structure(output)

    def test_bypass_empty_string_denies(self):
        """SCN-bypass-empty-string: FSM_BYPASS='', Read SKILL.md — deny JSON emitted."""
        payload = {"tool_name": "Read", "tool_input": {"file_path": "/path/to/skills/SKILL.md"}}
        exit_code, stdout, _ = run_block_hook(payload, env_overrides={"FSM_BYPASS": ""})

        assert exit_code == 0
        output = json.loads(stdout)
        assert_deny_structure(output)

    def test_denial_grep_without_bypass(self):
        """SCN-denial-grep: FSM_BYPASS unset, Grep path to SKILL.md — deny JSON emitted."""
        payload = {"tool_name": "Grep", "tool_input": {"pattern": "some_regex", "path": "/path/to/skills/SKILL.md"}}
        exit_code, stdout, _ = run_block_hook(payload, env_overrides={"FSM_BYPASS": None})

        assert exit_code == 0
        output = json.loads(stdout)
        assert_deny_structure(output)

    def test_denial_contains_bypass_instructions(self):
        """SCN-denial-contains-bypass-instructions: systemMessage contains 'export FSM_BYPASS=1'."""
        payload = {"tool_name": "Glob", "tool_input": {"pattern": "**/fsm.json"}}
        exit_code, stdout, _ = run_block_hook(payload)

        assert exit_code == 0
        output = json.loads(stdout)
        assert_deny_structure(output)
        assert "export FSM_BYPASS=1" in output["systemMessage"]

    def test_denial_removes_plugin_advice(self):
        """SCN-denial-removes-plugin-advice: systemMessage does NOT contain 'Disable finite-skill-machine'."""
        payload = {"tool_name": "Glob", "tool_input": {"pattern": "**/fsm.json"}}
        exit_code, stdout, _ = run_block_hook(payload)

        assert exit_code == 0
        output = json.loads(stdout)
        assert_deny_structure(output)
        assert "Disable finite-skill-machine" not in output["systemMessage"]

    def test_denial_reason_references_bypass(self):
        """EXTRA: permissionDecisionReason references the bypass mechanism."""
        payload = {"tool_name": "Read", "tool_input": {"file_path": "/path/to/skills/SKILL.md"}}
        exit_code, stdout, _ = run_block_hook(payload)

        assert exit_code == 0
        output = json.loads(stdout)
        assert_deny_structure(output)
        reason = output["hookSpecificOutput"]["permissionDecisionReason"]
        assert "FSM_BYPASS" in reason
