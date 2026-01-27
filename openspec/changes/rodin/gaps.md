# Rodin Gaps Analysis

Architecture changed to embedded metadata on 2026-01-23. See "Architecture Change" section at end of file.

## Critic Round 2: 2026-01-23

See `resolved.md` for GAP-50 through GAP-58 (all resolved and merged into artifacts).

## Architecture Change: Embedded Metadata (2026-01-23)

Redesigned to embed all rodin state in plan file as HTML comments. No external files.

### GAP-36: Race condition between PostToolUse and skill — RESOLVED (acknowledged)
- **Category**: risk
- **Severity**: medium
- **Resolution**: Edge case that shouldn't occur if agent follows flow correctly—nothing else should be happening during validation. Skill atomically writes verdict after subagent chain completes. Agent shouldn't edit files mid-assessment.

### GAP-40: Gaps merge conflict potential — RESOLVED (acknowledged)
- **Category**: risk
- **Severity**: medium
- **Resolution**: Edge case—shouldn't happen if agent follows flow. Leakage detector runs before agent edits gaps.md. Sequential execution assumed. No locking for MVP.

### GAP-44: Empty plan scenario not handled — RESOLVED (acknowledged)
- **Category**: risk
- **Severity**: medium
- **Resolution**: Accepted as edge case. Critic should catch trivial plans as lacking substance. Low-effort gaming isn't the threat model—plugin targets agents/users who want gap discipline.

### GAP-20: Opt-in circularity unacknowledged — RESOLVED (acknowledged)
- **Category**: risk
- **Severity**: medium
- **Resolution**: Added explicit acknowledgment in design.md. This is an intentional trade-off: forcing assessment would be intrusive. Plugin targets users/agents who want gap discipline, not those who need to be forced. Future work noted for automated invocation option.

### GAP-22: Leakage detection may false-positive — RESOLVED (acknowledged)
- **Category**: risk
- **Severity**: low
- **Resolution**: Accepted trade-off. 3+ keyword threshold may false-positive on cautious plans. Cheap to implement, easy to remove. Critic catches real gaps regardless.

### GAP-23: session_id stability not guaranteed — RESOLVED (acknowledged)
- **Category**: assumption
- **Severity**: high
- **Resolution**: Accepted as MVP limitation. Platform dependency outside our control. If session_id changes, user re-runs assessment. Error messages guide recovery.

### GAP-28: Skill depends on plan file path in system context — RESOLVED (acknowledged)
- **Category**: assumption
- **Severity**: high
- **Resolution**: Accepted as MVP limitation. Platform dependency—skill requires plan mode context. If unavailable, skill fails with clear error "Must be invoked in plan mode". No fallback heuristics.

### GAP-29: Critic isolation is soft constraint — RESOLVED (acknowledged)
- **Category**: assumption
- **Severity**: medium
- **Resolution**: Accepted as defense-in-depth. Critic receives plan content via Task tool input, but has full tool access and could read plan file (which now contains gaps block). Embedded architecture makes isolation *weaker* than separate gaps.md file. See GAP-48. Realistic threat is accidental priming, not adversarial critic. Soft isolation accepted for MVP.

### GAP-45: Sed pattern fragility for content extraction — ACKNOWLEDGED
- **Category**: risk
- **Severity**: medium
- **Resolution**: Sed patterns extract plan content and gaps block. Edge cases (nested comments, malformed markers) may cause incorrect extraction. Fail closed on parse errors. Accepted as MVP limitation—patterns work for expected input format.

### GAP-46: HTML comment rendering varies by viewer — ACKNOWLEDGED
- **Category**: risk
- **Severity**: low
- **Resolution**: HTML comments won't render in most markdown viewers (GitHub, VS Code). Some viewers may show them. Accepted trade-off—metadata at end of file minimizes visual impact.

### GAP-47: Session discovery via grep scales linearly — ACKNOWLEDGED
- **Category**: risk
- **Severity**: low
- **Resolution**: PreToolUse hook greps all plan files to find session marker. O(n) where n = number of plan files. Acceptable for typical usage (few plan files). If performance becomes issue, could add caching layer.

### GAP-48: Critic isolation weaker in embedded architecture — ACKNOWLEDGED
- **Category**: risk
- **Severity**: medium
- **Resolution**: Previous design had gaps in separate file (critic would have to know to look for it). New design has gaps in plan file—if critic reads plan file for context, gaps are visible. Skill passes extracted content (excluding gaps) via Task tool input, but critic has full tool access and could read the file. Accepted trade-off: embedded architecture benefits (no external state, plan mode compatibility) outweigh weaker isolation. Realistic threat remains accidental priming, not adversarial critic.

### GAP-49: Obsolete gaps from previous architecture — RESOLVED
- **Category**: cleanup
- **Severity**: n/a
- **Resolution**: Several gaps no longer applicable due to embedded architecture:
  - GAP-5 (slug→session mapping): Now uses session marker in plan file
  - GAP-14 (artifact path inconsistency): No external artifacts
  - GAP-18 (artifact cleanup): Metadata dies with plan file
  - GAP-37 (gate.yml parsing): No gate.yml, but similar sed concerns covered by GAP-45
  - GAP-41 (gaps.md deleted): Now about deleted rodin comments—fail closed

