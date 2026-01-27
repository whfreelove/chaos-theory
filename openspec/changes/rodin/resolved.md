# Rodin Resolved Gaps

Gaps that have been fully resolved and merged into artifacts.

## Critic Round 2: 2026-01-23

### GAP-50: Leakage detector circular dependency — RESOLVED
- **Category**: unclear
- **Severity**: high
- **Resolution**: Subagent writes directly via Edit tool. PostToolUse fires after append, sets validation=pending. Skill continues to verdict signal, which PostToolUse converts to final validation. Circular behavior is intentional—any edit after skill starts requires re-assessment.
- **Merged into**: design.md (leakage detection section, line ~95)

### GAP-51: sed -i '' macOS-specific syntax — RESOLVED
- **Category**: portability
- **Severity**: high
- **Resolution**: Use platform detection. Check `uname -s` and apply appropriate sed syntax (macOS requires `''`, Linux does not). All `sed -i` calls wrapped in `sed_inplace` helper function.
- **Merged into**: design.md (PostToolUse hook logic)

### GAP-52: cut delimiter truncates validation reason — RESOLVED
- **Category**: bug
- **Severity**: high
- **Resolution**: Change delimiter from `:` to `|`. Format: `<!-- rodin:validation=status|reason|timestamp -->`. Pipe won't appear in reason or timestamp.
- **Merged into**: design.md (embedded metadata format, hook logic), proposal.md, spec.md

### GAP-53: "Why" conflates self-awareness with honesty — RESOLVED
- **Category**: framing
- **Severity**: medium
- **Resolution**: Reframe proposal's "Why" section to focus on blindspots, not intentional hiding. Agents miss gaps due to cognitive limitations, not deception.
- **Merged into**: proposal.md (Why section)

### GAP-54: PostToolUse runs on ALL Write|Edit — RESOLVED
- **Category**: performance
- **Severity**: medium
- **Resolution**: Non-issue. Plan mode can only modify plan files, so path check is defense-in-depth. Early exit is O(1). Documented as acceptable overhead.
- **Merged into**: Acknowledged in gaps.md; no code change needed

### GAP-55: Validator rubric asymmetric (gaming vector) — RESOLVED
- **Category**: risk
- **Severity**: medium
- **Resolution**: Add over-claim check. If gaps count > 2× critic findings count AND critic found <3 issues, validator flags as suspicious with warning (but still passes if coverage met).
- **Merged into**: design.md (coverage determination section)

### GAP-56: No definition of "plan mode" — RESOLVED
- **Category**: documentation
- **Severity**: medium
- **Resolution**: Add brief definition: "Plan mode is Claude Code's planning state (`permission_mode == "plan"`) where the agent creates an implementation plan before taking action. Plan file path is provided in system context. In plan mode, the agent can only modify the plan file."
- **Merged into**: design.md (Goals/Non-Goals section)

### GAP-57: Skill verdict write assumption — RESOLVED
- **Category**: unclear
- **Severity**: medium
- **Resolution**: Non-issue. In plan mode, skill naturally uses Edit tool to write verdict signal. Documented for clarity but not a special requirement.
- **Merged into**: Acknowledged in gaps.md; no code change needed

### GAP-58: Leakage detector merge strategy — RESOLVED
- **Category**: missing
- **Severity**: medium
- **Resolution**: Specify algorithm: Scan gaps block for `/GAP-(\d+)/`, take max ID, increment by 1. If no existing GAPs, start at GAP-1. Append new gaps before `<!-- rodin:gaps:end -->` marker.
- **Merged into**: design.md (leakage detection merge strategy)

## Critic Round 3: 2026-01-23

### GAP-59: No hook testing infrastructure documented — RESOLVED
- **Category**: infrastructure
- **Severity**: high
- **Resolution**: Added "Test Infrastructure" section to design.md specifying: test harness structure (run_tests.sh, fixtures), fixture-based testing pattern, assertion helpers (assert_file_contains, assert_exit_code, assert_output_contains), and subagent mocking strategy. Follows worktree-isolation plugin pattern.
- **Merged into**: design.md (new "Test Infrastructure" section)

### GAP-60: Skill flow undefined for missing Goals/gaps block — RESOLVED
- **Category**: missing
- **Severity**: high
- **Resolution**: Fail fast. Skill fails with clear error message ("Plan must have ## Goals section" or "Plan must have gaps block") and exits. Agent re-invokes skill after fixing.
- **Merged into**: design.md (skill flow steps 1-2), spec.md (scenarios "Missing goals", "Missing gaps block")

### GAP-61: No mock strategy for subagent testing — RESOLVED
- **Category**: infrastructure
- **Severity**: medium
- **Resolution**: Fixture files. Test harness uses `fixtures/subagents/` directory with predetermined JSON responses for each subagent (leakage detector, critic, validator). Tests verify skill orchestration logic without real LLM calls.
- **Merged into**: design.md (Test Infrastructure → Subagent Mocking section)

