## Deployment

| Artifact | Location |
|---|---|
| Plugin root | `plugins/rodin/` |
| Hook definitions | `plugins/rodin/.claude-plugin/hooks/hooks.json` |
| Skill | `plugins/rodin/skills/plan-gate.md` |
| PostToolUse script | `plugins/rodin/hooks/post_tool_use.sh` |
| PreToolUse script | `plugins/rodin/hooks/pre_tool_use.sh` |

Hooks are activated via `hooks.json` binding `PostToolUse` on `Write|Edit` and `PreToolUse` on
`ExitPlanMode`. The skill is deployed to the Claude Code skills directory and invoked as
`/rodin:plan-gate`.

**Runtime dependencies:**

| Tool | Purpose | Notes |
|---|---|---|
| `jq` | Parse Claude Code hook JSON input | Only non-POSIX dependency; hooks check and fail with install guidance |
| `sed` | Text extraction, in-place metadata editing | Cross-platform helper required (`sed -i ''` on macOS, `sed -i` on Linux) |
| `grep` | Pattern matching, session marker discovery | POSIX standard |
| `shasum` | SHA-256 hash computation | POSIX standard; aliased to `sha256sum` on some Linux |
| `date` | ISO 8601 timestamp generation | POSIX standard |
| `python3` | Portable `realpath` computation | Built-in on macOS/Linux; used for path canonicalization only |

## Testing Strategy

Testing follows the `worktree-isolation` plugin pattern: fixture-based bash tests with mocked
inputs, no real LLM calls required for hook and orchestration logic.

### Test Layout

```
plugins/rodin/tests/
  run_tests.sh                  # Main test runner
  test_post_tool_use.sh         # PostToolUse hook tests
  test_pre_tool_use.sh          # PreToolUse hook tests
  test_skill_flow.sh            # Skill orchestration tests
  fixtures/
    plans/
      valid_plan.md             # Plan with valid rodin metadata (pass verdict)
      no_session.md             # Plan without session marker
      stale_plan_hash.md        # Plan with outdated plan hash
      stale_gaps_hash.md        # Plan with outdated gaps hash
      no_goals.md               # Plan without Goals section
      no_gaps_block.md          # Plan without gaps block markers
      empty_gaps_block.md       # Plan with empty gaps block
      pending_verdict.md        # Plan with validation=pending
      fail_verdict.md           # Plan with validation=fail
      deleted_metadata.md       # Plan with rodin comments removed
      malformed_markers.md      # Plan with unclosed/invalid markers
      hash_reference.md         # Minimal plan with known hash value for verification
    inputs/
      plan_mode_edit.json       # Hook input: permission_mode=plan, valid paths
      non_plan_mode.json        # Hook input: permission_mode != plan
      non_plan_file.json        # Hook input: file outside ~/.claude/plans/
      null_fields.json          # Hook input: missing session_id or file_path
      exit_plan_mode.json       # Hook input: ExitPlanMode with session_id
    subagents/
      leakage_none.json         # Leakage detector: no gap-like phrases
      leakage_found.json        # Leakage detector: 3+ phrases detected
      critic_pass.json          # Critic: NO ISSUES FOUND
      critic_findings.json      # Critic: multiple findings
      critic_malformed.json     # Critic: unparseable output (retry testing)
      critic_timeout.json       # Critic: simulated timeout response
      validator_pass.json       # Validator: VERDICT PASS
      validator_fail.json       # Validator: VERDICT FAIL
      validator_malformed.json  # Validator: unparseable output
```

### Test Categories and Requirement Mapping

| Test file | Requirements covered | Test type |
|---|---|---|
| `test_post_tool_use.sh` | `@post-tool-hook:1`, `@post-tool-hook:2` | Unit |
| `test_pre_tool_use.sh` | `@pre-tool-hook:1`, `@pre-tool-hook:2`, `@pre-tool-hook:3`, `@pre-tool-hook:5` | Unit |
| `test_skill_flow.sh` | `@plan-gate-skill:1`–`@plan-gate-skill:8` | Unit (mocked subagents) |
| `test_integration.sh` | `@pre-tool-hook:4` (bypass scenarios) | Integration |

**Unit tests** exercise hook logic in isolation using JSON fixture inputs piped to the hook
script. Assertions check exit codes, stdout/stderr content, and plan file state.

**Integration tests** chain multiple hook invocations with state verification between each
step, verifying that the skill→PostToolUse→PreToolUse state machine behaves correctly end-to-end.

### Assertion Helpers

```bash
assert_file_contains <file> <pattern>      # Verify pattern present in file
assert_exit_code <expected> <command>      # Verify exit status
assert_output_contains <pattern> <command> # Verify stdout/stderr content
```

### Skill Subagent Mocking

Skill tests use a mock Task tool wrapper (`mock_task`) that:
1. Records invocation arguments (model, prompt content)
2. Returns a predetermined fixture response from `MOCK_TASK_RESPONSES` sequence
3. Enables invocation-order and argument assertions

```bash
# Skill-specific assertion helpers
assert_task_invoked <model> <prompt_pattern>         # Verify Task call with model + prompt
assert_invocation_order <model1> <model2> ...        # Verify subagent sequence
assert_verdict_signal <status> <reason_pattern>      # Verify verdict signal content
```

Retry testing uses `MOCK_TASK_SEQUENCE` to return failure fixture first, success second:

```bash
export MOCK_TASK_SEQUENCE="critic_malformed.json,critic_findings.json"
```

### Test Naming Convention

Test functions follow `test_<requirement>_<scenario>` to map directly to requirement file scenarios:

```bash
test_goals_section_validation_missing_goals()    # @plan-gate-skill:2, "Plan missing goals section"
test_leakage_detection_below_threshold()         # @plan-gate-skill:4, "Few gap-like phrases"
test_enforcement_valid_pass_verdict()            # @pre-tool-hook:1, "Valid pass verdict"
```

Coverage verification: compare test function names against scenario titles. Missing test = coverage gap.

### Platform Portability Testing

- **Local**: macOS developer platform (primary target)
- **CI**: Linux container to verify `sed -i` without quotes works correctly
- **Manual verification**: Override `uname -s` return to test both code paths in `sed_inplace` helper

## Observability

- **Hook failure messages**: Surface directly in the Claude Code UI when the hook blocks exit,
  providing actionable guidance (`Run /rodin:plan-gate`, `Plan content changed since assessment`)
- **Session marker**: `<!-- rodin:session=<session_id> -->` links the plan file to the active
  session, enabling plan discovery and traceability across hook invocations
- **Embedded metadata**: All rodin state is readable as HTML comments in the plan file—any
  text editor can inspect current validation status, hashes, and verdict without special tooling
- **jq install guidance**: Error messages include OS-specific install commands so users can
  resolve the sole non-POSIX dependency without external documentation
