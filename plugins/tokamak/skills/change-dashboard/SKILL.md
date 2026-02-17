---
name: change-dashboard
description: View lifecycle status of all OpenSpec changes at a glance. Shows schema, version, specs-status, code-status, and created date. Use when agent or user wants to know what to work on next.
---

# Change Dashboard

## Step 1: Run the dashboard script

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/change_dashboard.sh"
```

If the user requested archived changes (e.g. `/change-dashboard --archive`), add the flag:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/change_dashboard.sh" --archive
```

## Step 2: Present the output

The script outputs a markdown table. Copy the **stdout** output verbatim into your response text so that Claude Code renders the table. Do not summarize or reformat it.

## Notes

- This is a **read-only** command. Do not modify any `.openspec.yaml` files.
- The output is a markdown table showing CHANGE, PROJECT, SCHEMA, VERSION, SPECS-STATUS, CODE-STATUS, and CREATED for each change.
- Missing fields display `-`.
- Archived changes (under `openspec/changes/archive/`) are excluded by default; use `--archive` to include them.
- A projects footer shows which project directories have no active changes referencing them.