## Critic Round 4: 2026-01-23

See `resolved.md` for GAP-63 through GAP-73 (HIGH and MEDIUM resolved and merged into artifacts).

### GAP-74: Multi-session marker handling unclear — ACKNOWLEDGED
- **Category**: edge-case
- **Severity**: low
- **Description**: What happens if a plan file is edited across multiple sessions? Current design: new session marker injected if missing, but if existing marker from different session, it remains unchanged.
- **Resolution**: Edge case. Plan files are typically single-session. If user opens old plan in new session, they should re-run assessment anyway. Behavior is acceptable: old session can't exit (no matching marker), new session can't exit (no marker for it). User re-runs `/rodin:plan-gate`.

### GAP-75: Scenario titles use technical terms — ACKNOWLEDGED
- **Category**: spec-style
- **Severity**: low
- **Description**: Some scenario titles like "Critic isolation" and "Hash update" describe implementation concepts rather than user-visible behavior.
- **Resolution**: Acceptable for technical spec. These are behavioral specs for implementers, not user stories. Clarity over marketing polish.

### GAP-76: No-op sed pattern in hash extraction — ACKNOWLEDGED
- **Category**: code-quality
- **Severity**: low
- **Description**: PreToolUse hook has `| sed 's/ -->//'` that does nothing because grep already stopped before `>`. Harmless but confusing.
- **Resolution**: Minor code cleanup. Can be removed during implementation. Does not affect correctness—just redundant.

### GAP-77: Session marker injection adds blank line — ACKNOWLEDGED
- **Category**: cosmetic
- **Severity**: low
- **Description**: PostToolUse hook adds `echo ""` before session marker, creating a blank line. Cosmetic issue in plan file formatting.
- **Resolution**: Acceptable. Blank line separates plan content from rodin metadata. Minor cosmetic preference. Can adjust during implementation if desired.

### GAP-78: Goals section content not validated — ACKNOWLEDGED
- **Category**: edge-case
- **Severity**: low
- **Description**: Skill checks for `## Goals` heading but not whether section contains meaningful content. Empty Goals section passes validation.
- **Resolution**: Let critic catch it. Adversarial review should flag plans with empty or trivial Goals as lacking substance. Adding content validation would be scope creep—critic is the quality gate.

### GAP-79: Error condition fixtures incomplete — ACKNOWLEDGED
- **Category**: test-infrastructure
- **Severity**: low
- **Description**: Fixture list includes malformed_markers.md but not other error conditions like invalid hash format or multiple session markers.
- **Resolution**: Sufficient for MVP. Core error scenarios covered. Additional error fixtures can be added during implementation if needed. Test harness supports adding new fixtures easily.

## Critic Round 5: 2026-01-24

### GAP-85: Date command portability — ACKNOWLEDGED
- **Category**: implementation
- **Severity**: low
- **Description**: `date -u +%Y-%m-%dT%H:%M:%SZ` format assumed portable across macOS/Linux.
- **Resolution**: Implementation detail. Format is ISO 8601 standard, works on both platforms.

### GAP-86: Plan size limits — ACKNOWLEDGED
- **Category**: implementation
- **Severity**: low
- **Description**: No limit on plan content size passed to critic.
- **Resolution**: Practical limit from Task tool context. Extremely large plans will fail naturally.

### GAP-87: file_path fallback mechanism — ACKNOWLEDGED
- **Category**: design
- **Severity**: low
- **Description**: PostToolUse uses `.tool_input.file_path // .tool_response.filePath` fallback.
- **Resolution**: Documented in design. Handles Write vs Edit tool schema differences.

### GAP-88: Empty vs deleted gaps block indistinguishable — ACKNOWLEDGED
- **Category**: design
- **Severity**: low
- **Description**: Both produce same hash. PreToolUse can't detect deleted markers.
- **Resolution**: Fail closed behavior covers both cases. If markers deleted, validation fails.

### GAP-89: Empty directory glob fails — ACKNOWLEDGED
- **Category**: implementation
- **Severity**: low
- **Description**: `*.md` glob with no files causes grep error instead of "No assessment found".
- **Resolution**: Error message still blocks exit. Minor UX issue for rare edge case.

### GAP-90: Verdict signal orphaning — ACKNOWLEDGED
- **Category**: edge-case
- **Severity**: low
- **Description**: If skill crashes after writing signal but before hook runs, signal orphaned.
- **Resolution**: Subsequent edit triggers PostToolUse which handles orphaned signals.

## Critic Round 6: 2026-01-25

See `resolved.md` for GAP-101 through GAP-109 (all resolved and merged into artifacts, except GAP-108 deferred to future release).

