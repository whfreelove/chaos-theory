## Context

Claude Code plugin installed locally via `.claude-plugin/plugin.json`. No server infrastructure. Hooks execute as child processes of the Claude Code CLI. Task files are stored on the local filesystem at `~/.claude/tasks/{session_id}/`.

## Objectives

- `OBJ-test-coverage`: All requirements across task-hydration-skill (@task-hydration-skill:1 through @task-hydration-skill:8), v2-registry-parsing (@v2-registry-parsing:1 through @v2-registry-parsing:4, modified @task-hydration-skill:2), per-skill-deletion (@per-skill-deletion:1-2), and active-task-guard (@active-task-guard:1-3) covered by pytest suite
- `OBJ-local-deploy`: Plugin installable via standard Claude Code plugin mechanism with no additional setup
- `OBJ-backward-compat`: Existing v1 tests continue to pass — no regression in base functionality


## Deployment

### Plugin Installation

Plugin installed via Claude Code CLI. No environment configs, feature flags, or rollout stages.

Single deployment unit:
- `plugin.json` — plugin metadata
- `hooks/hooks.json` — hook definitions (PostToolUse on Skill, PreToolUse guard)
- `scripts/hydrate-tasks.py` — hydration hook
- `scripts/block-skill-internals.sh` — read guard

CI/CD pipeline (GitHub Actions, merge flow) is documented in `openspec/common/infra.md`.

## Testing Strategy

### Test Environment

Tests run locally via `pytest` using subprocess-based `run_hook()` helper in `helpers.py` (exposed as a session-scoped fixture via `conftest.py`). Each test gets an isolated `tmp_path` directory for task files, skill directories, and plugin manifests. The `FSM_PLUGINS_FILE` env var overrides the registry path for test isolation. No external services or network access required.

Contributor setup and general verification approach are documented in `openspec/common/infra.md`.

### Fixtures

- **tmp_path**: pytest built-in for filesystem operations
- **JSON fixtures**: `installed_plugins.json` samples (v1 and v2 formats), `fsm.json` samples
- **v2 format registry fixtures**: Object with `"version": 2` and `"plugins"` dict containing plugin entries keyed by `plugin@marketplace` format
- **Malformed registry fixtures**: Missing version field (`{"plugins": {}}`), unknown version number (`{"version": 3, "plugins": {}}`), plugins-not-dict (`{"version": 2, "plugins": []}`), missing plugins key (`{"version": 2}`)
- **Multi-key registry fixtures**: Registry with multiple marketplace keys (e.g., `"alpha@marketplace"` and `"beta@marketplace"`) for key matching isolation tests
- **Multi-skill task directory**: Pre-populated with FSM tasks from two different skills (e.g., `"fsm": "plugin-a:skill-a"` and `"fsm": "plugin-b:skill-b"`) plus a manual task
- **Active task fixtures**: Task directories containing tasks with various status combinations for the invoking skill, used by the active guard tests. Includes: all-pending, all-completed, all-in_progress, mixed completed+pending, mixed in_progress+completed

### Coverage Mapping