### GAP-62: No spec-to-test automation guidance — RESOLVED
- **Category**: infrastructure
- **Severity**: medium
- **Resolution**: Test naming convention. Functions named `test_<requirement>_<scenario>` to map directly to spec scenarios. Coverage verified by comparing function names to spec scenario names.
- **Merged into**: design.md (Test Infrastructure → Test Naming Convention section)

## Critic Round 4: 2026-01-23

### GAP-63: Spec scenarios missing GIVEN clauses — RESOLVED
- **Category**: spec-quality
- **Severity**: high
- **Resolution**: Rewrote entire spec.md with proper Gherkin format. All scenarios now have Given-When-Then structure establishing context before action.
- **Merged into**: spec.md (complete rewrite)

### GAP-64: Spec scenarios leak implementation details — RESOLVED
- **Category**: spec-quality
- **Severity**: high
- **Resolution**: Removed references to "haiku-model", "opus-model", "Task tool", "hash computation" from scenarios. Scenarios now describe observable behaviors, not implementation mechanisms.
- **Merged into**: spec.md (complete rewrite)

### GAP-65: PostToolUse hook activation conditions not specified — RESOLVED
- **Category**: spec-coverage
- **Severity**: high
- **Resolution**: Added new requirement "PostToolUse hook activation" with scenarios: "Edit outside plan mode", "Edit non-plan file in plan mode", "Edit plan file in plan mode".
- **Merged into**: spec.md (new requirement section)

### GAP-66: Empty gaps block creates catch-22 — RESOLVED
- **Category**: logic
- **Severity**: medium
- **Resolution**: Modified validator logic: empty gaps block passes if critic also finds no issues. If critic finds issues, fails as expected. Prevents agents from needing to invent defensive gaps.
- **Merged into**: design.md (embedded metadata format section)

### GAP-67: jq returns null on missing JSON fields — RESOLVED
- **Category**: robustness
- **Severity**: medium
- **Resolution**: Added null checks after jq extraction in both hooks. PostToolUse exits silently on null. PreToolUse fails with clear error message.
- **Merged into**: design.md (hook logic sections)

### GAP-68: Spec missing boundary/edge case scenarios — RESOLVED
- **Category**: spec-coverage
- **Severity**: medium
- **Resolution**: User decision: specs cover end-to-end/integration behaviors. Unit-level boundary testing deferred to implementation. Design says "fail closed on parse errors".
- **Merged into**: Acknowledged (no spec change needed)

### GAP-69: Ambiguous data expectations in spec — RESOLVED
- **Category**: spec-clarity
- **Severity**: medium
- **Resolution**: Added Definitions section to spec.md defining: gap-like phrases (with examples), semantic match (with example), verdict signal, validation metadata.
- **Merged into**: spec.md (new Definitions section)

### GAP-70: Missing negative test scenarios — RESOLVED
- **Category**: spec-coverage
- **Severity**: medium
- **Resolution**: Added "Negative scenarios - bypass prevention" requirement with scenarios: agent deletes session marker, agent modifies plan/gaps after assessment, session marker from different session.
- **Merged into**: spec.md (new requirement section)

### GAP-71: PreToolUse hook discovery mechanism not in spec — RESOLVED
- **Category**: spec-coverage
- **Severity**: medium
- **Resolution**: Added "PreToolUse hook plan discovery" requirement with scenarios: plan file found, multiple plan files, no matching plan file.
- **Merged into**: spec.md (new requirement section)

### GAP-72: Hook fixture list incomplete — RESOLVED
- **Category**: test-infrastructure
- **Severity**: medium
- **Resolution**: Expanded fixture list to cover all scenarios: plans (valid, stale hashes, pending/fail verdict, deleted metadata, malformed markers) and inputs (plan mode, non-plan mode, null fields).
- **Merged into**: design.md (Test Infrastructure section)

### GAP-73: Skill test infrastructure missing — RESOLVED
- **Category**: test-infrastructure
- **Severity**: medium
- **Resolution**: Added "Skill Test Infrastructure" section with mock Task tool approach, test pattern example, and skill-specific assertions (assert_task_invoked, assert_invocation_order, assert_verdict_signal).
- **Merged into**: design.md (Test Infrastructure section)

## Critic Round 5: 2026-01-24

### GAP-80: Directory traversal bypass in file path validation — RESOLVED
- **Category**: security
- **Severity**: high
- **Description**: File path validation pattern `[[ "$file_path" != "$HOME/.claude/plans/"*.md ]]` accepts directory traversal paths like `/Users/test/.claude/plans/../../../etc/passwd.md`.
- **Resolution**: Add realpath validation. Use `realpath` to canonicalize path and verify it's under `~/.claude/plans/` before processing.
- **Merged into**: design.md (PostToolUse hook logic)

