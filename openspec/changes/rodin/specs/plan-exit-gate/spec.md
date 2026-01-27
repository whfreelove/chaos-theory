## Definitions

**Gap-like phrases**: Language indicating uncertainty, unresolved decisions, or acknowledged risks. Examples include:
- Uncertainty markers: "unclear", "not sure", "might fail", "need to investigate"
- Deferral markers: "TODO", "TBD", "to be determined", "later"
- Risk language: "risk of", "potential issue", "may not work"
- Assumption language: "assuming", "if this works", "hopefully"

**Semantic match**: A gap addresses a finding when both reference the same concern, even if phrased differently. Example: finding "No database rollback strategy" matches gap "Migration failure recovery undefined". The validator applies benefit of doubt—if plausibly related, it counts as covered.

**Verdict signal**: Temporary JSON comment `<!-- rodin:verdict:signal={"status":"...","reason":"..."} -->` written by skill, converted to validation metadata by hook. Uses compact (minified) JSON format with no whitespace for consistency.

**Validation metadata**: Persistent JSON comment `<!-- rodin:validation={"status":"...","reason":"...","ts":"..."} -->` recording assessment outcome. Uses compact JSON format. Parsed with jq.

---

## ADDED Requirements

### REQ-PEG-001: Skill requires plan mode context

The skill SHALL require plan mode context to function.

#### Scenario: Skill invoked outside plan mode

- **Given** the agent is not in plan mode
- **When** the agent invokes `/rodin:plan-gate`
- **Then** the skill fails with "Must be invoked in plan mode" error

#### Scenario: Skill invoked in plan mode

- **Given** the agent is in plan mode with a plan file
- **When** the agent invokes `/rodin:plan-gate`
- **Then** the skill proceeds with assessment using that plan file

### REQ-PEG-002: Goals section validation

The skill SHALL verify the plan contains a Goals section.

#### Background

- **Given** the agent is in plan mode with a plan file

#### Scenario: Plan missing goals section

- **Given** the plan file lacks a `## Goals` section
- **When** the skill validates the plan structure
- **Then** the skill fails with "Plan must have ## Goals section"
- **And** assessment stops immediately

#### Scenario: Plan has goals section

- **Given** the plan file has a `## Goals` section
- **When** the skill validates the plan structure
- **Then** validation passes for goals requirement

### REQ-PEG-003: Gaps block validation

The skill SHALL verify the plan contains a gaps block.

#### Background

- **Given** the agent is in plan mode with a plan file

#### Scenario: Plan missing gaps block

- **Given** the plan file lacks `<!-- rodin:gaps:start -->` and `<!-- rodin:gaps:end -->` markers
- **When** the skill validates the plan structure
- **Then** the skill fails with "Plan must have gaps block"
- **And** assessment stops immediately

#### Scenario: Plan has gaps block

- **Given** the plan file has gaps block markers
- **When** the skill validates the plan structure
- **Then** validation passes for gaps block requirement

#### Scenario: Plan has empty gaps block

- **Given** the plan file has gaps block markers but no gap entries
- **When** the skill validates the plan structure
- **Then** the skill proceeds with assessment
- **And** any critic findings will be marked as uncovered

### REQ-PEG-004: Leakage detection

The skill SHALL detect gap-like phrases in plan content before critic analysis.

#### Scenario: Multiple gap-like phrases detected

- **Given** a plan containing 3 or more distinct gap-like phrases outside the gaps block
- **When** the leakage detector analyzes the plan
- **Then** the gaps block contains the detected concerns

#### Scenario: Few gap-like phrases detected

- **Given** a plan containing fewer than 3 gap-like phrases
- **When** the leakage detector analyzes the plan
- **Then** the skill proceeds to critic analysis without modification

#### Scenario: Threshold boundary - 2 phrases (no detection)

- **Given** a plan containing exactly 2 distinct gap-like phrases outside the gaps block
- **When** the leakage detector analyzes the plan
- **Then** the skill proceeds to critic analysis without modification
- **And** no gaps are appended to the gaps block

#### Scenario: Threshold boundary - 3 phrases (detection triggered)

