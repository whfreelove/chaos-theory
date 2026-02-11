---
name: resolve-gaps-brownfield
description: Resolve gaps from brownfield documentation critique through categorization, solution design, and documentation updates. Resolutions favor updating documentation to match code reality. Use after running tokamak:critique-specs-brownfield to address identified gaps.
---

- Each lettered section **MUST COMPLETE** before the next lettered section
- Create TaskCreate tasks for each lettered section and make it block the section after
- Complete each section after all of its steps are complete
- Each numbered step **MUST COMPLETE** before the next numbered step
- Create TaskCreate tasks for each numbered step, make it block the step after (no prior-step-block for 1), make it blocked by the section before it (no prior-section-block for steps in A), and make it block the section task for the section its in (the last section section-block is not blocked by anything)
- Complete each step task after its work is verified and complete

## Brownfield Gap Resolution Workflow

**The code is ground truth. Documentation describes what IS, not what should be.**

Resolutions always favor updating documentation to match code reality. Never suggest code changes as gap resolution, except for critical concerns (security vulnerabilities, data loss risks).

### D: Categorize Gap Resolution Method

1. Call a Task tool project manager subagent with the code block below as a prompt:
    - Model: Sonnet
    - Skills: `tokamak:managing-spec-gaps`
    - Files: `${PROJECT_ROOT}/openspec/changes/<change>`
        - `gaps.md`

    ```
    Apply category semantics from tokamak:managing-spec-gaps when triaging.
    Categorize each entry in `gaps.md` (TodoWrite entry per gap):
    1. Each high severity gap: (individual question per gap, batched into minimal responses) AskUserQuestion to triage "check-in" vs "defer-resolution"; NEVER ASK MULTIPLE GAPS IN ONE QUESTION
    2. Each medium severity gap: (individual question per gap, batched into minimal responses) AskUserQuestion to triage "check-in" vs "delegate" vs "defer-release" vs "defer-resolution"; NEVER ASK MULTIPLE GAPS IN ONE QUESTION
    3. Low severity gaps: autonomously triage between "check-in" vs "delegate" vs "defer-release"
    4. Respond with gap category JSON list, e.g. `[{"id": 36, "category": "check-in"}]`
    ```

2. Apply the gap categories in the response to `gaps.md`

### E: Decide on Solutions

Thinking like an experienced technical writer improving documentation accuracy, update `gaps.md` with decisions on how to update the documentation for each gap. The focus is "How should we update the documentation?" not "How should we fix the code?"

- All "check-in" gaps: (perform steps **per individual gap**)
  1. Write enough problem context to output for uninformed user to understand your documentation correction dilemma
  2. Autonomously develop 5+ documentation correction options
  3. Sort the options from best to worst
  4. Write each option to output
    - Include enough context for uninformed user to make informed decision
    - Include why you like the option
  5. Pick the best option and write explanation why to output
  6. Ask user with each gap in a separate question
    - AskUserQuestion tool
    - Use the top 4 options
    - Up to 4 gap questions per tool call
  7. Record chosen decision to `gaps.md`
- All "delegate" gaps:
  1. Write enough problem context to output for uninformed user to understand your documentation correction dilemma
  2. Autonomously develop 3+ documentation correction options
  3. Sort the options from best to worst
  4. Write each option to output
    - Include enough context for uninformed user to make informed decision
    - Include why you like the approach
  5. Pick the best option and write explanation why to output
  6. Record chosen decision to `gaps.md`
- All "defer-release" gaps:
  1. Write enough problem context to output for uninformed user to understand your justification dilemma
  2. Develop 4 plausible rationale approaches
    - Autonomously consider the documentation accuracy/completeness/risk impacts of deferment
    - Determine plausible rationale for the impacts
    - Decide where it should be recorded (Functional Out of Scope, Current Limitations, Planned Future Work, Technical Decision, Technical Known Risk, or combinations)
  3. Sort the plausible approaches from best to worst
  4. Write each plausible approach to output
    - Include enough context for uninformed user to make informed decision
    - Include why you like the approach
  5. Ask user with each gap in a separate question
    - AskUserQuestion tool
    - Use the 4 plausible approaches
    - Up to 4 gap questions per tool call
  6. Record chosen rationale in specification files
  7. Record decision and rationale to `gaps.md`
- All "defer-resolution" gaps:
  1. Record decision as "blocking documentation completeness, but defer resolution" to `gaps.md`

### F: Resolve Gaps

