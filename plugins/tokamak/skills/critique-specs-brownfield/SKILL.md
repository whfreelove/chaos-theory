---
name: critique-specs-brownfield
description: Run parallel critics against brownfield documentation artifacts. Validates both internal consistency and accuracy against the actual codebase. Use when validating reverse-engineered documentation from existing code.
---

- Each lettered section **MUST COMPLETE** before the next lettered section
- Create TaskCreate tasks for each lettered section and make it block the section after
- Complete each section after all of its steps are complete
- Each numbered step **MUST COMPLETE** before the next numbered step
- Create TaskCreate tasks for each numbered step, make it block the step after (no prior-step-block for 1), make it blocked by the section before it (no prior-section-block for steps in A), and make it block the section task for the section its in (the last section section-block is not blocked by anything)
- Complete each step task after its work is verified and complete

## Brownfield Documentation Critique Workflow

Brownfield documentation is reverse-engineered from existing code. Critics validate both internal consistency (artifacts agree with each other) and external accuracy (documentation matches what the code actually does). Accuracy critics use Read/Glob/Grep tools to explore the actual codebase.

### A: Critique

1. Ensure `gaps.md` and `resolved.md` exist in `openspec/changes/$0/`. If missing, copy from:
    - `${CLAUDE_PLUGIN_ROOT}/skills/critique-specs/templates/gaps.md`
    - `${CLAUDE_PLUGIN_ROOT}/skills/critique-specs/templates/resolved.md`

2. Run critics in parallel:

    !`python ${CLAUDE_PLUGIN_ROOT}/scripts/run_critics.py openspec/changes/$0`

    If the output shows `critics_run: 0`, skip to section B.

    If any critics failed (check `results` for `status: "error"`), report failures
    to the user and ask whether to proceed with partial results or retry.

    Collect the `output` field from each successful result — these are the critic
    findings for steps 3, B, and C.
3. If gaps with valid statuses (not rejected, deprecated, or superseded) in `gaps.md`, `resolved.md`, or critic findings conflict with each other, resolve the conflict with a user check in via AskUserQuestion; typical options might include rejecting either or both or merging them somehow

   **Project consistency conflicts**: When a project consistency finding conflicts with a change-internal finding, the resolution is typically one of:
   - The change deliberately expands scope — resolution updates the project boundary (at merge time)
   - The change inadvertently conflicts — fix the change artifact
   - The project docs are outdated — note that merge-change will update them

   Present these options to the user alongside reject/merge.

### B: Validation

1. Call a Task tool validation subagent with the code block below as a prompt:
    - Model: Sonnet
    - Pass: critic findings
    - Files: `${PROJECT_ROOT}/openspec/changes/$0`
        - `gaps.md`
        - `resolved.md`
    - Project reference files (if available, read-only):
        - `${PROJECT_ROOT}/<project>/functional.md`
        - `${PROJECT_ROOT}/<project>/technical.md`

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

For project consistency findings, also check if the concern is already acknowledged in project docs
(e.g., in Current Limitations, Known Risks, or Out of Scope). If so, mark as COVERED with the
project doc section as the match source.

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
    - Project reference files (if available, read-only):
        - `${PROJECT_ROOT}/<project>/functional.md`
        - `${PROJECT_ROOT}/<project>/technical.md`

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
7. Verify `gaps.md` changes
8. Respond with gap changes summary JSON list, e.g. [{"id": 36, "change": "new/update", "description": "what you did"}]
```

3. Save hashes: `python ${CLAUDE_PLUGIN_ROOT}/scripts/select_critics.py openspec/changes/$0 --update-hashes`
