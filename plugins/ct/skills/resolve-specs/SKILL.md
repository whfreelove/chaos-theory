---
name: resolve-specs
description: Resolve gaps from critique findings through categorization, solution design, and documentation updates. Use after running ct:critique-specs to address identified gaps.
---

- Each lettered section **MUST COMPLETE** before the next lettered section
- Create TaskCreate tasks for each lettered section and make it block the section after
- Complete each section after all of its steps are complete
- Each numbered step **MUST COMPLETE** before the next numbered step
- Create TaskCreate tasks for each numbered step, make it block the step after (no prior-step-block for 1), make it blocked by the section before it (no prior-section-block for steps in A), and make it block the section task for the section its in (the last section section-block is not blocked by anything)
- Complete each step task after its work is verified and complete

## Gap Resolution Workflow

### D: Categorize Gap Resolution Method

1. Call a Task tool project manager subagent with the code block below as a prompt:
    - Model: Sonnet
    - Files: `${PROJECT_ROOT}/openspec/changes/<change>`
        - `gaps.md`

```
Categorize each entry in `gaps.md` (TodoWrite entry per gap):
1. Each high severity gap: (individual question per gap, batched into minimal responses) AskUserQuestion to triage "check-in" vs "defer-resolution"
2. Each medium severity gap: (individual question per gap, batched into minimal responses) AskUserQuestion to triage "check-in" vs "delegate" vs "defer-release" vs "defer-resolution"
3. Low severity gaps: autonomously triage between "check-in" vs "delegate" vs "defer-release"
4. Respond with gap category JSON list, e.g. `[{"id": 36, "category": "check-in"}]`
```

### E: Decide on Solutions

Thinking like an experienced software architect, update `gaps.md` with decisions on how to approach each gap:

1. All "check-in" gaps: (individual question per gap, batched into minimal responses) autonomously develop 5+ solutions, use at least 3 (recommend best 1) to AskUserQuestion for solution approach (include enough context for user to make informed decision), record decision in `gaps.md`
2. All "delegate" gaps: autonomously develop 3+ solutions, pick the best, output a text summary of each solution and final decision rationale, record decision to `gaps.md` entry
3. Call a Task tool subagent (use Haiku model, pass in list of gap IDs categorized "defer-*"):
    - Model: Haiku
    - Pass: "defer-*" gap IDs
    - Files: `${PROJECT_ROOT}/openspec/changes/<change>`
        - `gaps.md`

```
For each gap ID, update `gaps.md` to record decision.
defer-release: "acknowledge gap as acceptable for now, defer to future release"
defer-resolution: "blocking release, but defer resolution"
```

### F: Resolve Gaps

1. Call a Task tool subagent with the code block below as a prompt:
    - Model: Opus
    - Skills: `ce:documenting-systems`
    - Files: `${PROJECT_ROOT}/openspec/changes/<change>`
        - `gaps.md`
        - `resolved.md`
        - `proposal.md`
        - `design.md`
        - `specs/*/spec.md`

```
As an experienced software architect, resolve (fix, mitigate, or explicitly defer) each entry in `gaps.md` (TodoWrite list entry per gap):
1. Ignore entries that "defer resolution," continue to next gap
2. Merge the decision into OpenSpec artifact documentation such that future fresh agents working on them will understand the updated capabilities, behaviors, interfaces, requirements, scenarios fully
3. Move the gap entry to `resolved.md` and leave its ID, severity, description, and decisions intact
```

### G: Gap Leakage

1. Get the next available gap ID: `${CLAUDE_PLUGIN_ROOT}/scripts/next_gap.sh openspec/changes/<change>`
2. Call a Task tool documentation reviewer subagent with the code block below as a prompt:
    - Model: Opus
    - Pass: next available gap ID
    - Files: `${PROJECT_ROOT}/openspec/changes/<change>`
        - `gaps.md`
        - `resolved.md`
        - `proposal.md`
        - `design.md`
        - `specs/*/spec.md`

```
As an experience software technical writer, detect implicit gaps in documentation (TodoList entry per step):
1. Search `proposal.md`, `design.md`, and `specs/*/spec.md` for verbiage that indicates uncertainties and ambiguity
2. If none found, respond with empty JSON list: []
3. Append implicit gap entry findings to `gaps.md` with appropriate severity
4. Respond with new gap entry summary JSON list, e.g. [{"id": 36, "change": "new", "description": "what you found"}]
```

### H: Report

1. Output a summary of the findings resolved grouped by severity rating
2. Output a summary of the gaps remaining grouped by severity rating
3. If no critic findings were high or medium severity and no entries in `gaps.md` are high or medium severity, announce **DESIGN IS COMPLETE**
4. Otherwise, design is incomplete and more rounds of critique are suggested