1. Call a Task tool subagent with the code block below as a prompt:
    - Model: Opus
    - Skills: `ce:documenting-systems`, `tokamak:managing-spec-gaps`
    - Files: `${PROJECT_ROOT}/openspec/changes/<change>`
        - `gaps.md`
        - `resolved.md`
        - `functional.md`
        - `technical.md`
        - `infra.md`
        - `requirements/*/requirements.feature.md`

    ```
    As an experienced technical writer improving brownfield documentation accuracy, resolve (fix, mitigate, or explicitly defer) each entry in `gaps.md` (TaskList entry per gap):

    The code is ground truth. Documentation describes what IS, not what should be.

    1. Ignore entries that "defer resolution," continue to next gap
    2. Merge the decision into brownfield documentation artifacts such that future fresh agents working on them will understand the documented capabilities, behaviors, interfaces, requirements, and scenarios accurately reflect the codebase
    3. When a Y-Statement would be added to `technical.md` Decisions section, use `[initial-docs]` provenance and you MUST use AskUserQuestion to confirm wording
    4. Move the gap entry to `resolved.md` and leave its ID, severity, description, and decisions intact
    5. Apply resolution completeness and supersession rules from tokamak:managing-spec-gaps: Decision text is immutable, co-resolved gaps use bidirectional refs, defer-release needs artifact coverage before moving to resolved.md, superseded gaps use Category: superseded with Superseded by and Current approach fields
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
        As an experienced technical writer, detect implicit gaps in brownfield documentation (TodoList entry per step):
        1. Search `functional.md`, `technical.md`, `infra.md`, and `requirements/*/requirements.feature.md`
        2. Find verbiage that indicates uncertainties, ambiguity, or hedging about code behavior (e.g., "likely", "appears to", "seems to", "probably")
        3. If none found, respond with empty JSON list: []
        4. Append implicit gap entry findings to `gaps.md` with appropriate severity and `Source: implicit-detection`
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
        As an experienced technical writer, detect stale gaps (TodoList entry per step):
        1. Search `functional.md`, `technical.md`, `infra.md`, and `requirements/*/requirements.feature.md`
        2. Compare to `gaps.md` and `resolved.md`
        3. Look for stale details in the current and resolved gaps from old versions of the documentation
        4. If none found, respond with empty JSON list: []
        5. Any new gaps recorded from stale concerns should use `Source: stale-detection`
        6. Respond with stale gap JSON list, e.g. [{"id": 42, "rationale": "why"}]
        ```

    - **Gap Supersession Detection**
        - Model: Opus
        - Skills: `tokamak:managing-spec-gaps`
        - Files: `${PROJECT_ROOT}/openspec/changes/<change>`
            - `gaps.md`

        ```
        Apply supersession rules from tokamak:managing-spec-gaps.
        As an experienced technical writer, detect superseded gaps (TodoList entry per step):
        1. Search `gaps.md`
        2. Determine if any valid gaps appear to supersede others
        3. If none found, respond with empty JSON list: []
        4. One valid gap A that supersedes multiple gaps B, C should create two entries: A > B, A > C
        5. Multiple valid gaps A, B that, combined, supersede one gap C should create two entries: A > C, B > C
        6. Any new gaps recorded from supersession concerns should use `Source: supersession-detection`
        7. Respond with gap comparison summary JSON list, e.g. [{"valid": 42, "superseded": 13, "rationale": "why"}]
        ```

    - **Defer-Release Coverage Detection**
        - Model: Opus
        - Skills: `tokamak:managing-spec-gaps`
        - Files: `${PROJECT_ROOT}/openspec/changes/<change>`
            - `gaps.md`
            - `functional.md`
            - `technical.md`

        ```
        Apply resolution completeness principles from tokamak:managing-spec-gaps.
        As an experienced technical writer, detect defer-release gaps lacking artifact coverage (TodoList entry per step):
        1. Extract all gaps marked "defer-release" or "DEFERRED TO FUTURE RELEASE" from `gaps.md`
        2. For each defer-release gap:
           a. Check if the gap's concern is semantically addressed in `functional.md` Out of Scope, Current Limitations, or Planned Future Work sections
           b. Check if the gap's concern is semantically addressed in `technical.md` Decisions section (Y-Statements)
           c. "Covered" means the artifact explicitly acknowledges the limitation/deferral, not just tangentially mentions the topic
        3. If all defer-release gaps are covered, respond with empty JSON list: []
        4. Any new gaps recorded from coverage concerns should use `Source: defer-release-coverage-detection`
        5. Respond with uncovered gap JSON list, e.g. [{"gap_id": 108, "description": "gap description", "rationale": "why not covered by Out of Scope, Current Limitations, Planned Future Work, or Decisions"}]
        ```

3. Record implicit gaps to `gaps.md`
4. Categorize stale, superseded, and uncovered defer-release gap concerns using category semantics from tokamak:managing-spec-gaps: (individual question per concern, batched into minimal responses) AskUserQuestion to triage "check-in" vs "delegate" vs "defer-release" vs "defer-resolution"
5. All "check-in" concerns: (individual question per concerns, batched into minimal responses) autonomously develop 5+ solutions, use at least 3 (recommend best 1) to AskUserQuestion for solution approach (include enough context for user to make informed decision), apply decisions
6. All "delegate" concerns: autonomously develop 3+ solutions, pick the best, output a text summary of each solution and final decision rationale, apply decisions
7. Record each defer-release concern to `gaps.md` with decision: "acknowledge documentation gap as acceptable for now, defer to future documentation pass"
8. Record each defer-resolution concern to `gaps.md` with decision: "blocking documentation completeness, but defer resolution"
    ```

### H: Report

1. Output a summary of the findings resolved grouped by severity rating
2. Output a summary of the gaps remaining grouped by severity rating
3. If no critic findings were high or medium severity and no entries in `gaps.md` are high or medium severity, announce **DOCUMENTATION IS COMPLETE**
4. Otherwise, documentation is incomplete and more rounds of critique are suggested