- **Given** a plan containing exactly 3 distinct gap-like phrases outside the gaps block
- **When** the leakage detector analyzes the plan
- **Then** the gaps block contains all 3 detected concerns
- **And** each detected gap has MEDIUM severity

#### Scenario: Above threshold - 5 phrases (detection triggered)

- **Given** a plan containing 5 distinct gap-like phrases outside the gaps block
- **When** the leakage detector analyzes the plan
- **Then** the gaps block contains all 5 detected concerns
- **And** each detected gap has MEDIUM severity

### REQ-PEG-005: Critic analysis

The skill SHALL run adversarial analysis to find gaps in the plan.

#### Scenario: Critic analyzes independently

- **Given** a plan file with documented gaps
- **When** the critic analyzes the plan
- **Then** critic findings are independent of previously documented gaps

#### Scenario: Critic identifies gaps

- **Given** a plan with implementation risks or unstated assumptions
- **When** the critic analyzes the plan
- **Then** the critic reports findings with severity levels
- **And** findings include goals mismatches, blockers, assumptions, and risks

#### Scenario: Critic finds no issues

- **Given** a comprehensive plan with no gaps
- **When** the critic analyzes the plan
- **Then** the critic explicitly declares no issues found

### REQ-PEG-006: Validator coverage check

The skill SHALL validate that documented gaps cover critic findings.

#### Scenario: All findings covered

- **Given** critic findings and a gaps block
- **When** the validator checks coverage
- **Then** the validator reports PASS if all HIGH and MEDIUM findings have corresponding gaps

#### Scenario: Findings uncovered

- **Given** critic findings with HIGH or MEDIUM severity
- **When** the validator finds no corresponding gap for a finding
- **Then** the validator reports FAIL with the uncovered findings listed

#### Scenario: Semantic matching

- **Given** a gap that plausibly addresses a critic finding
- **When** the validator evaluates coverage
- **Then** the validator counts it as covered

#### Scenario: Low severity findings deferred

- **Given** critic findings with only LOW severity uncovered
- **When** the validator checks coverage
- **Then** the validator reports PASS

### REQ-PEG-007: Subagent error handling

The skill SHALL handle subagent failures gracefully.

#### Scenario: Subagent fails once

- **Given** a subagent that times out or returns unparseable output
- **When** the skill detects the failure
- **Then** the skill retries the subagent once

#### Scenario: Subagent fails twice

- **Given** a subagent that fails on retry
- **When** the second attempt also fails
- **Then** the skill fails closed and blocks plan mode exit

### REQ-PEG-008: Verdict signal

The skill SHALL write verdict outcome to the plan file.

#### Scenario: Assessment passes

- **Given** the validator determines all findings are covered
- **When** the skill completes assessment
- **Then** a pass verdict signal is written to the plan file

#### Scenario: Assessment fails

- **Given** the validator finds uncovered findings
- **When** the skill completes assessment
- **Then** a fail verdict signal is written with uncovered findings listed

### REQ-PEG-009: PostToolUse hook activation

The hook SHALL only run in appropriate contexts.

#### Scenario: Edit outside plan mode

- **Given** the agent is not in plan mode
- **When** the agent edits any file
- **Then** the hook does not run

#### Scenario: Edit non-plan file in plan mode

- **Given** the agent is in plan mode
- **When** the agent edits a file outside `~/.claude/plans/`
- **Then** the hook does not run

#### Scenario: Edit plan file in plan mode

- **Given** the agent is in plan mode
- **When** the agent edits a file in `~/.claude/plans/`
- **Then** the hook runs and maintains metadata

### REQ-PEG-010: PostToolUse hook metadata maintenance

The hook SHALL maintain embedded metadata in plan files.

#### Background

- **Given** the agent is in plan mode
- **And** the agent edits a file in `~/.claude/plans/`

#### Scenario: First edit adds session marker

- **Given** the plan file lacks a session marker
- **When** the hook processes the edit
- **Then** the hook injects a session marker at end of file

#### Scenario: Edit updates hashes

- **Given** the plan file has rodin metadata
- **When** the hook processes the edit
- **Then** the hook recomputes and updates plan and gaps hashes

#### Scenario: Verdict signal converted

- **Given** the plan file contains a verdict signal
- **When** the hook processes the edit
- **Then** the signal is converted to validation metadata with timestamp
- **And** the signal comment is removed

