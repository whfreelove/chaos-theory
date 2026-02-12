---
name: critique-specs
description: Run parallel critics against OpenSpec change artifacts and document gaps. Use when validating proposal, design, specs, or tasks against each other.
---

- Each lettered section **MUST COMPLETE** before the next lettered section
- Create TaskCreate tasks for each lettered section and make it block the section after
- Complete each section after all of its steps are complete
- Each numbered step **MUST COMPLETE** before the next numbered step
- Create TaskCreate tasks for each numbered step, make it block the step after (no prior-step-block for 1), make it blocked by the section before it (no prior-section-block for steps in A), and make it block the section task for the section its in (the last section section-block is not blocked by anything)
- Complete each step task after its work is verified and complete

## Documentation Critique Workflow

### A: Critique

1. Ensure `gaps.md` and `resolved.md` exist in `openspec/changes/$0/`. If missing, create them with:

    **gaps.md**:
    !`cat ${CLAUDE_PLUGIN_ROOT}/skills/critique-specs/templates/gaps.md`

    **resolved.md**:
    !`cat ${CLAUDE_PLUGIN_ROOT}/skills/critique-specs/templates/resolved.md`

2. Critic selection:

    !`python ${CLAUDE_PLUGIN_ROOT}/scripts/select_critics.py openspec/changes/$0`

    If the `critics` array is empty, skip to section B. For each critic in the output, create a task blocking this step then invoke **all** critic Task tool subagents in a **single message** (blocking parallel calls, do NOT use `run_in_background`). This ensures all critics complete before proceeding. Each subagent should have:
    - Model: `model` field
    - Files: `${PROJECT_ROOT}/openspec/changes/$0`
        - The OpenSpec artifacts listed in `files` field
        - `gaps.md`
        - `resolved.md`
    - Evaluation criteria: `evaluate` field
    - Include:
        - Do not submit gaps already covered in `gaps.md` or `resolved.md`
        - One quality gap is more valuable than ten covered or nitpick gaps
        - Standard critic output format template from `output_template` field
3. If gaps with valid statuses (not rejected, deprecated, or superseded) in `gaps.md`, `resolved.md`, or critic findings conflict with each other, resolve the conflict with a user check in via AskUserQuestion; typical options might include rejecting either or both or merging them somehow

### B: Validation

1. Call a Task tool validation subagent with the code block below as a prompt:
    - Model: Sonnet
    - Pass: critic findings
    - Files: `${PROJECT_ROOT}/openspec/changes/$0`
        - `gaps.md`
        - `resolved.md`

```
Validate whether critic findings are each semantically distinct from existing gaps in `gaps.md` or `resolved.md`.

For each mapping, you MUST quote specific text from BOTH the finding AND the gap that demonstrates semantic match. If you cannot quote matching text, mark as UNCOVERED.

Example of valid mapping:
- Finding: "Session ID source undefined"
- Gap text: "session_id comes from Claude Code's hook input"
- Match Reason: Both reference session ID sourcing ✓

Example of invalid mapping:
- Finding: "No testing methodology"
- Gap text: "Critic must explicitly declare no issues"
- Match Reason: Finding is about testing hooks, gap is about output format ✗

Respond with findings summary JSON list, e.g. [{"finding": "...", "status": "COVERED", "matched_gaps": ["GAP-12"], "match_reason": "..."}, {"finding": "...", "status": "PARTIAL", "matched_gaps": ["GAP-4"], "match_reason": "..."}, {"finding": "...", "status": "UNCOVERED", "matched_gaps": [], "match_reason": ""}]
```

### C: Document Gaps

1. Get the next available gap ID: `${CLAUDE_PLUGIN_ROOT}/scripts/next_gap.sh openspec/changes/$0`
2. Call a Task tool documentation subagent with the code block below as a prompt:
    - Model: Sonnet
    - Skills: `ce:documenting-systems`, `tokamak:managing-spec-gaps`
    - Pass: critic findings, validation results, next available gap ID
    - Files: `${PROJECT_ROOT}/openspec/changes/$0`
        - `gaps.md`
        - `resolved.md`

```
Merge critic findings into `gaps.md`; use TodoWrite list of each step:
1. Ignore findings that validation marked as fully covered
2. If any findings are PARTIAL status with matching gap in `gaps.md`, either merge it into the existing entry or rework it to be unique
3. If any findings are PARTIAL status with matching gap in `resolved.md`, **DO NOT MODIFY THE RESOLVED GAP ENTRY**, reference the similarity to the `resolved.md` gap in the finding description
4. Merge similar findings across critiques
5. Re-evaluate severity ratings
6. Add each finding as gaps with available IDs to `gaps.md`
  - Include ONLY: Source, Severity, Description
  - Source = kebab-case critic name + `-critic` suffix from the finding heading (e.g., `functional-critic` from "Functional-3: ...", `architecture-accuracy-critic` from "Architecture Accuracy-1: ...")
  - DO NOT set: Triage, Decision (managed by different workflow)
  - Reference spec sections by location, not quotes (spec text is volatile). One concern per gap.
  - Write descriptions as evergreen text: no hard-coded scenario counts, no brittle scenario number references (reference behavior instead), no inline annotations like `[Resolved: ...]`. See tokamak:managing-spec-gaps § Evergreen Writing.
7. Verify `gaps.md` changes
8. Respond with gap changes summary JSON list, e.g. [{"id": 36, "change": "new/update", "description": "what you did"}]
```

3. Save hashes: `python ${CLAUDE_PLUGIN_ROOT}/scripts/select_critics.py openspec/changes/$0 --update-hashes`
