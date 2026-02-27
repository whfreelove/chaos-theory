# Feature: Actionable Denial (CAP-actionable-denial)

<!--
MDG format. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

TERMINOLOGY (proposal language -> Gherkin keyword):
- "Capability" -> "Feature" (one Feature per capability)
- "Requirement" -> "Rule" (requirements are grouped as Rules)
-->

## Requirements

`@CAP-actionable-denial:1`
### Rule: Denial message includes FSM_BYPASS export instructions

The denial message MUST tell the user to export FSM_BYPASS=1 to allow skill file access for the session. The denial message MUST NOT contain advice to disable the plugin.

`@CAP-actionable-denial:1.1`
#### Scenario: Denial message contains bypass instructions

- Given FSM_BYPASS is not present in the shell environment
- When the agent attempts to Glob a skill-internal file (fsm.json)
- Then the tool request is denied
- And the denial message contains "export FSM_BYPASS=1"

`@CAP-actionable-denial:1.2`
#### Scenario: Denial message does not contain plugin disable advice

- Given FSM_BYPASS is not present in the shell environment
- When the agent attempts to Glob a skill-internal file (fsm.json)
- Then the tool request is denied
- And the denial message does not contain "Disable finite-skill-machine"
