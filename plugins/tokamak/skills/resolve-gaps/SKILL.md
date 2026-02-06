---
name: resolve-gaps
description: Resolve gaps from critique findings through categorization, solution design, and documentation updates. Use after running tokamak:critique-specs to address identified gaps.
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
    1. Each high severity gap: (individual question per gap, batched into minimal responses) AskUserQuestion to triage "check-in" vs "defer-resolution"; NEVER ASK MULTIPLE GAPS IN ONE QUESTION
    2. Each medium severity gap: (individual question per gap, batched into minimal responses) AskUserQuestion to triage "check-in" vs "delegate" vs "defer-release" vs "defer-resolution"; NEVER ASK MULTIPLE GAPS IN ONE QUESTION
    3. Low severity gaps: autonomously triage between "check-in" vs "delegate" vs "defer-release"
    4. Respond with gap category JSON list, e.g. `[{"id": 36, "category": "check-in"}]`
    ```

2. Apply the gap categories in the response to `gaps.md`

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
        - `functional.md`
        - `technical.md`
        - `requirements/*/requirements.feature.md`

    ```
    As an experienced software architect, resolve (fix, mitigate, or explicitly defer) each entry in `gaps.md` (TaskList entry per gap):
    1. Ignore entries that "defer resolution," continue to next gap
    2. Merge the decision into OpenSpec artifact documentation such that future fresh agents working on them will understand the updated capabilities, behaviors, interfaces, requirements, scenarios fully
    3. When a Y-Statement would be added to `technical.md` Decisions section, you MUST use AskUserQuestion to confirm wording
    4. Move the gap entry to `resolved.md` and leave its ID, severity, description, and decisions intact
    ```

### G: Gap Cleanup

1. Get the next available gap ID: `${CLAUDE_PLUGIN_ROOT}/scripts/next_gap.sh openspec/changes/<change>`

2. Call the following three Task tool subagents **in parallel** in one message:

    - **Implicit Gap Detection**
        - Model: Opus
        - Pass: next available gap ID
        - Files: `${PROJECT_ROOT}/openspec/changes/<change>`
            - `gaps.md`
            - `functional.md`
            - `technical.md`
            - `infra.md`
            - `requirements/*/requirements.feature.md`

        ```
        As an experienced software technical writer, detect implicit gaps in documentation (TodoList entry per step):
        1. Search `functional.md`, `technical.md`, `infra.md`, and `requirements/*/requirements.feature.md`
        2. Find verbiage that indicates uncertainties and ambiguity
        3. If none found, respond with empty JSON list: []
        4. Append implicit gap entry findings to `gaps.md` with appropriate severity
        5. Respond with new gap entry summary JSON list, e.g. [{"id": 36, "change": "new", "description": "what you found"}]
        ```

    - **Stale Gap Detection**
        - Model: Opus
        - Files: `${PROJECT_ROOT}/openspec/changes/<change>`
            - `gaps.md`
            - `resolved.md`
            - `functional.md`
            - `technical.md`
            - `infra.md`
            - `requirements/*/requirements.feature.md`

        ```
        As an experienced software technical writer, detect stale gaps (TodoList entry per step):
        1. Search `functional.md`, `technical.md`, `infra.md`, and `requirements/*/requirements.feature.md`
        2. Compare to `gaps.md` and `resolved.md`
        3. Look for stale details in the current and resolved gaps from old versions of the specifications
        4. If none found, respond with empty JSON list: []
        5. Respond with stale gap JSON list, e.g. [{"id": 42, "rationale": "why"}]
        ```

    - **Gap Supersession Detection**
        - Model: Opus
        - Files: `${PROJECT_ROOT}/openspec/changes/<change>`
            - `gaps.md`

        ```
        As an experienced software technical writer, detect superseded gaps (TodoList entry per step):
        1. Search `gaps.md`
        2. Determine if any valid gaps appear to supersede others
        3. If none found, respond with empty JSON list: []
        4. One valid gap A that supersedes multiple gaps B, C should create two entries: A > B, A > C
        5. Multiple valid gaps A, B that, combined, supersede one gap C should create two entries: A > C, B > C
        6. Respond with gap comparison summary JSON list, e.g. [{"valid": 42, "superseded": 13, "rationale": "why"}]
        ```

3. Record implicit gaps to `gaps.md`
4. Categorize stale and superseded gap concerns: (individual question per concern, batched into minimal responses) AskUserQuestion to triage "check-in" vs "delegate" vs "defer-release" vs "defer-resolution"
5. All "check-in" concerns: (individual question per concerns, batched into minimal responses) autonomously develop 5+ solutions, use at least 3 (recommend best 1) to AskUserQuestion for solution approach (include enough context for user to make informed decision), apply decisions
6. All "delegate" concerns: autonomously develop 3+ solutions, pick the best, output a text summary of each solution and final decision rationale, apply decisions
7. Record each defer-release concern to `gaps.md` with decision: "acknowledge gap as acceptable for now, defer to future release"
8. Record each defer-resolution concern to `gaps.md` with decision: "blocking release, but defer resolution"
    ```

### H: Report

1. Output a summary of the findings resolved grouped by severity rating
2. Output a summary of the gaps remaining grouped by severity rating
3. If no critic findings were high or medium severity and no entries in `gaps.md` are high or medium severity, announce **DESIGN IS COMPLETE**
4. Otherwise, design is incomplete and more rounds of critique are suggested
