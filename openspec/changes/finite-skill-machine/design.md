## Overview

PostToolUse hook on `Skill` that reads a companion `fsm.json` file and writes tasks directly to the task store.

## Skill Package Structure

Skills that define workflows include an `fsm.json` alongside `SKILL.md`:

```
my-skill/
├── SKILL.md           # Agent instructions (references tasks conceptually)
└── fsm.json           # Task definitions (FSM reads this, agent doesn't)
```

**Important:** `SKILL.md` should NOT reference `fsm.json` directly. The agent works from the conceptual workflow in `SKILL.md`; FSM silently hydrates the task list. This prevents the agent from reading the JSON and wasting context.

## fsm.json Format

```json
[
  {
    "id": 1,
    "subject": "Set up environment",
    "activeForm": "Setting up environment"
  },
  {
    "id": 2,
    "subject": "Implement feature X",
    "description": "Details here",
    "blockedBy": [1]
  }
]
```

### Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | number | yes | Local offset ID (1, 2, 3...) |
| subject | string | yes | Task title (imperative form) |
| description | string | no | Detailed requirements |
| activeForm | string | no | Present continuous form for spinner |
| status | string | no | `pending` (default), `in_progress`, `completed` |
| blockedBy | number[] | no | Local IDs of blocking tasks |
| blocks | number[] | no | Local IDs of tasks this blocks |
| metadata | object | no | Arbitrary key-value pairs |
| owner | string | no | Agent assignment |

### ID Translation

IDs in `fsm.json` are **local offsets**, not global task IDs. The hook:
1. Reads existing task files to find max ID (call it `base`)
2. Translates each local ID: `actual_id = base + local_id`
3. Rewrites `blockedBy`/`blocks` arrays with translated IDs
4. Writes task files with actual IDs

**Example:** If max existing task ID is 5, and `fsm.json` has IDs 1, 2, 3:
- Local 1 → Actual 6
- Local 2 → Actual 7
- Local 3 → Actual 8
- `blockedBy: [1]` → `blockedBy: [6]`

## Hook Mechanics

### Input

Hook receives JSON via stdin:
```json
{
  "session_id": "uuid",
  "cwd": "/path/to/project",
  "tool_input": { "skill": "my-plugin:my-skill" },
  "tool_response": {
    "success": true,
    "commandName": "my-plugin:my-skill"
  }
}
```

### Skill Location

The hook locates the skill directory using `commandName` and `~/.claude/plugins/installed_plugins.json`.

**For plugin skills** (commandName contains `:`):

1. Parse `commandName` (e.g., `my-plugin:my-skill` → plugin=`my-plugin`, skill=`my-skill`)
2. Read `~/.claude/plugins/installed_plugins.json`
3. Find entries matching `{plugin}@*`
4. Filter to applicable entries:
   - `scope=local` or `scope=project`: `projectPath` must match or contain `cwd`
   - `scope=user`: always applies
5. Prefer most specific scope: `local` > `project` > `user`
6. Use `installPath` from selected entry
7. Check for `fsm.json` in:
   - `{installPath}/skills/{skill}/fsm.json`
   - `{installPath}/commands/{skill}/fsm.json` (if command is a directory)

**For non-plugin skills** (no `:` in commandName):

Check in order:
1. `{cwd}/.claude/skills/{skill}/fsm.json`
2. `~/.claude/skills/{skill}/fsm.json`

**installed_plugins.json missing or malformed:**

If commandName contains `:` (plugin-style) but `installed_plugins.json` is missing or contains invalid JSON, **fail-closed** with error: "Skill '{commandName}' not found - installed_plugins.json is missing or malformed". Do NOT fall back to non-plugin lookup in this case.

**Plugin not found in valid installed_plugins.json:**

If commandName contains `:` and `installed_plugins.json` exists and is valid, but no matching plugin entry is found, fall back to non-plugin skill lookup:
1. `{cwd}/.claude/skills/{skill}/fsm.json`
2. `~/.claude/skills/{skill}/fsm.json`

