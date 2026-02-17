`@plan-gate-skill` `@post-tool-hook` `@pre-tool-hook`
# Feature: Assessment verdict propagation (integration)

`@integration:1` `@plan-gate-skill` `@post-tool-hook` `@pre-tool-hook`
## Rule: Assessment verdict determines exit eligibility

### Background

- Given the agent is in plan mode with a plan file containing a goals section and gaps block

### Scenario: Passing assessment enables plan mode exit

- Given a pass verdict has been recorded in the plan file
- When the agent attempts to exit plan mode
- Then the agent exits plan mode successfully

### Scenario: Failing assessment blocks plan mode exit

- Given a fail verdict has been recorded in the plan file
- When the agent attempts to exit plan mode
- Then the agent is blocked with the failure reason from the assessment

`@integration:2` `@plan-gate-skill` `@post-tool-hook` `@pre-tool-hook`
## Rule: Content change after assessment invalidates exit eligibility

### Background

- Given the agent is in plan mode
- And a pass verdict has been recorded in the plan file

### Scenario: Plan edit after assessment blocks exit

- When the agent edits the plan content
- Then the agent is unable to exit plan mode

### Scenario: Gaps edit after assessment blocks exit

- When the agent edits the gaps block
- Then the agent is unable to exit plan mode

### Scenario: Re-assessment after content change restores exit eligibility

- Given the agent has edited the plan content since the last assessment
- And a new pass verdict has been recorded in the plan file
- When the agent attempts to exit plan mode
- Then the agent exits plan mode successfully