### GAP-81: Undocumented POSIX commands (cut, uname, head) — RESOLVED
- **Category**: documentation
- **Severity**: high
- **Description**: Hook code uses `cut`, `uname`, and `head` commands extensively but they're not listed in Dependencies table.
- **Resolution**: Acknowledge as implicit. Add note that POSIX builtins/standard utilities are assumed available and not individually documented. Explicit dependency documentation reserved for non-universal tools like `jq`.
- **Merged into**: design.md (Dependencies section)

### GAP-82: jq dependency check not in spec requirements — RESOLVED
- **Category**: spec-coverage
- **Severity**: high
- **Description**: Hooks fail immediately if jq unavailable with user-facing error messages, but spec.md has no scenario testing this behavior.
- **Resolution**: Add spec scenario for missing jq. New requirement "Hook dependency validation" with scenario testing that hooks fail with clear installation guidance when jq is missing.
- **Merged into**: spec.md (new requirement)

### GAP-83: No test strategy for critic content extraction verification — RESOLVED
- **Category**: test-infrastructure
- **Severity**: high
- **Description**: No method to verify gaps block was excluded from content passed to critic. Critical for testing isolation requirement.
- **Resolution**: Add assertion helper `assert_content_excludes <content_var> <pattern>` to verify gaps block is not present in critic input. Test pattern: capture Task tool invocation arguments, assert gaps block markers and content not present.
- **Merged into**: design.md (Test Infrastructure section)

### GAP-84: No integration test strategy for PostToolUse→PreToolUse hash synchronization — RESOLVED
- **Category**: test-infrastructure
- **Severity**: high
- **Description**: Hooks tested in isolation. No guidance on testing state transitions across multiple hook invocations in sequence.
- **Resolution**: Add integration test pattern. Test files that exercise full workflow: initial edit → PostToolUse adds metadata → subsequent edit → PostToolUse updates hashes → ExitPlanMode → PreToolUse validates. Use test orchestrator script that chains hook invocations with state verification between each.
- **Merged into**: design.md (Test Infrastructure section)

### GAP-91: Pipe delimiter parsing issues — RESOLVED
- **Category**: architecture
- **Severity**: medium
- **Description**: Validation reason may contain pipes, breaking cut-based parsing.
- **Resolution**: Switch to JSON format for embedded metadata. Verdict signal and validation metadata now use JSON, parsed with jq.
- **Merged into**: design.md (Embedded Metadata Format, Hook Logic), spec.md (Definitions)

### GAP-92: GAP-N ID pattern matches text references — RESOLVED
- **Category**: logic
- **Severity**: medium
- **Description**: `/GAP-(\d+)/` pattern could match "see GAP-99" in descriptions.
- **Resolution**: Anchor pattern to line start: `/^### GAP-(\d+):/` to match only gap headers.
- **Merged into**: design.md (Leakage detection merge strategy)

### GAP-93: Over-claim check feature complexity — RESOLVED
- **Category**: scope
- **Severity**: medium
- **Description**: Feature to warn on excessive gaps vs findings adds complexity with unclear value.
- **Resolution**: Removed feature. Let critic catch gaming attempts naturally.
- **Merged into**: design.md (removed from Coverage determination section)

### GAP-94: Spec scenarios describe control flow — RESOLVED
- **Category**: spec-quality
- **Severity**: medium
- **Description**: "Plan has goals section" Then clause described internal flow, not behavior.
- **Resolution**: Changed to behavior-focused outcome: "validation passes for goals requirement".
- **Merged into**: spec.md (Goals section validation, Gaps block validation scenarios)

### GAP-95: Spec scenarios leak implementation — RESOLVED
- **Category**: spec-quality
- **Severity**: medium
- **Description**: "appended to gaps block with appropriate severity" exposes implementation.
- **Resolution**: Changed to observable outcome: "the gaps block contains the detected concerns".
- **Merged into**: spec.md (Leakage detection scenario)

### GAP-96: Spec scenario describes mechanism — RESOLVED
- **Category**: spec-quality
- **Severity**: medium
- **Description**: "critic receives plan content excluding gaps block" describes HOW not WHAT.
- **Resolution**: Renamed to "Critic analyzes independently", focused on outcome: "findings are independent of documented gaps".
- **Merged into**: spec.md (Critic analysis scenario)

### GAP-97: jq parse errors not handled — RESOLVED
- **Category**: robustness
- **Severity**: medium
- **Description**: Malformed JSON input to hooks could cause unpredictable behavior.
- **Resolution**: Added JSON validation before parsing: `jq -e . >/dev/null 2>&1` check in both hooks.
- **Merged into**: design.md (PostToolUse and PreToolUse hook logic)