If no `fsm.json` found, no-op (skill has no predefined tasks).

**Note:** Relies on Claude Code internal file format (`installed_plugins.json`). May need updates if format changes.

### Output

- Writes task files to `~/.claude/tasks/{session_id}/{id}.json`
- Returns `{"continue": true}` to allow normal flow
- Logs activity to stderr

### Multi-Skill Task Interaction

The hook handles multiple skills creating tasks through selective deletion:

1. **No fsm.json:** No-op, preserves all existing tasks
2. **fsm.json found:** Delete only FSM-tagged tasks, preserve manual/other tasks
3. **Task Tagging:** All created tasks include `{"fsm": "skill-name"}` in metadata. The skill name value is stored for potential future use (e.g., per-skill task tracking), but **deletion checks for key existence only** - any task with an `fsm` metadata key is considered FSM-managed.
4. **Clean State:** New skill invocation deletes ALL FSM-tagged tasks (from any skill) and writes fresh tasks

This allows skills to coexist with manual task management. Manual tasks (those without `fsm` metadata key) are never deleted.

**Re-invocation Behavior:** When any skill with fsm.json is invoked, FSM performs fresh hydration: ALL tasks with `fsm` metadata key are deleted (regardless of which skill created them), then new tasks from the current skill's fsm.json are written. Any agent modifications to FSM-tagged tasks (status changes, owner assignments, metadata updates) ARE LOST. This is intentional - invoking a skill with fsm.json means "reset the FSM workflow."

### Error Handling

The hook uses **atomic fail-closed** behavior:

1. Parse + validate ALL tasks first
2. Only delete + write after full validation success
3. On any error: **hook fails**, notifying agent and user
4. Report ALL validation errors in single message

**Errors that trigger failure:**
- Malformed JSON in fsm.json
- Missing required `id` or `subject` field
- Duplicate IDs in same fsm.json
- Invalid dependency reference (ID not in same file)
- File write failures
- File deletion failures: "Failed to delete task {id}: {error}. Manual cleanup required at ~/.claude/tasks/{session_id}/"
- `installed_plugins.json` missing or malformed

**Rationale:** Silent failures prevent visibility into task creation problems. Explicit failures ensure issues are surfaced immediately.

**Non-errors (not detected):**
- Circular dependencies (e.g., task 1 blockedBy 2, task 2 blockedBy 1) — mirrors Claude Code's task system, which also does not detect cycles

## Task File Schema

The hook writes task files to `~/.claude/tasks/{session_id}/{id}.json` using Claude Code's native format:

```json
{
  "id": "6",
  "subject": "Set up environment",
  "description": "Detailed requirements here",
  "activeForm": "Setting up environment",
  "owner": "",
  "status": "pending",
  "blocks": [],
  "blockedBy": ["5"],
  "metadata": {
    "fsm": "my-plugin:my-skill"
  }
}
```

### Task File Fields

| Field | Type | Notes |
|-------|------|-------|
| id | string | **String, not number** - actual ID after translation |
| subject | string | Task title (imperative form) |
| description | string | Detailed requirements (empty string if not provided) |
| activeForm | string | Present continuous form for spinner (empty string if not provided) |
| owner | string | Agent assignment (empty string if not assigned) |
| status | string | `pending`, `in_progress`, or `completed` |
| blocks | string[] | Array of task ID strings this task blocks (always present, even if empty) |
| blockedBy | string[] | Array of task ID strings blocking this task (always present, even if empty) |
| metadata | object | Arbitrary key-value pairs (always includes `{"fsm": "skill-name"}`) |

**Key Implementation Notes:**
- `id` is a **STRING**, not a number - this is critical for compatibility with Claude Code's task system
- `blocks` and `blockedBy` are always present as arrays (empty `[]` when no dependencies)
- All dependency IDs in `blocks`/`blockedBy` are also strings
- Hook must convert numeric local IDs from fsm.json to string actual IDs in output

## Technology

- Pure Python 3 (stdlib only)
- JSON for task definitions and output

## File Structure

