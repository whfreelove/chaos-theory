---
name: ratify-specs
description: Ratify reviewed specs to unlock implementation. Use after the user has run critique/resolve CLI tools and specs are ready.
---

# Ratify Specs

Transition specs from reviewing to ratified, unlocking implementation.

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
- **Ratify** — Mark specs as ratified, unlock implementation
- **Not ready** — User needs to run another critique/resolve round via CLI first

## Step 4: Apply ratification

If the user chooses "Ratify":

1. Set `specs-status: ratified`:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/change_status.sh" write "openspec/changes/$0" specs-status ratified
```

2. Resolve artifacts to determine if tasks exist:
```bash
artifacts=$(python "${CLAUDE_PLUGIN_ROOT}/scripts/resolve_artifacts.py" "openspec/changes/$0")
```

Check the `has_tasks` field from the JSON output:
- If `has_tasks` is `false` → no implementation needed:
  ```bash
  "${CLAUDE_PLUGIN_ROOT}/scripts/change_status.sh" write "openspec/changes/$0" code-status n/a
  ```
- If `has_tasks` is `true` → implementation needed:
  ```bash
  "${CLAUDE_PLUGIN_ROOT}/scripts/change_status.sh" write "openspec/changes/$0" code-status ready
  ```

If the user chooses "Not ready", tell the user to run critique/resolve outside this session:

> Run another critique/resolve round via CLI:
>
> ```
> python plugins/tokamak/scripts/run_critique_specs.py openspec/changes/$0
> python plugins/tokamak/scripts/run_resolve_gaps.py openspec/changes/$0
> ```
>
> Then return here to ratify.

## Step 5: Report status

Display the new state and next steps:
- If `code-status: ready` → suggest `Skill(tokamak:implement-change, args: "$0")`
- If `code-status: n/a` → suggest `Skill(tokamak:merge-change, args: "$0")` to merge spec changes

**Guardrails**
- Do NOT ratify without user confirmation
- Do NOT skip the gap summary — the user needs this information to make an informed decision
- If there are open HIGH severity gaps, warn prominently before presenting the ratify option