#### Scenario: Content change resets validation

- **Given** the plan file lacks a verdict signal
- **When** the hook processes the edit
- **Then** validation status is set to pending

### REQ-PEG-011: PreToolUse hook enforcement

The hook SHALL enforce assessment verdict on ExitPlanMode.

#### Background

- **Given** the agent attempts to exit plan mode

#### Scenario: No session marker found

- **Given** no plan file contains a session marker for the current session
- **Then** the hook blocks with prompt to run `/rodin:plan-gate`

#### Scenario: Plan content changed since assessment

- **Given** a plan file exists with the current session marker
- **And** the current plan content hash differs from recorded hash
- **Then** the hook blocks with "Plan content changed" message

#### Scenario: Gaps changed since assessment

- **Given** a plan file exists with the current session marker
- **And** the current gaps hash differs from recorded hash
- **Then** the hook blocks with "Gaps changed" message

#### Scenario: Valid pass verdict

- **Given** a plan file exists with the current session marker
- **And** hashes match and validation status is pass
- **Then** the hook allows exit

#### Scenario: Pending verdict

- **Given** a plan file exists with the current session marker
- **And** validation status is pending
- **Then** the hook blocks with prompt to run `/rodin:plan-gate`

#### Scenario: Valid fail verdict

- **Given** a plan file exists with the current session marker
- **And** hashes match and validation status is fail
- **Then** the hook blocks with the failure reason

#### Scenario: Missing metadata

- **Given** a plan file exists with the current session marker
- **And** rodin metadata comments are missing from the plan file
- **Then** the hook blocks and treats it as no assessment

### REQ-PEG-012: PreToolUse hook plan discovery

The hook SHALL locate the plan file for the current session.

#### Scenario: Plan file found by session marker

- **Given** a plan file in `~/.claude/plans/` contains the current session marker
- **When** the hook searches for the plan file
- **Then** the hook uses that file for validation

#### Scenario: Multiple plan files exist

- **Given** multiple plan files exist in `~/.claude/plans/`
- **And** only one contains the current session marker
- **When** the hook searches for the plan file
- **Then** the hook uses the file with matching session marker

#### Scenario: No matching plan file

- **Given** no plan file in `~/.claude/plans/` contains the current session marker
- **When** the hook searches for the plan file
- **Then** the hook blocks with "No assessment found" message

### REQ-PEG-013: Empty gaps block handling

The validator SHALL handle empty gaps blocks appropriately.

#### Scenario: Empty gaps and critic finds no issues

- **Given** a plan with an empty gaps block
- **And** the critic declares no issues found
- **When** the validator checks coverage
- **Then** the validator reports PASS

#### Scenario: Empty gaps but critic finds issues

- **Given** a plan with an empty gaps block
- **And** the critic reports HIGH or MEDIUM findings
- **When** the validator checks coverage
- **Then** the validator reports FAIL with all findings uncovered

### REQ-PEG-014: Negative scenarios - bypass prevention

The system SHALL prevent common bypass attempts.

#### Background

- **Given** a plan file with valid passing assessment

#### Scenario: Agent deletes session marker

- **When** the agent deletes the session marker comment
- **And** the agent attempts to exit plan mode
- **Then** the PreToolUse hook blocks exit with "No assessment found"

#### Scenario: Agent modifies plan after assessment

- **When** the agent edits plan content
- **Then** the PostToolUse hook resets validation to pending
- **And** the PreToolUse hook blocks exit until re-assessment

#### Scenario: Agent modifies gaps after assessment

- **When** the agent modifies the gaps block
- **Then** the PostToolUse hook updates gaps hash
- **And** the PreToolUse hook blocks exit due to hash mismatch

#### Scenario: Session marker from different session

- **Given** the plan file has a session marker from a previous session
- **When** the agent attempts to exit plan mode in a new session
- **Then** the hook blocks because session markers don't match

### REQ-PEG-015: Hook dependency validation

The hooks SHALL validate required dependencies are available.

#### Scenario: jq not installed

- **Given** a system without jq installed
- **When** either hook attempts to run
- **Then** the hook fails with error message containing "jq required"
- **And** the error message includes installation guidance for macOS and Linux