```
plugins/finite-skill-machine/
├── .claude-plugin/
│   └── plugin.json
├── hooks/
│   └── hooks.json
├── scripts/
│   └── hydrate-tasks.py
└── tests/
    ├── conftest.py
    ├── test_hydrate_tasks.py
    └── fixtures/
        └── ...
```

## Testing

### Framework and Approach

- **pytest** as test framework
- **tmpdir/tmp_path** fixtures for real filesystem operations
- **JSON fixtures** for test data (installed_plugins.json, fsm.json samples)
- **Subprocess execution** of hook script for integration tests
- **No external dependencies** beyond pytest

### Test Categories

**Unit Tests:**
- fsm.json parsing and validation
- ID translation logic (local → actual)
- Dependency resolution (symbolic refs → numeric IDs)
- Metadata merging (fsm tag + custom metadata)
- Error message formatting

**Integration Tests:**
- Full hook execution via subprocess with JSON stdin
- Verify stdout response (`{"continue": true}`)
- Verify task file outputs match expected schema

### Hook-Specific Testing Patterns

**Fixture-Based Testing:**
Create temp directories with controlled test data:

```python
@pytest.fixture
def task_dir(tmp_path):
    """Empty task directory for fresh hydration tests."""
    d = tmp_path / "tasks" / "session-123"
    d.mkdir(parents=True)
    return d

@pytest.fixture
def task_dir_with_manual_tasks(task_dir):
    """Task directory with pre-existing manual tasks."""
    (task_dir / "1.json").write_text('{"id": "1", "subject": "Manual task", ...}')
    return task_dir

@pytest.fixture
def task_dir_with_fsm_tasks(task_dir):
    """Task directory with pre-existing FSM-tagged tasks."""
    (task_dir / "1.json").write_text('{"id": "1", "metadata": {"fsm": "other-skill"}, ...}')
    return task_dir
```

**Testing Atomic Fail-Closed Behavior:**
1. Create task directory with existing FSM tasks
2. Provide fsm.json with validation errors
3. Execute hook (expect failure)
4. Verify NO tasks were deleted (original tasks still present)
5. Verify NO new tasks were written

**Testing installed_plugins.json Resolution:**
```python
@pytest.fixture
def installed_plugins(tmp_path):
    """Controlled installed_plugins.json for scope precedence tests."""
    content = [{
        "name": "my-plugin@1.0.0",
        "scope": "local",
        "projectPath": "/test/project",
        "installPath": str(tmp_path / "local-install")
    }, {
        "name": "my-plugin@1.0.0",
        "scope": "user",
        "installPath": str(tmp_path / "user-install")
    }]
    plugins_file = tmp_path / ".claude" / "plugins" / "installed_plugins.json"
    plugins_file.parent.mkdir(parents=True)
    plugins_file.write_text(json.dumps(content))
    return plugins_file
```

**Hook Subprocess Execution:**
```python
def run_hook(stdin_data: dict, env_overrides: dict = None) -> tuple[int, str, str]:
    """Execute hook script with JSON stdin, return (exit_code, stdout, stderr)."""
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)

    result = subprocess.run(
        ["python3", "scripts/hydrate-tasks.py"],
        input=json.dumps(stdin_data),
        capture_output=True,
        text=True,
        env=env
    )
    return result.returncode, result.stdout, result.stderr
```

**Verifying Atomicity (No Partial Writes):**
```python
def test_no_partial_writes_on_error(task_dir_with_fsm_tasks, invalid_fsm_json):
    """Verify atomic behavior: validation failure means no changes."""
    original_files = list(task_dir_with_fsm_tasks.iterdir())
    original_contents = {f.name: f.read_text() for f in original_files}

    exit_code, _, _ = run_hook(make_stdin(invalid_fsm_json))

    assert exit_code != 0  # Hook should fail
    # Verify nothing changed
    current_files = list(task_dir_with_fsm_tasks.iterdir())
    assert set(f.name for f in current_files) == set(original_contents.keys())
    for f in current_files:
        assert f.read_text() == original_contents[f.name]
```
