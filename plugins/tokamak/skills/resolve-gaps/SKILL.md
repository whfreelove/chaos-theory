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

### D: Triage Gap Resolution Method

1. Call a Task tool project manager subagent with the code block below as a prompt:
    - Model: Sonnet
    - Skills: `tokamak:managing-spec-gaps`
    - Files: `${PROJECT_ROOT}/openspec/changes/<change>`
        - `gaps.md`

    !`python ${CLAUDE_PLUGIN_ROOT}/scripts/resolve_triage_policy.py openspec/changes/$0`

    ```
    Apply triage semantics from tokamak:managing-spec-gaps when triaging.
    Apply the triage policy above to each entry in `gaps.md` (TodoWrite entry per gap):
    - For severity levels where user decides: (individual question per gap, batched into minimal responses) AskUserQuestion to triage between the listed options; NEVER ASK MULTIPLE GAPS IN ONE QUESTION
    - For severity levels where agent triages: autonomously triage between the listed options
    - For severity levels with a single option: apply that option directly without asking
    Respond with gap triage JSON list, e.g. `[{"id": 36, "triage": "check-in"}]`
    ```

2. Apply the gap triage values in the response to `gaps.md`

### E: Decide on Solutions + Assign Files

1. Read `gaps.md` and identify actionable gaps:
   - `placement-rejected`: gaps with a Placement-result field
   - `check-in`, `delegate`, `defer-release`: gaps with Triage but without Decision
   - `defer-resolution`: record decision directly (step 6 below, no solver needed)

2. Group actionable gaps (excluding defer-resolution) for parallel solution development:
   - Gaps whose solutions likely constrain each other → same group
   - ≤3 actionable gaps total → single group
   - Consider which gaps reference the same spec areas

3. Develop solutions via parallel Opus subagents:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/run_solvers.py" "openspec/changes/$0" \
     --groups '<JSON groups from step 2>'
   ```

   `--groups` format — dict mapping group labels to gap ID string lists:
   ```json
   {"technical-components": ["GAP-34", "GAP-35", "GAP-36"], "requirements-gherkin": ["GAP-38", "GAP-39"]}
   ```

   Save the returned `sessions` dict for potential rework.

4. Process returned proposals by triage type:

   **placement-rejected** proposals:
   - For each gap: present original Decision, rejection reason, solver's 3 alternatives
   - AskUserQuestion per gap (up to 4 per tool call)
   - Update Primary-file and Decision in gaps.md; clear Placement-result field

   **check-in** proposals:
   - For each gap: present problem context and top 4 solutions from solver
   - AskUserQuestion per gap (up to 4 per tool call)
   - NEVER ASK MULTIPLE GAPS IN ONE QUESTION
   - Record chosen Decision and Primary-file to gaps.md

   **delegate** proposals:
   - Review solver's recommendation for each gap
   - If recommendation is sound, accept it
   - Output problem context + solution summary + decision rationale
   - Record Decision and Primary-file to gaps.md

   **defer-release** proposals:
   - For each gap: present justification context and 4 rationale approaches
   - AskUserQuestion per gap (up to 4 per tool call)
   - Record chosen rationale in specification files
   - Record Decision, rationale, and Primary-file to gaps.md

5. Rework insufficient proposals (if any):

   Collect feedback for gaps whose proposals were rejected:
   - User selected "Other" on AskUserQuestion → user's typed direction is the feedback
   - Orchestrator found a delegate recommendation unsound → write specific issues

   Resume solver sessions with feedback:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/run_solvers.py" "openspec/changes/$0" \
     --resume --sessions '<JSON sessions from step 3>' \
     --feedback '<JSON: gap_id → feedback text>'
   ```
   Process reworked proposals (return to step 4 for the reworked gaps only).

6. **defer-resolution** gaps (no solver needed):
   - Record decision as "blocking release, but defer resolution" to gaps.md

When recording each decision, also record a `Primary-file` field indicating which
artifact file the resolution primarily modifies:
- Exact relative path within change directory (e.g., `functional.md`,
  `requirements/dependency-mapping/requirements.feature.md`)
- `gap-lifecycle` if resolution only affects gap lifecycle
- Each gap gets exactly one primary file

### F: Resolve Per-File

1. Group gaps by primary file:
  ```bash
  python "${CLAUDE_PLUGIN_ROOT}/scripts/group_gaps.py" "openspec/changes/$0"
  ```

  If there are ungrouped gaps, stop and report them — they need `Primary-file` annotations
  added in Section E before resolution can proceed.

2. Resolve change artifact files:
  ```bash
  python "${CLAUDE_PLUGIN_ROOT}/scripts/resolve_artifacts.py" "openspec/changes/$0"
  ```

3. Read `project` field from `.openspec.yaml`:
  ```bash
  project=$("${CLAUDE_PLUGIN_ROOT}/scripts/change_status.sh" read "openspec/changes/$0" project)
  ```

4. Launch parallel resolvers:
  ```bash
  python "${CLAUDE_PLUGIN_ROOT}/scripts/run_resolvers.py" "openspec/changes/$0" --timeout 600
  ```

  If any resolvers failed, report failures to the user and ask whether to
  proceed with partial results or retry.

5. Verify collation results:
  The resolver script handles collation as its final phase. Verify:
  - All resolved gaps moved from gaps.md to resolved.md
  - No conflicts in resolution reports
  - Outcome fields recorded for each resolved gap

### G: Gap Cleanup

1. Get the next available gap ID: `${CLAUDE_PLUGIN_ROOT}/scripts/next_gap.sh openspec/changes/<change>`

2. Run gap detectors:
  ```bash
  python "${CLAUDE_PLUGIN_ROOT}/scripts/run_critics.py" "openspec/changes/$0" --type gap-detectors
  ```

3. Record implicit gaps to `gaps.md`
4. Categorize stale, superseded, and uncovered defer-release gap concerns using triage semantics from tokamak:managing-spec-gaps: (individual question per concern, batched into minimal responses) AskUserQuestion to triage "check-in" vs "delegate" vs "defer-release" vs "defer-resolution"
5. For remaining check-in + delegate detected gaps, develop solutions via solver subagents:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/run_solvers.py" "openspec/changes/$0"
   ```
   Process proposals:
   - check-in: AskUserQuestion with top 3+ solutions (recommend best 1), apply decisions
   - delegate: review recommendation, output summary, apply decisions

6. Record each defer-release concern to `gaps.md` with decision: "acknowledge gap as acceptable for now, defer to future release"
7. Record each defer-resolution concern to `gaps.md` with decision: "blocking release, but defer resolution"

### H: Report

1. Stage and commit resolution changes:

    ```bash
    git add "openspec/changes/$0"
    git commit -m "spec($0): <subject>

    <body>"
    ```

    The subject should summarize the resolution action (e.g., `spec(rodin): Resolve 4 gaps, record 2 implicit gaps`).
    The body should list each gap resolved and each implicit gap recorded/resolved,
    one per line (e.g., `- GAP-36 resolved: Missing retry policy for webhook failures`).

    If there are no staged changes, skip the commit.

2. Output a summary of the findings resolved grouped by severity rating
3. Output a summary of the gaps remaining grouped by severity rating