### GAP-98: Validation status not validated — RESOLVED
- **Category**: robustness
- **Severity**: medium
- **Description**: Status extraction didn't verify value is one of expected values.
- **Resolution**: Added case statement with explicit handling for pass/pending/fail and default error.
- **Merged into**: design.md (PreToolUse hook logic)

### GAP-99: Subagent retry fixtures missing — RESOLVED
- **Category**: test-infrastructure
- **Severity**: medium
- **Description**: No fixtures for testing retry logic on malformed/timeout responses.
- **Resolution**: Added critic_malformed.json, critic_timeout.json, validator_malformed.json fixtures and MOCK_TASK_SEQUENCE pattern.
- **Merged into**: design.md (Subagent Mocking section)

### GAP-100: Platform portability testing undefined — RESOLVED
- **Category**: test-infrastructure
- **Severity**: medium
- **Description**: No guidance on testing cross-platform sed behavior.
- **Resolution**: Added Platform Portability Testing section with local/CI/manual verification guidance.
- **Merged into**: design.md (new section before Risks/Trade-offs)

## Gaps.md Cleanup: 2026-01-25

### GAP-38: Validator output format unspecified — RESOLVED
- **Category**: missing
- **Severity**: high
- **Resolution**: Structured markdown format like critic: `### VERDICT: PASS` or `### VERDICT: FAIL`, `**Reason**: <explanation>`. Easy for orchestrating agent to parse.
- **Merged into**: design.md (lines 73-80)

### GAP-15: No API to query permission_mode — RESOLVED
- **Category**: missing
- **Severity**: high
- **Resolution**: Hooks receive `permission_mode` directly in JSON input. PostToolUse hook checks `permission_mode == "plan"` and only runs in plan mode. No workaround needed—Claude Code provides this data.
- **Merged into**: design.md (hook code)

### GAP-19: Fresh agent context transfer unaddressed — RESOLVED (reframed)
- **Category**: unclear
- **Severity**: high
- **Resolution**: Reframed proposal's "why" entirely. The value is adversarial validation forcing honest gap articulation—not cross-session handoff. Removed "fresh agent" framing from proposal and design.
- **Merged into**: proposal.md (Why section uses "blindspots" framing)

### GAP-21: Missing plan-assessment skill spec — RESOLVED
- **Category**: missing
- **Severity**: high
- **Resolution**: The existing spec already covers both skill and hook requirements (lines 1-82 for skill, 84-101 for hook). Updated proposal to list single combined capability `plan-exit-gate` that includes both skill and hook.
- **Merged into**: proposal.md (Capabilities section)

### GAP-13: Hash bypass enables gaming — RESOLVED
- **Category**: risk
- **Severity**: high
- **Resolution**: PreToolUse hook implements "stale = block" policy. Hash mismatch blocks exit with "Re-run /rodin:plan-gate" message. Agent cannot game by making trivial edits—any edit invalidates verdict and requires re-assessment.
- **Merged into**: design.md (stale=block logic in PreToolUse hook)

### GAP-3: Leakage detection too aggressive — RESOLVED
- **Category**: risk
- **Severity**: high
- **Resolution**: Keyword threshold approach: only flag if 3+ distinct gap-like phrases appear. Single phrases pass through (minor slips acceptable, major ones caught by critic). Overzealous matching risk accepted as trade-off—cheap to implement, easy to rip out if it doesn't work in MVP.
- **Merged into**: design.md (line 110, leakage detection section)

### GAP-31: UUID source undefined — RESOLVED
- **Category**: missing
- **Severity**: medium
- **Resolution**: Use `session_id` consistently throughout design. Remove UUID terminology. session_id comes from Claude Code's hook input (not generated by plugin).
- **Merged into**: design.md (throughout)

### GAP-32: Critic output format unspecified — RESOLVED
- **Category**: missing
- **Severity**: medium
- **Resolution**: Critic returns structured markdown: `### FINDING-N: <title>`, `**Severity**: high|medium|low`, `**Description**: ...`. Easy for validator LLM to parse.
- **Merged into**: design.md (Critic output format section)

### GAP-33: Plan file path detection mechanism incomplete — RESOLVED
- **Category**: unclear
- **Severity**: medium
- **Resolution**: Skill prompt instructs agent to extract plan file path from system message (LLM extraction). Claude Code includes plan file path in system context when in plan mode. GAP-28 already acknowledges this platform dependency.
- **Merged into**: design.md (Skill flow step 0)

### GAP-39: No handling for critic finding zero issues — RESOLVED
- **Category**: unclear
- **Severity**: medium
- **Resolution**: Critic prompt must explicitly declare "no gaps found" if none detected. Zero findings without explicit declaration fails. Validator checks for explicit "no issues" statement, not just empty findings list.
- **Merged into**: design.md (Critic output format section)

