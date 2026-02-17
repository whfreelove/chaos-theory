`@pre-tool-hook`
# Feature: pre-tool-hook

The PreToolUse hook fires on ExitPlanMode. It discovers the plan file by session marker,
verifies content integrity via hash comparison, and enforces the assessment verdict before
allowing the agent to exit plan mode. The hook fails closed — any unexpected state blocks exit.

---

`@pre-tool-hook:1`
## Rule: Enforcement logic

### Background

- Given the agent attempts to exit plan mode

### Scenario: No session marker found — blocks exit

- Given no plan file contains a session marker for the current session
- Then the hook blocks with prompt to run `/rodin:plan-gate`

### Scenario: Plan content changed since assessment — blocks exit

- Given a plan file exists with the current session marker
- And the current plan content hash differs from the recorded hash
- Then the hook blocks with "Plan content changed since assessment" message

### Scenario: Gaps changed since assessment — blocks exit

- Given a plan file exists with the current session marker
- And the current gaps hash differs from the recorded hash
- Then the hook blocks with "Gaps changed since assessment" message

### Scenario: Valid pass verdict — allows exit

- Given a plan file exists with the current session marker
- And hashes match and validation status is `pass`
- Then the hook allows exit

### Scenario: Pending verdict — blocks exit

- Given a plan file exists with the current session marker
- And validation status is `pending`
- Then the hook blocks with prompt to run `/rodin:plan-gate`

### Scenario: Valid fail verdict — blocks exit

- Given a plan file exists with the current session marker
- And hashes match and validation status is `fail`
- Then the hook blocks with the assessment failure reason

### Scenario: Missing metadata — blocks exit

- Given a plan file exists with the current session marker
- And rodin metadata comments are missing from the plan file
- Then the hook blocks and treats it as no assessment

---

`@pre-tool-hook:2`
## Rule: Plan file discovery

### Scenario: Plan file found by session marker

- Given a plan file in `~/.claude/plans/` contains the current session marker
- When the hook searches for the plan file
- Then the hook uses that file for validation

### Scenario: Multiple plan files exist

- Given multiple plan files exist in `~/.claude/plans/`
- And only one contains the current session marker
- When the hook searches for the plan file
- Then the hook uses the file with the matching session marker

### Scenario: No matching plan file

- Given no plan file in `~/.claude/plans/` contains the current session marker
- When the hook searches for the plan file
- Then the hook blocks with "No assessment found" message

---

`@pre-tool-hook:3`
## Rule: Empty gaps block handling

### Scenario: Empty gaps block and critic finds no issues

- Given a plan with an empty gaps block
- And the critic declares no issues found
- When the validator checks coverage
- Then the validator reports PASS

### Scenario: Empty gaps block but critic finds issues

- Given a plan with an empty gaps block
- And the critic reports HIGH or MEDIUM findings
- When the validator checks coverage
- Then the validator reports FAIL with all findings listed as uncovered

---

`@pre-tool-hook:4`
## Rule: Bypass prevention

### Background

- Given a plan file with a valid passing assessment

### Scenario: Agent deletes session marker — blocks exit

- When the agent deletes the session marker comment
- And the agent attempts to exit plan mode
- Then the PreToolUse hook blocks exit with "No assessment found"

### Scenario: Agent modifies plan after assessment — blocks exit

- When the agent edits plan content after assessment
- Then the PostToolUse hook resets validation to `pending`
- And the PreToolUse hook blocks exit until re-assessment

### Scenario: Agent modifies gaps after assessment — blocks exit

- When the agent modifies the gaps block after assessment
- Then the PostToolUse hook updates the gaps hash
- And the PreToolUse hook blocks exit due to hash mismatch

### Scenario: Session marker from different session — blocks exit

- Given the plan file has a session marker from a previous session
- When the agent attempts to exit plan mode in a new session
- Then the hook blocks because session markers do not match

---

`@pre-tool-hook:5`
## Rule: Dependency validation

### Scenario: jq not installed

- Given a system without `jq` installed
- When either hook attempts to run
- Then the hook fails with an error message containing "jq required"
- And the error message includes installation guidance for macOS and Linux