| Capability | Test Class | Covers |
|------------|-----------|--------|
| `task-hydration-skill` | Test infrastructure | @task-hydration-skill:1-8 baseline |
| `task-hydration-skill` | TestFsmValidation | @task-hydration-skill:4 (fsm.json validation) |
| `task-hydration-skill` | TestIdTranslation (modified) | @task-hydration-skill:5 (ID translation with scoped deletion) |
| `task-hydration-skill` | TestScopePrecedence | @task-hydration-skill:3 (scope precedence) |
| `task-hydration-skill` | TestHookExecution | @task-hydration-skill:1, @task-hydration-skill:2, @task-hydration-skill:8 (full hook execution) |
| `task-hydration-skill` | TestAtomicDeletion | @task-hydration-skill:7 (atomic deletion behavior) |
| `task-hydration-skill` | TestAtomicBehavior | @task-hydration-skill:7 (validation blocks deletion, file system error aborts) |
| `task-hydration-skill` | TestV1Deprecation | @task-hydration-skill:2 (modified): deprecation emitted to stderr, message content |
| `v2-registry-parsing` | TestFormatDetection | @v2-registry-parsing:1 (v2 detected, v1 detected, malformed, unknown version) |
| `v2-registry-parsing` | TestV2KeyMatching | @v2-registry-parsing:2 (plugin key matching, no match fallback, empty plugins, multiple keys) |
| `v2-registry-parsing` | TestV2ScopePrecedence | @v2-registry-parsing:3 (scope ordering, projectPath matching, missing installPath) |
| `v2-registry-parsing` | TestV2MalformedRegistry | @v2-registry-parsing:4 (fail-closed for structural issues, non-plugin fallback) |
| `per-skill-deletion` | TestPerSkillDeletion | @per-skill-deletion:1 (deletion scoping by fsm metadata value) |
| `per-skill-deletion` | TestPerSkillIdOffset | @per-skill-deletion:2 (ID offset calculation with preserved tasks, corrupted files) |
| `active-task-guard` | TestActiveTaskGuard | @active-task-guard:1 (uniform-status proceed/mixed-status abort logic) |
| `active-task-guard` | TestActiveTaskGuardMessage | @active-task-guard:2 (JSON abort format, message content constraints) |
| `active-task-guard` | TestActiveTaskGuardScope | @active-task-guard:3 (cross-skill isolation of guard checks) |
| `session-bypass` | TestBypassGuard | @CAP-session-bypass:1.1 (Read SKILL.md allowed with bypass) |
| `session-bypass` | TestBypassGuard | @CAP-session-bypass:1.2 (Read SKILL.md denied without bypass) |
| `session-bypass` | TestBypassGuard | @CAP-session-bypass:1.3 (Glob allowed with bypass) |
| `session-bypass` | TestBypassGuard | @CAP-session-bypass:1.4 (Grep allowed with bypass) |
| `session-bypass` | TestBypassGuard | @CAP-session-bypass:1.5 (Read hooks.json allowed with bypass) |
| `session-bypass` | TestBypassGuard | @CAP-session-bypass:1.6 (Read fsm.json allowed with bypass) |
| `session-bypass` | TestDenialResponse | @CAP-session-bypass:1.7 (empty string bypass denied) |
| `session-bypass` | TestDenialResponse | @CAP-session-bypass:1.8 (Grep denied without bypass) |
| `actionable-denial` | TestDenialResponse | @CAP-actionable-denial:1.1 (denial contains bypass instructions) |
| `actionable-denial` | TestDenialResponse | @CAP-actionable-denial:1.2 (denial removes plugin advice) |

Coverage for `contributor-reproduces-environment` and `ci-validates-pr` is documented in `openspec/common/infra.md`.

### Testing Patterns

**Fixture-based filesystem**: Create temp directories with controlled test data (existing tasks, installed_plugins.json entries, fsm.json files) to isolate each test case.

**Subprocess integration**: Execute `hydrate-tasks.py` via `subprocess.run()` with JSON stdin, capturing stdout/stderr/exit code to verify hook behavior end-to-end.

**Atomicity verification**: Pre-record filesystem state, trigger validation failure, confirm no files were created/deleted/modified.

**Backward compatibility verification**: Existing v1 fixtures stay unchanged — they verify backward compatibility. Existing scope precedence tests remain as-is (v1 path, unchanged behavior). No existing test classes require structural changes; new test classes cover new and modified behavior independently.

**Existing test modifications**: The existing `TestIdTranslation` test class needs updates to account for preserved other-skill tasks in the max ID calculation. The `task_dir_with_fsm_tasks` fixture currently uses `"fsm": "other-skill"` — tests invoking with a different skill name will now preserve these tasks instead of deleting them, requiring fixture or assertion adjustments.

## Observability

- stderr logging for hook activity (skill resolution, task creation, errors)
- stderr deprecation notice for v1 format (new in v2-registry-parsing)
- Error messages for malformed v2 registries use `error_exit()` to stderr per existing hook protocol
- No metrics, dashboards, or alerts (local CLI plugin)
- CI observability (run logs, status badges) documented in `openspec/common/infra.md`