### GAP-42: Critic prompt content not specified — RESOLVED
- **Category**: missing
- **Severity**: medium
- **Resolution**: Document key prompt elements in design: (1) adversarial role, (2) focus on goals mismatches/blockers/assumptions/risks, (3) structured output format, (4) explicit "no issues" if none found. Full prompt deferred to implementation.
- **Merged into**: design.md (Skill uses Task tool for subagents section)

### GAP-43: Task tool model selection not configurable — RESOLVED
- **Category**: assumption
- **Severity**: medium
- **Resolution**: Verified. Task tool supports `model` parameter with values "sonnet", "opus", "haiku", "inherit". Design correctly specifies model per subagent.
- **Merged into**: design.md (verified assumption)

### GAP-7: No error handling for subagent failure — RESOLVED
- **Category**: missing
- **Severity**: medium
- **Resolution**: Retry once on failure. If subagent times out, crashes, or returns unparseable output, skill retries once. If second attempt fails, fail closed (block exit). User must fix issue or force-exit plan mode via native hotkey.
- **Merged into**: design.md (Skill uses Task tool for subagents section)

### GAP-8: Intent section role unclear — RESOLVED
- **Category**: unclear
- **Severity**: medium
- **Resolution**: Renamed to `## Goals`. Defined as success criteria for the plan. Critic uses Goals to evaluate whether plan achieves stated objectives. Matches common planning conventions.
- **Merged into**: design.md, proposal.md, spec.md (Goals section validation)

### GAP-10: Gaming prevention threat model unstated — RESOLVED
- **Category**: assumption
- **Severity**: medium
- **Resolution**: Documented as defense-in-depth. Not about conspiracy—prevents accidental priming. Critic shouldn't see agent's gap framing before independent analysis. Independent discovery is more valuable than confirming known gaps. Isolation ensures critic finds gaps the agent missed, not just validates gaps agent already documented.
- **Merged into**: design.md (Critic isolation section)

### GAP-16: Semantic coverage threshold undefined — RESOLVED
- **Category**: unclear
- **Severity**: medium
- **Resolution**: Added coverage rubric to design.md: PASS if all HIGH and MEDIUM severity findings covered, FAIL if any HIGH or MEDIUM uncovered. LOW findings deferred by default. Validator errs on side of coverage (benefit of doubt). Updated spec with coverage criteria.
- **Merged into**: design.md (Coverage determination section), spec.md

### GAP-17: External yq dependency unspecified — RESOLVED
- **Category**: assumption
- **Severity**: medium
- **Resolution**: Replaced yq with portable grep-based YAML parsing in design.md hook logic. Uses `grep '^key:' | cut -d' ' -f2` which works on any POSIX system. No external dependencies.
- **Merged into**: design.md (replaced with jq and sed-based parsing)

### GAP-24: Skip bypass can be added by agent — RESOLVED
- **Category**: risk
- **Severity**: medium
- **Resolution**: Removed skip bypass mechanism entirely. No `<!-- RODIN:ASSESSMENT_SKIPPED -->` comment support. Users who need to bypass must use native Claude Code hotkey to force-exit plan mode (outside our control).
- **Merged into**: design.md (no bypass mechanism)

### GAP-25: No file system error handling in hooks — RESOLVED
- **Category**: missing
- **Severity**: medium
- **Resolution**: Fail closed on FS errors. Hook removes `2>/dev/null` suppressions and adds explicit error checks. If hook can't verify (permissions, disk full, etc.), block exit with clear error message. Strict enforcement prevents silent failures.
- **Merged into**: design.md (hook error handling)

### GAP-11: Hook error messages unspecified — RESOLVED
- **Category**: missing
- **Severity**: low
- **Resolution**: Standard message format: `[RODIN] <what failed>: <reason>. To fix: <guidance>`. Human-readable with actionable guidance. Examples in design.md hook code.
- **Merged into**: design.md (hook code examples)

### GAP-12: Performance/timeout unspecified — RESOLVED
- **Category**: missing
- **Severity**: low
- **Resolution**: Use Task tool's default timeout (2 minutes). Sufficient for critic/validator subagents. No custom timeout or env var needed for MVP.
- **Merged into**: design.md (accepted default)

### GAP-34: Critic severity assignment algorithm undefined — RESOLVED
- **Category**: unclear
- **Severity**: low
- **Resolution**: LLM judgment with prompt guidance. Critic prompt instructs: HIGH = blocks implementation, MEDIUM = degrades functionality, LOW = minor issue. Explicit rubrics too rigid for LLM critic.
- **Merged into**: design.md (Critic output format section)

