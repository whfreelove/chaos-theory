## ADDED Requirements

### Requirement: Skill requires plan mode context
The skill SHALL use the plan file path from system context (LLM extraction) and slug→session_id mapping.

#### Scenario: Plan file path unavailable
- **WHEN** `/rodin:plan-gate` invoked AND plan file path not in system context
- **THEN** skill fails with "Must be invoked in plan mode" error

#### Scenario: No session mapping
- **WHEN** `/rodin:plan-gate` invoked AND `<slug>.session` mapping file does not exist
- **THEN** skill prompts agent to edit plan file first (triggers PostToolUse hook to create mapping)

#### Scenario: Session mapping exists
- **WHEN** `/rodin:plan-gate` invoked AND `<slug>.session` mapping file exists
- **THEN** skill reads session_id from mapping and proceeds with assessment

### Requirement: Goals section validation
The skill SHALL verify the plan contains a Goals section defining success criteria.

#### Scenario: Missing goals
- **WHEN** plan file lacks `## Goals` section
- **THEN** skill prompts agent to add success criteria before continuing

#### Scenario: Goals present
- **WHEN** plan file has `## Goals` section
- **THEN** skill proceeds to gaps check

### Requirement: Gaps file management
The skill SHALL ensure gaps.md exists before assessment.

#### Scenario: Missing gaps file
- **WHEN** `<session_id>.gaps.md` does not exist
- **THEN** skill prompts agent to write known gaps

#### Scenario: Gaps file exists
- **WHEN** `<session_id>.gaps.md` exists
- **THEN** skill proceeds to leakage check

### Requirement: Leakage detection
The skill SHALL use Task tool to run a **haiku-model** subagent for leakage detection before critic.

#### Scenario: Leakage detected
- **WHEN** plan contains 3+ distinct gap-like phrases (hedging language, uncertainty markers)
- **THEN** haiku subagent appends them as gaps to gaps.md with appropriate severity (next available GAP-N ID), then assessment continues

#### Scenario: Below threshold
- **WHEN** plan contains fewer than 3 gap-like phrases
- **THEN** skill proceeds to critic (minor slips acceptable, critic catches major gaps)

### Requirement: Critic subagent assessment
The skill SHALL use Task tool to run an **opus-model** critic subagent that finds gaps in the plan.

#### Scenario: Critic execution
- **WHEN** leakage check passes
- **THEN** skill runs critic via Task tool with plan content as input (NOT gaps.md—critic must find gaps independently)

#### Scenario: Critic focus
- **WHEN** critic evaluates the plan
- **THEN** it reports gaps: goals mismatches, implementation blockers, unstated assumptions, unmitigated risks

### Requirement: Validator subagent coverage check
The skill SHALL use Task tool to run a **haiku-model** validator subagent that checks coverage.

#### Scenario: Validator execution
- **WHEN** critic returns findings
- **THEN** skill runs validator via Task tool with gaps + findings as input

#### Scenario: Coverage determination
- **WHEN** validator evaluates gaps vs findings
- **THEN** it applies coverage rubric: PASS if all HIGH and MEDIUM findings covered, FAIL if any HIGH or MEDIUM uncovered (LOW deferred)

#### Scenario: Benefit of doubt
- **WHEN** a gap plausibly addresses a finding (semantic match)
- **THEN** validator counts it as covered

#### Scenario: Validator output format
- **WHEN** validator completes coverage check
- **THEN** it outputs `### VERDICT: PASS` or `### VERDICT: FAIL` with `**Reason**: <explanation>`

#### Scenario: Critic finds no issues
- **WHEN** critic analysis finds no gaps in the plan
- **THEN** critic outputs `### NO ISSUES FOUND` (explicit declaration required, not empty output)

### Requirement: Subagent error handling
The skill SHALL retry failed subagents once before failing closed.

#### Scenario: Subagent failure
- **WHEN** leakage detector, critic, or validator times out, crashes, or returns unparseable output
- **THEN** skill retries the subagent once

#### Scenario: Retry failure
- **WHEN** second attempt also fails
- **THEN** skill fails closed (blocks exit, user must fix issue or force-exit via native hotkey)

### Requirement: Verdict file
The skill SHALL write verdict to gate.yml. PostToolUse hook maintains hashes.

#### Scenario: Write verdict
- **WHEN** validator subagent returns verdict
- **THEN** skill sets status and reason in gate.yml (hashes already maintained by PostToolUse hook)

#### Scenario: Pass verdict
- **WHEN** validator determines gaps cover findings
- **THEN** gate.yml status is "pass"

#### Scenario: Fail verdict
- **WHEN** validator finds uncovered gaps
- **THEN** gate.yml status is "fail" with reason listing uncovered findings

### Requirement: PostToolUse hook maintains state
The PostToolUse hook SHALL maintain gate.yml hashes and reset status on edits.

#### Scenario: Plan file edited
- **WHEN** agent edits plan file in plan mode
- **THEN** hook updates plan_hash and resets status to "pending"

#### Scenario: Gaps file edited
- **WHEN** agent edits gaps.md
- **THEN** hook updates gaps_hash and resets status to "pending"

#### Scenario: Session isolation
- **WHEN** hook detects gaps.md edit
- **THEN** hook uses session_id from filename (not session_id from input) to find correct gate.yml

### Requirement: Hook enforces verdict
The hook SHALL check gate.yml on ExitPlanMode.

#### Scenario: No gate file
- **WHEN** ExitPlanMode called AND gate.yml does not exist
- **THEN** hook blocks with prompt to run `/rodin:plan-gate`

#### Scenario: Stale verdict
- **WHEN** ExitPlanMode called AND plan or gaps hash doesn't match gate.yml
- **THEN** hook blocks with prompt to re-run `/rodin:plan-gate`

#### Scenario: File system error
- **WHEN** ExitPlanMode called AND hook cannot read plan file or gaps file
- **THEN** hook blocks with error message (fail closed)

#### Scenario: Gaps file referenced but missing
- **WHEN** ExitPlanMode called AND gate.yml has gaps_file path AND file does not exist
- **THEN** hook blocks with "Gaps file referenced but missing" error

#### Scenario: Valid pass verdict
- **WHEN** ExitPlanMode called AND hashes match AND status is "pass"
- **THEN** hook allows exit

#### Scenario: Valid fail verdict
- **WHEN** ExitPlanMode called AND hashes match AND status is "fail"
- **THEN** hook blocks with reason from gate.yml