### GAP-108: Missing Examples tables for data-driven scenarios — DEFERRED TO FUTURE RELEASE
- **Category**: spec-quality
- **Severity**: low
- **Description**: Several scenarios test variations of same behavior (e.g., different validation statuses, different file path patterns). Could use Gherkin Scenario Outline with Examples table for clarity.
- **Decision**: Defer to future release
- **Rationale**: Nice-to-have spec quality improvement. Not blocking MVP. Can be added when scenarios need parameterized testing.
- **Status**: Acknowledged. Will be addressed in post-MVP iteration when implementing parameterized tests.

## Implicit Gap Detection: 2026-01-25

### GAP-120: Test fixture maintenance strategy undefined — ACKNOWLEDGED (defer-release)
- **Category**: test-infrastructure
- **Severity**: low
- **Description**: Design.md describes fixture files for subagent mocking (lines 523-536) but provides no guidance on maintaining fixtures when subagent output formats change. If critic or validator output format evolves (e.g., new fields, format changes), fixtures may silently become stale. No version tagging or validation mechanism documented.
- **Resolution**: Defer to future release - Fixture versioning is nice-to-have, not blocking MVP.
- **Source**: design.md lines 523-536

### GAP-121: Hash-missing-but-validation-present scenario not covered — ACKNOWLEDGED (defer-release)
- **Category**: spec-coverage
- **Severity**: low
- **Description**: Spec.md REQ-PEG-011 scenario "Missing metadata" covers missing rodin metadata, but doesn't distinguish between partial metadata states. If a plan file has session marker and validation=pass but both hash comments are missing (deleted or corrupted), the behavior is undefined. PreToolUse hook code would fail on hash comparison, but no explicit scenario documents this edge case.
- **Resolution**: Defer to future release - Edge case covered by fail-closed behavior; explicit scenario can be added post-MVP.
- **Source**: spec.md REQ-PEG-011

## Critic Round 7: 2026-01-25

See `resolved.md` for GAP-110 through GAP-118 (all resolved and merged into artifacts).

## Critic Round 8: 2026-01-25

### GAP-127: Spec missing leakage merge strategy scenarios — ACKNOWLEDGED (defer-release)
- **Category**: spec-coverage
- **Severity**: low
- **Description**: Design.md describes detailed GAP-N ID increment logic (scan existing gaps, find max ID, increment by 1) but spec.md has no scenarios covering append-to-existing vs first-gap vs concurrent-edit cases. REQ-PEG-004 only tests detection threshold, not merge behavior.
- **Resolution**: Defer to future release - Design documents merge strategy; spec can be expanded post-MVP.
- **Source**: spec.md REQ-PEG-004, design.md Leakage detection merge strategy
- **Related**: GAP-58 (merge strategy resolved in design)

### GAP-128: Spec missing critic isolation verification scenario — ACKNOWLEDGED (defer-release)
- **Category**: spec-coverage
- **Severity**: low
- **Description**: Design.md documents that gaps block is excluded from critic's Task tool input, but spec.md has no scenario verifying this isolation. No test approach for confirming gaps block is stripped from content before passing to critic subagent.
- **Resolution**: Defer to future release - Design documents isolation approach with assert_content_excludes; spec can be expanded post-MVP.
- **Source**: spec.md (missing scenario), design.md Critic isolation section
- **Related**: GAP-83 (test strategy documented in design)

### GAP-130: Missing jq dependency test scenario — ACKNOWLEDGED (defer-release)
- **Category**: spec-coverage
- **Severity**: low
- **Description**: REQ-PEG-015 (now in resolved.md GAP-82) requires testing jq availability but no scenario documents what happens when jq missing. No approach for testing error message quality or installation guidance.
- **Resolution**: Defer to future release - REQ-PEG-015 documents the requirement; test scenario is implementation detail.
- **Source**: spec.md (scenario gap), resolved.md GAP-82
- **Related**: GAP-82 (resolved in spec)

## RESOLVED (No Longer Applicable)

| Original | Resolution |
|----------|------------|
| GAP-1: Hooks can't spawn subagents | Design pivoted to skill-based approach |
| GAP-2: Coverage algorithm undefined | Validator uses LLM semantic judgment |
| GAP-4: "Lazy init" contradiction | Rewritten - skill prompts, doesn't lazy-init |
| GAP-6: Confidence scoring undefined | Removed from design entirely |
| GAP-9: Subagent A prompt inconsistency | Critic focus now aligned across artifacts |
| GAP-5: Plan file discovery | Embedded architecture uses session marker grep |
| GAP-14: Artifact path inconsistency | No external artifacts in embedded architecture |
| GAP-18: No artifact cleanup policy | Metadata embedded in plan file, dies with it |
| GAP-26: Gaps.md must be created after plan edit | Workflow requirement documented in skill flow |
| GAP-27: Skip bypass requires gate.yml to exist | Skip bypass mechanism removed (GAP-24) |
| GAP-30: Design line 69 contradicts hook behavior | Fixed design.md to match hook blocking behavior |
| GAP-37: Gate.yml parsing fragility | No gate.yml; sed concerns covered by GAP-45 |
| GAP-41: gaps.md deleted behavior | Now about deleted rodin comments—fail closed |