### GAP-35: Hash algorithm not explicitly documented — RESOLVED
- **Category**: missing
- **Severity**: low
- **Resolution**: Accepted as implementation detail. SHA-256 (`shasum -a 256`) is standard, visible in hook code. No need to over-document.
- **Merged into**: design.md (hook code)

### GAP-59: No hook testing infrastructure documented — RESOLVED
- **Category**: infrastructure
- **Severity**: high
- **Resolution**: Added "Test Infrastructure" section to design.md specifying: test harness structure, fixture-based testing pattern, assertion helpers, and subagent mocking strategy. Follows worktree-isolation plugin pattern.
- **Merged into**: design.md (Test Infrastructure section)

### GAP-60: Skill flow undefined for missing Goals/gaps block — RESOLVED
- **Category**: missing
- **Severity**: high
- **Resolution**: Fail fast. Skill fails with clear error message ("Plan must have ## Goals section" or "Plan must have gaps block") and exits. Agent re-invokes skill after fixing. Updated design.md skill flow and spec.md scenarios.
- **Merged into**: design.md (Skill flow steps 1-2), spec.md

### GAP-61: No mock strategy for subagent testing — RESOLVED
- **Category**: infrastructure
- **Severity**: medium
- **Resolution**: Fixture files. Test harness uses `fixtures/subagents/` with predetermined JSON responses (leakage_none.json, critic_findings.json, validator_pass.json, etc.). Tests verify skill orchestration logic without real LLM calls.
- **Merged into**: design.md (Test Infrastructure → Subagent Mocking section)

### GAP-62: No spec-to-test automation guidance — RESOLVED
- **Category**: infrastructure
- **Severity**: medium
- **Resolution**: Test naming convention. Functions named `test_<requirement>_<scenario>` (e.g., `test_goals_section_validation_missing_goals`). Coverage verified by comparing function names to spec scenario names.
- **Merged into**: design.md (Test Infrastructure section)

## Critic Round 6: 2026-01-25

### GAP-101: PostToolUse metadata operations not mentioned in "What Changes" — RESOLVED
- **Category**: documentation
- **Severity**: medium
- **Resolution**: Updated proposal.md "What Changes > Hook: PostToolUse" section with clearer bullet points: session marker injection, hash tracking, verdict signal conversion, validation reset on content change.
- **Merged into**: proposal.md (What Changes section)

### GAP-102: Exit blocking behavior not documented in Impact section — RESOLVED
- **Category**: documentation
- **Severity**: medium
- **Resolution**: Added explicit "Exit is BLOCKED until assessment passes" statement to Impact section.
- **Merged into**: proposal.md (Impact section)

### GAP-103: Goals verification not in "What Changes" section — RESOLVED
- **Category**: documentation
- **Severity**: low
- **Resolution**: Verified already present in proposal.md line 9: "1. Verifies plan has `## Goals` section (success criteria)". Visibility is sufficient - no change needed.
- **Merged into**: N/A (already documented)

### GAP-104: Hook JSON input schema stability not validated — RESOLVED
- **Category**: assumption
- **Severity**: high
- **Resolution**: Added "Hook JSON schema stability assumption" section to design.md Decisions. Updated hook code with defensive parsing using `// empty` fallbacks, clearer null checks, and error messages indicating potential schema changes.
- **Merged into**: design.md (Decisions section, PostToolUse hook code, PreToolUse hook code)

### GAP-105: realpath command unavailable on macOS without coreutils — RESOLVED
- **Category**: portability
- **Severity**: medium
- **Resolution**: Replaced `realpath` with Python-based alternative: `python3 -c "import os; print(os.path.realpath('$file_path'))"`. Python3 is universally available on macOS/Linux.
- **Merged into**: design.md (PostToolUse hook code)

### GAP-106: No justification for shell-based hook implementation — RESOLVED
- **Category**: architecture
- **Severity**: medium
- **Resolution**: Added "Shell vs Python for hooks" decision to design.md documenting trade-offs. MVP uses shell with targeted Python fallbacks; full Python rewrite planned for future to address accumulated portability issues.
- **Merged into**: design.md (Decisions section)

### GAP-107: Missing Background sections for repeated context — RESOLVED
- **Category**: spec-quality
- **Severity**: medium
- **Resolution**: Added Background sections to requirements with repeated Given clauses: Goals section validation, Gaps block validation, PostToolUse hook metadata maintenance, PreToolUse hook enforcement, Negative scenarios - bypass prevention.
- **Merged into**: spec.md (multiple requirements)

### GAP-108: Missing Examples tables for data-driven scenarios — DEFERRED TO FUTURE RELEASE
- **Category**: spec-quality
- **Severity**: low
- **Resolution**: Nice-to-have spec quality improvement. Deferred to future release. Acknowledged in gaps.md with note for post-MVP iteration when implementing parameterized tests.
- **Merged into**: gaps.md (acknowledgment only)

