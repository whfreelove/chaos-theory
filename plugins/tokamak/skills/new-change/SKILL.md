---
name: new-change
description: Create a new OpenSpec change with triage policy and gap tracking initialized. Use when starting a new feature, fix, or modification.
---

# New Change

Create a new OpenSpec change directory with all prerequisites for the critique/resolve workflow.

**Input**: `$0` is the change name (kebab-case). If empty, ask the user what they want to build and derive a kebab-case name.

## Step 1: Determine change name

If `$0` is empty, use AskUserQuestion (open-ended, no preset options):
> "What change do you want to work on? Describe what you want to build or fix."

From the description, derive a kebab-case name (e.g., "add user authentication" becomes `add-user-auth`).

**Do NOT proceed without a change name.**

## Step 2: Create the change directory

```bash
openspec new change "$0"
```

Add `--schema <name>` only if the user explicitly requested a specific workflow. Otherwise omit it to use the default schema.

If the user asks "what schemas are available", run `openspec schemas --json` and let them choose.

This creates a scaffolded change at `openspec/changes/$0/`.

## Step 3: Select triage policy

Use **AskUserQuestion** to ask which triage profile to use:

- Question: "Which triage policy should this change use?"
- Options:
  - **default (Recommended)** — HIGH/MEDIUM severity: user decides. LOW severity: agent decides.
  - **conservative** — All severities require user check-in before action.
  - **confident** — HIGH: user decides. MEDIUM/LOW: agent decides.
  - **autonomous** — All severities delegated to agent.

Then initialize the policy:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/resolve_triage_policy.py" "openspec/changes/$0" --init <profile>
```

Where `<profile>` is the user's selection (default, conservative, confident, or autonomous).

## Step 4: Initialize gap tracking

Copy the gap tracking templates into the change directory:

```bash
cp "${CLAUDE_PLUGIN_ROOT}/skills/critique-specs/templates/gaps.md" "openspec/changes/$0/gaps.md"
cp "${CLAUDE_PLUGIN_ROOT}/skills/critique-specs/templates/resolved.md" "openspec/changes/$0/resolved.md"
```

## Step 5: Summary

Report what was created:

- Change directory: `openspec/changes/$0/`
- Triage policy: `.triage-policy.json` (profile name)
- Gap tracking: `gaps.md` and `resolved.md`
- Next step: run `opsx:continue` to begin creating artifacts

**Guardrails**
- Do NOT create any artifacts — only set up the change directory and prerequisites
- Do NOT advance beyond the summary
- If a change with the name already exists, inform the user and suggest `opsx:continue` instead
- If the name is not kebab-case, ask for a valid name
