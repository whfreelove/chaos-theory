---
name: sculpt-specs
description: Freeform design refinement for specs in draft state. Reads all artifacts holistically to identify cross-cutting design tensions, then revises artifacts directly. Use when specs need fundamental coherency work before structured critique/resolve polishing.
---

Sculpting is iterative — this skill can be invoked multiple times while in `draft` state.
Each invocation is one iteration with three phases: Analyze, Write, Commit.

## Phase 1: Analyze

Read all artifacts in `openspec/changes/$0/` as a unit. Identify cross-cutting design tensions — not surface symptoms but underlying problems that would fragment into inconsistent gaps if evaluated dimension-by-dimension. Perform any research required to verify claims or inform direction: read the codebase, search for documentation, ask the user, etc.

What to look for:
- Cross-artifact contradictions (claims in one artifact that conflict with documented behavior in another)
- Design decisions that constrain each other without acknowledgment
- Components with undefined or circular data dependencies
- Stated properties (e.g., "independent", "forward-only") that don't survive contact with the specified data flows
- Runtime environment constraints (hooks, guards) that conflict with specified patterns
- Scope ambiguity between what's in/out of the deliverable
- Misplaced content located in inappropriate places

What NOT to look for (leave these for critique-specs/resolve-gaps):
- Gherkin normative violations, scenario coverage, wording polish

Present findings as design questions to the user via AskUserQuestion. Frame each tension as a choice between coherent alternatives, not a defect to fix. Batch related tensions into minimal AskUserQuestion calls.

After the user responds, revise the affected artifacts directly — no gap tracking. If no tensions are found, report that and skip to Phase 3.

## Phase 2: Write

For each artifact modified during Phase 1, invoke the corresponding writing skill to ensure design fixes are expressed in the right format:

| If touched... | Invoke skill |
|---|---|
| functional.md | `tokamak:writing-functional-specs` |
| technical.md | `tokamak:writing-technical-design` |
| requirements/*.feature.md | `tokamak:writing-markdown-gherkin` |
| infra.md | `tokamak:writing-infra-specs` |

Only invoke skills for artifacts that were actually modified. Follow each skill's guidance when revising.

## Phase 3: Commit

Stage and commit all changes from this iteration:

```bash
git add "openspec/changes/$0"
git commit -m $'sculpt($0): <summary of design changes>\n\n<list of tensions addressed>'
```

If there are no staged changes, skip the commit.

## Promoting to `reviewing`

When the user is satisfied the design is coherent, promote the change out of `draft`:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/change_status.sh" write "openspec/changes/$0" specs-status reviewing
```

Then confirm the transition: "specs-status promoted to reviewing. You can now run critique-specs."

Do NOT auto-promote — only promote when the user explicitly approves.