### GAP-109: Leakage detector error handling not specified — RESOLVED
- **Category**: missing
- **Severity**: high
- **Resolution**: Added error handling section to leakage detection in design.md specifying retry-once-then-fail-closed pattern: regex failure defaults to GAP-1, Edit failures retry once then fail, concurrent edits detected by hash mismatch, malformed structure fails closed.
- **Merged into**: design.md (Leakage detection section)

## Critic Round 7: 2026-01-25

### GAP-110: Leakage detector severity assignment undefined — RESOLVED
- **Category**: missing
- **Severity**: medium
- **Description**: Design says leakage detector appends detected gaps "with appropriate severity" but no criteria defined for what severity the leakage detector should assign.
- **Resolution**: Always assign MEDIUM severity. Leakage is inherently ambiguous—not HIGH (not blocking), not LOW (worth noting).
- **Merged into**: design.md (Leakage detection section)

### GAP-111: Verdict signal JSON whitespace handling — RESOLVED
- **Category**: spec-clarity
- **Severity**: low
- **Description**: Verdict signal JSON whitespace handling not explicitly defined.
- **Resolution**: Specify compact JSON format (no whitespace) for consistency.
- **Merged into**: spec.md (Definitions section), design.md (Skill flow step 6)

### GAP-112: Missing scenario IDs in spec — RESOLVED
- **Category**: spec-quality
- **Severity**: high
- **Description**: Spec scenarios lack unique identifiers. Difficult to reference specific scenarios in test coverage reports or gap analysis.
- **Resolution**: Use requirement prefix format: REQ-PEG-001, REQ-PEG-002, etc. Added unique ID to each requirement in spec.md.
- **Merged into**: spec.md (all requirements renamed)

### GAP-113: Leakage detector testability undefined — RESOLVED
- **Category**: test-infrastructure
- **Severity**: high
- **Description**: No scenarios test whether leakage detection mechanism correctly identifies gap-like phrases. No way to validate detection accuracy.
- **Resolution**: Added threshold boundary test scenarios: 2 phrases = no detection, 3 phrases = detection, 5 phrases = detection. Each confirms MEDIUM severity assignment.
- **Merged into**: spec.md (REQ-PEG-004: Leakage detection)

### GAP-114: Hash computation correctness unverifiable — RESOLVED
- **Category**: test-infrastructure
- **Severity**: medium
- **Description**: No spec scenarios verify hash computation is correct. Edge cases like whitespace or encoding could cause mismatches without detection.
- **Resolution**: Documented exactly what content is hashed (after sed extraction, before rodin comment markers). Added reference fixture with known hash value for verification.
- **Merged into**: design.md (Hash maintenance section, Test fixtures)

### GAP-115: Verdict signal conversion timing untestable — RESOLVED
- **Category**: test-infrastructure
- **Severity**: medium
- **Description**: PostToolUse hook converts verdict signal to validation metadata, but no scenario verifies timing or atomicity. Hook failure between read and write could leave inconsistent state.
- **Resolution**: Acknowledged as edge case. Hook failures between signal read and validation write are rare. Documented fail-closed behavior: system blocks exit on failure, user re-runs assessment to recover.
- **Merged into**: design.md (PostToolUse hook section)

### GAP-116: Hash collision handling not addressed — RESOLVED (acknowledged)
- **Category**: edge-case
- **Severity**: low
- **Description**: SHA-256 collision probability is negligible but not zero. No specified behavior if two different plan contents produce same hash.
- **Resolution**: Acknowledged as negligible risk (SHA-256 collision probability ~2^-128). No action needed for MVP.
- **Merged into**: N/A (no change needed)

### GAP-117: E2E test suitability unclear — RESOLVED (acknowledged)
- **Category**: test-infrastructure
- **Severity**: medium
- **Description**: Some spec scenarios require verifying internal state. E2E tests observe external behavior but may not verify internal state without reading plan file contents.
- **Resolution**: Acknowledged MVP limitation. Integration tests with mocked Task tool are sufficient for MVP. Scenarios requiring internal state verification use file assertions.
- **Merged into**: design.md (E2E Testing Future Work section)

### GAP-118: E2E test infrastructure incomplete — RESOLVED (acknowledged)
- **Category**: test-infrastructure
- **Severity**: medium
- **Description**: Design documents unit and integration test infrastructure but no E2E test infrastructure. Gap between integration tests (mocked Task tool) and true E2E tests (real Claude Code environment).
- **Resolution**: Acknowledged MVP limitation. Integration tests with mocked Task tool are sufficient for MVP. True E2E requires Claude Code test harness (future work).
- **Merged into**: design.md (E2E Testing Future Work section)

## Critic Round 8: 2026-01-25

