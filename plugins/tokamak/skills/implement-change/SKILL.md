---
name: implement-change
description: Implement tasks from a ratified OpenSpec change with lifecycle tracking. Use when code-status is ready or in-progress.
---

# Implement Change

Implement tasks from an OpenSpec change with lifecycle status tracking.

**Input**: `$0` is the change name. If empty, check conversation context. If ambiguous, prompt for available changes.

**Note:** The PreToolUse hook validates `code-status: ready|in-progress` and denies this skill otherwise. The PostToolUse hook automatically transitions `code-status: ready → in-progress` when this skill is invoked.

## Step 1: Load context

```bash
openspec instructions apply --change "$0" --json
```

Use this output **only for the `contextFiles` list**. Ignore the `progress`, `tasks`, and `state` fields — they do not work with the chaos-theory schema's `tasks.yaml` format.

Then read `tasks.yaml` directly:

```
openspec/changes/$0/tasks.yaml
```

This file contains grouped task lists in YAML format (group names as keys, plain list items as tasks).

## Step 2: Read spec files

Read the files listed in `contextFiles` from the apply instructions output.

## Step 3: Create task list

Parse `tasks.yaml` groups into TaskCreate entries:
- One TaskCreate per YAML list item
- Prefix each task subject with its group name (e.g., `[test-relocation] Move conftest.py ...`)
- Create tasks in the order they appear in the file

**On re-invocation** (`code-status: in-progress`): Before creating tasks, inspect the codebase to determine which tasks are already done. Mark already-completed tasks as `completed` via TaskUpdate immediately after creation.

## Step 4: Implement tasks

Work group by group, in file order:
- Use TaskUpdate to set each task to `in_progress` before starting it
- Make the code changes required
- Keep changes minimal and focused
- Use TaskUpdate to set each task to `completed` after finishing it
- Continue to next task

**Pause if:**
- Task is unclear → ask for clarification
- Implementation reveals a design issue → suggest updating artifacts
- Error or blocker encountered → report and wait for guidance

## Step 5: Completion

**When ALL tasks are complete:**

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/change_status.sh" write "openspec/changes/$0" code-status implemented
```

Report:
- Tasks completed this session
- Overall progress: all tasks done

Check `specs-status` to suggest next step:
- If specs not yet merged → `Skill(tokamak:merge-change, args: "$0")`
- If specs already merged → `Skill(tokamak:archive-change, args: "$0")`

**If paused or blocked:** Leave status as `in-progress`.

**Guardrails**
- Keep going through tasks until done or blocked
- Always read context files before starting implementation
- If task is ambiguous, pause and ask before implementing
- Keep code changes minimal and scoped to each task
- Do NOT modify tasks.yaml — it is a spec artifact, not a progress tracker
- Do NOT set code-status to implemented until ALL tasks are complete
- On re-invocation, re-read tasks.yaml and assess progress from the codebase
