---
name: ratify-specs
description: Ratify reviewed specs to unlock implementation. Use after critique/resolve cycles are complete and specs are ready.
---

# Ratify Specs

Transition specs from reviewing to ready, unlocking implementation.

**Input**: `$0` is the change name. If empty, ask the user which change to ratify.

## Step 1: Validate state

Verify `specs-status: reviewing` (redundant with hook gate, but serves as instruction-level safety).

```bash
current=$("${CLAUDE_PLUGIN_ROOT}/scripts/change_status.sh" read "openspec/changes/$0" specs-status)
```

If not `reviewing`, inform the user what state the change is in and what needs to happen first.

## Step 2: Compute gap summary

Read `openspec/changes/$0/gaps.md` and `openspec/changes/$0/resolved.md`.

Compute:
- Open gaps by severity (HIGH / MEDIUM / LOW count)
- Defer-resolution count (gaps marked as defer-resolution in resolved.md)
- Total gaps vs resolved gaps

## Step 3: Present ratification checklist

Use **AskUserQuestion** to present the readiness assessment:

Question: "Ready to ratify specs for `$0`?"

Include in the description:
- Open gaps breakdown (by severity)
- Defer-resolution count
- Readiness signals:
  - All HIGH/MEDIUM gaps resolved?
  - No defer-resolution gaps?
  - Specs reflect intended design?

Options:
- **Ratify** — Mark specs as ready, unlock implementation
- **Not ready** — Run another critique/resolve round first

## Step 4: Apply ratification

If the user chooses "Ratify":

1. Set `specs-status: ready`:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/change_status.sh" write "openspec/changes/$0" specs-status ready
```

2. Check `tasks.yaml` to determine code-status:
```bash
tasks_file="openspec/changes/$0/tasks.yaml"
if [[ ! -f "$tasks_file" ]] || ! grep -v '^#' "$tasks_file" | grep -v '^[[:space:]]*$' | grep -q .; then
  # No tasks or empty tasks file → no implementation needed
  "${CLAUDE_PLUGIN_ROOT}/scripts/change_status.sh" write "openspec/changes/$0" code-status n/a
else
  "${CLAUDE_PLUGIN_ROOT}/scripts/change_status.sh" write "openspec/changes/$0" code-status ready
fi
```

If the user chooses "Not ready", suggest running `Skill(tokamak:critique-specs, args: "$0")`.

## Step 5: Report status

Display the new state and next steps:
- If `code-status: ready` → suggest `Skill(tokamak:implement-change, args: "$0")`
- If `code-status: n/a` → suggest `Skill(tokamak:merge-change, args: "$0")` to merge spec changes

**Guardrails**
- Do NOT ratify without user confirmation
- Do NOT skip the gap summary — the user needs this information to make an informed decision
- If there are open HIGH severity gaps, warn prominently before presenting the ratify option
