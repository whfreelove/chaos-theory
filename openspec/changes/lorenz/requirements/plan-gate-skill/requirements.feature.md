`@plan-gate-skill`
# Feature: plan-gate-skill

The `/rodin:plan-gate` skill orchestrates adversarial gap analysis and produces a pass/fail verdict
for the agent's plan. It requires plan mode context and a structurally valid plan before proceeding.

---

`@plan-gate-skill:1`
## Rule: Skill requires plan mode context

### Scenario: Skill invoked outside plan mode

- Given the agent is not in plan mode
- When the agent invokes `/rodin:plan-gate`
- Then the skill fails with "Must be invoked in plan mode" error

### Scenario: Skill invoked in plan mode

- Given the agent is in plan mode with a plan file
- When the agent invokes `/rodin:plan-gate`
- Then the skill proceeds with assessment using that plan file

---

`@plan-gate-skill:2`
## Rule: Goals section validation

### Background

- Given the agent is in plan mode with a plan file

### Scenario: Plan missing goals section

- Given the plan file lacks a `## Goals` section
- When the skill validates the plan structure
- Then the skill fails with "Plan must have ## Goals section"
- And assessment stops immediately

### Scenario: Plan has goals section

- Given the plan file has a `## Goals` section
- When the skill validates the plan structure
- Then validation passes for the goals requirement

---

`@plan-gate-skill:3`
## Rule: Gaps block validation

### Background

- Given the agent is in plan mode with a plan file

### Scenario: Plan missing gaps block

- Given the plan file lacks `<!-- rodin:gaps:start -->` and `<!-- rodin:gaps:end -->` markers
- When the skill validates the plan structure
- Then the skill fails with "Plan must have gaps block"
- And assessment stops immediately

### Scenario: Plan has gaps block

- Given the plan file has gaps block markers
- When the skill validates the plan structure
- Then validation passes for the gaps block requirement

### Scenario: Plan has empty gaps block

- Given the plan file has gaps block markers but no gap entries
- When the skill validates the plan structure
- Then the skill proceeds with assessment
- And any critic findings are treated as uncovered

---

`@plan-gate-skill:4`
## Rule: Leakage detection

### Scenario: Multiple gap-like phrases detected

- Given a plan containing 3 or more distinct gap-like phrases outside the gaps block
- When the leakage detector analyzes the plan
- Then the detected concerns are appended to the gaps block with MEDIUM severity

### Scenario: Few gap-like phrases detected

- Given a plan containing fewer than 3 gap-like phrases
- When the leakage detector analyzes the plan
- Then the skill proceeds to critic analysis without modification

### Scenario: Threshold boundary — 2 phrases, no detection

- Given a plan containing exactly 2 distinct gap-like phrases outside the gaps block
- When the leakage detector analyzes the plan
- Then the skill proceeds to critic analysis without modification
- And no gaps are appended to the gaps block

### Scenario: Threshold boundary — 3 phrases, detection triggered

- Given a plan containing exactly 3 distinct gap-like phrases outside the gaps block
- When the leakage detector analyzes the plan
- Then the gaps block contains all 3 detected concerns
- And each detected gap has MEDIUM severity

### Scenario: Above threshold — 5 phrases, detection triggered

- Given a plan containing 5 distinct gap-like phrases outside the gaps block
- When the leakage detector analyzes the plan
- Then the gaps block contains all 5 detected concerns
- And each detected gap has MEDIUM severity

---

`@plan-gate-skill:5`
## Rule: Critic analysis

### Scenario: Critic analyzes independently

- Given a plan file with documented gaps
- When the critic analyzes the plan
- Then critic findings are independent of the previously documented gaps

### Scenario: Critic identifies gaps

- Given a plan with implementation risks or unstated assumptions
- When the critic analyzes the plan
- Then the critic reports findings with severity levels
- And findings include goals mismatches, blockers, assumptions, and unmitigated risks

### Scenario: Critic finds no issues

- Given a comprehensive plan with no gaps
- When the critic analyzes the plan
- Then the critic explicitly declares no issues found

---

`@plan-gate-skill:6`
## Rule: Validator coverage check

### Scenario: All findings covered

- Given critic findings and a non-empty gaps block
- When the validator checks coverage
- Then the validator reports PASS if all HIGH and MEDIUM findings have corresponding gaps

### Scenario: Findings uncovered

- Given critic findings with HIGH or MEDIUM severity
- When the validator finds no corresponding gap for a finding
- Then the validator reports FAIL with the uncovered findings listed

### Scenario: Semantic matching

- Given a gap that plausibly addresses a critic finding
- When the validator evaluates coverage
- Then the validator counts it as covered

### Scenario: Low severity findings deferred

- Given critic findings with only LOW severity uncovered
- When the validator checks coverage
- Then the validator reports PASS

---

`@plan-gate-skill:7`
## Rule: Subagent error handling

### Scenario: Subagent fails once

- Given a subagent that times out or returns unparseable output
- When the skill detects the failure
- Then the skill retries the subagent once

### Scenario: Subagent fails twice

- Given a subagent that fails on retry
- When the second attempt also fails
- Then the skill fails closed and blocks plan mode exit

---

`@plan-gate-skill:8`
## Rule: Verdict signal written to plan file

### Scenario: Assessment passes

- Given the validator determines all findings are covered
- When the skill completes assessment
- Then a pass verdict signal is written to the plan file

### Scenario: Assessment fails

- Given the validator finds uncovered findings
- When the skill completes assessment
- Then a fail verdict signal is written with the uncovered findings listed
