---
name: archive-change
description: Archive a completed change after specs are merged and code is implemented. Use when both tracks are in terminal state.
---

# Archive Change

Archive a completed change with lifecycle state verification.

**Input**: `$0` is the change name. If empty, check conversation context. If ambiguous, prompt for available changes.

## Step 1: Validate state

Verify both tracks are in terminal state (redundant with hook gate):
- `specs-status: merged`
- `code-status: implemented` or `n/a`

```bash
specs=$("${CLAUDE_PLUGIN_ROOT}/scripts/change_status.sh" read "openspec/changes/$0" specs-status)
code=$("${CLAUDE_PLUGIN_ROOT}/scripts/change_status.sh" read "openspec/changes/$0" code-status)
```

If specs are not merged, suggest `Skill(tokamak:merge-change, args: "$0")`.
If code is not implemented/n/a, suggest `Skill(tokamak:implement-change, args: "$0")`.

## Step 2: Assess merge state

Verify that change artifacts have been merged into project documentation by checking that `specs-status` is `merged`.

If `specs-status` is `merged`, spot-check project docs for merged content (capabilities, requirements, technical decisions from the change should be present).

If merge appears incomplete:
- Offer to merge now via `Skill(tokamak:merge-change, args: "$0")`
- If user declines, warn and confirm they want to proceed without full merge

## Step 3: Pre-archive commit

Capture the final state of change artifacts in git before archiving.

Read the project name:
```bash
project=$("${CLAUDE_PLUGIN_ROOT}/scripts/change_status.sh" read "openspec/changes/$0" project)
```

Stage and commit the change directory only (not merged project changes):
```bash
git add "openspec/changes/$0"
git commit --allow-empty -m "spec(${project}): <summary of what the change accomplished>"
```

`--allow-empty` handles the case where artifacts are already committed. The message
should read as a changelog entry, e.g. `spec(finite-skill-machine): Add taskflow skill creation workflow`.

Tag the commit:
```bash
git tag "$project/$0"
```

If the tag already exists, warn the user and ask whether to overwrite (`git tag -f`) or skip.

## Step 4: Perform the archive

```bash
mkdir -p openspec/changes/archive
```

Generate target name with current date:
```bash
target="openspec/changes/archive/$(date +%Y-%m-%d)-$0"
```

Check if target already exists. If yes, fail with error.

```bash
mv "openspec/changes/$0" "$target"
```

## Step 5: Post-archive commit

The archive directory is `.gitignored`, so the `mv` effectively deletes `openspec/changes/$0`
from git tracking. Commit this deletion together with any merged project spec changes.

Stage the deleted change directory and merged project documentation:
```bash
git add "openspec/changes/$0"
git add "openspec/${project}/"
```

The first `git add` stages the deletion. The second stages project-level spec files updated during merge.
The `project` field is always relative to `openspec/` (e.g., `finite-skill-machine` → `openspec/finite-skill-machine/`).

```bash
git commit --allow-empty -m "spec(${project}): Archive $0"
```

## Step 6: Report summary

Display:
- Change name
- Archive location
- Whether specs were merged
- Final status of both tracks

**Guardrails**
- Always verify both tracks are in terminal state before archiving
- Do NOT bypass the hook gate — if lifecycle state is wrong, tell the user what to run
- If merge is needed, route through `Skill(tokamak:merge-change)`, NOT opsx:sync
- Preserve .openspec.yaml when moving (it moves with the directory)
