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

## Step 1b: Determine project path

Scan `openspec/` for project directories (anything that isn't `changes/`, `schemas/`, or files):
```bash
ls -1d openspec/*/ 2>/dev/null | grep -vE '(changes|schemas)/' | sed 's|openspec/||;s|/$||'
```

- **One project found**: AskUserQuestion yes/no: "Is this change for project `<name>`?"
- **Multiple projects found**: AskUserQuestion with project names as options + "New project"
- **No projects found**: AskUserQuestion open-ended: "What project is this change for?"

Record as `PROJECT_PATH` (e.g., `finite-skill-machine`). Directory does NOT need to exist yet.

## Step 1c: Determine project type (new projects only)

If the user selected an **existing project** in Step 1b, skip this step.

If the user specified a **new project**, use AskUserQuestion:
- "Is this project greenfield (building something new) or brownfield (documenting/modifying existing code)?"
- Options:
  - **Greenfield** — New codebase; specs designed collaboratively before implementation
  - **Brownfield** — Existing codebase; documentation reverse-engineered from code

If **brownfield**: present a follow-up recommendation:
- "For brownfield projects, consider starting with a documentation change first to capture the current codebase state. This creates a project baseline that future changes build on. Proceed with a brownfield documentation change?"
- Options:
  - **Yes, brownfield documentation change (Recommended)** — Use `--schema chaos-theory-brownfield` in Step 2
  - **No, proceed with a regular change** — Use default schema

If **greenfield**: use `--schema chaos-theory-greenfield` in Step 2.

Record the schema choice as `SCHEMA_FLAG` for Step 2.

## Step 2: Create the change directory

```bash
openspec new change "$0"
```

Add `${SCHEMA_FLAG}` if set by Step 1c. Also add `--schema <name>` if the user explicitly requested a specific workflow in a different step. Otherwise omit it to use the default schema.

If the user asks "what schemas are available", run `openspec schemas --json` and let them choose.

This creates a scaffolded change at `openspec/changes/$0/`.

## Step 2b: Initialize lifecycle status

```bash
echo "specs-status: new" >> "openspec/changes/$0/.openspec.yaml"
echo "code-status: waiting" >> "openspec/changes/$0/.openspec.yaml"
echo "project: ${PROJECT_PATH}" >> "openspec/changes/$0/.openspec.yaml"
```

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
- Project: `${PROJECT_PATH}`
- Triage policy: `.triage-policy.json` (profile name)
- Gap tracking: `gaps.md` and `resolved.md`
- Next step: run `opsx:continue` to begin creating artifacts

**Guardrails**
- Do NOT create any artifacts — only set up the change directory and prerequisites
- Do NOT advance beyond the summary
- If a change with the name already exists, inform the user and suggest `opsx:continue` instead
- If the name is not kebab-case, ask for a valid name