### GAP-119: Critic-to-validator handoff mechanism ambiguous — RESOLVED
- **Category**: unclear
- **Severity**: medium
- **Description**: Design.md line 104 states "Critic findings passed directly critic→validator (by agent)" but the phrase "by agent" is ambiguous. Does the orchestrating agent manually extract and pass findings, or is this automatic via the Task tool's return value? The skill flow (lines 240-246) shows the sequence but doesn't clarify how findings are captured and forwarded. This could lead to implementation confusion.
- **Resolution**: Task tool return - Critic output returned to orchestrating agent, who passes findings to validator via Task tool prompt. Clarify in design.md that this is explicit agent orchestration, not automatic.
- **Merged into**: design.md (Skill uses Task tool for subagents section)

### GAP-122: Verdict signal JSON extraction pattern vulnerable to nested braces — RESOLVED
- **Category**: robustness
- **Severity**: medium
- **Description**: Lines 351-352 and 443 in design.md use `grep -o '<!-- rodin:verdict:signal={[^}]*}'` to extract JSON. The pattern `{[^}]*}` breaks when the `reason` field contains nested braces (e.g., `"reason": "Missing error handling for {retries, timeouts}"`), producing truncated/malformed JSON that jq cannot parse.
- **Resolution**: Replace grep patterns with sed-based extraction. Use `sed -n 's/.*rodin:verdict:signal=\({.*}\).*/\1/p'` which correctly handles nested braces.
- **Merged into**: design.md (PostToolUse and PreToolUse hook code)

### GAP-123: Proposal "Goals to Capabilities" mapping unclear — RESOLVED
- **Category**: documentation
- **Severity**: medium
- **Description**: Proposal's "Why" section establishes goal of "surfacing blindspots" but "Capabilities" section lists `plan-exit-gate` without explaining what specific blindspot-detection capabilities it provides. The connection between the stated problem (agents miss gaps) and the solution (exit gate) requires the reader to infer the mechanism.
- **Resolution**: Add capability descriptions - Expand Capabilities section in proposal.md to explain how each component addresses the blindspots problem.
- **Merged into**: proposal.md (Capabilities section)

### GAP-124: Proposal uses undefined terminology — RESOLVED
- **Category**: documentation
- **Severity**: low
- **Description**: Multiple terms appear in proposal without prior definition: (1) "Leakage detection" mentioned in Step 3 with "3+ gap-like phrases" threshold but never defined, (2) Session marker rationale missing, (3) `permission_mode == 'plan'` referenced but concept not explained.
- **Resolution**: Add brief definitions inline - (1) Define "leakage detection" when first mentioned, (2) Add sentence explaining session marker purpose, (3) Note that permission_mode is a Claude Code concept.
- **Merged into**: proposal.md (What Changes section)

### GAP-125: Leakage detection test scenarios incomplete — RESOLVED
- **Category**: spec-coverage
- **Severity**: medium
- **Description**: REQ-PEG-004 scenarios require verifying "the gaps block contains the detected concerns" after leakage detector runs. Current test infrastructure only provides subagent mocking for Task tool outputs, not Edit tool behavior verification. No documented approach for testing whether leakage detector correctly appends gaps to gaps block.
- **Resolution**: File assertions - After mocked Edit tool call, verify gaps block content with assert_file_contains. Document this approach in test infrastructure section with example test pattern.
- **Merged into**: design.md (Test Infrastructure - Leakage Detection Testing section)

### GAP-126: PostToolUse error handling inconsistency — RESOLVED
- **Category**: robustness
- **Severity**: medium
- **Description**: Design claims "fail-closed on errors" but PostToolUse hook exits silently (no error message, no exit code) on malformed JSON or missing fields. This creates ambiguous failure mode—agent sees no feedback, may assume hook succeeded.
- **Resolution**: Fail-open is correct - Keep silent exit (exit 0) on schema errors. PreToolUse catches missing metadata at exit time. Document this as intentional "fail-open for liveness" behavior, clarifying it's not inconsistent with overall fail-closed philosophy since PreToolUse is the enforcement point.
- **Merged into**: design.md (PostToolUse hook section)

### GAP-129: Subagent retry output format unspecified — RESOLVED
- **Category**: spec-clarity
- **Severity**: low
- **Description**: Spec says "unparseable output" triggers retry but doesn't define what "parseable" means for each subagent. Validator expects `### VERDICT: PASS/FAIL`, critic expects `### FINDING-N`, but no regex patterns or parsing rules documented for retry decision.
- **Resolution**: Add parseable format definitions to design.md - Validator expects `/^### VERDICT: (PASS|FAIL)$/m`, Critic expects `/^### FINDING-\d+:/m` or `/^### NO ISSUES FOUND$/m`. Document regex patterns used for retry decision.
- **Merged into**: design.md (Skill uses Task tool for subagents section)
