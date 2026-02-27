# Feature: Session Bypass (CAP-session-bypass)

<!--
MDG format. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

TERMINOLOGY (proposal language -> Gherkin keyword):
- "Capability" -> "Feature" (one Feature per capability)
- "Requirement" -> "Rule" (requirements are grouped as Rules)
-->

## Requirements

`@CAP-session-bypass:1`
### Rule: FSM_BYPASS env var allows skill file access

When FSM_BYPASS is set to a non-empty value, Read, Glob, and Grep access to skill files MUST be allowed without denying the request.

`@CAP-session-bypass:1.1`
#### Scenario: Bypass active allows Read of SKILL.md

- Given FSM_BYPASS is exported and non-empty in the shell environment
- When the agent attempts to Read a skill-internal file (SKILL.md)
- Then the tool request is allowed

`@CAP-session-bypass:1.2`
#### Scenario: Bypass not set denies Read of SKILL.md

- Given FSM_BYPASS is not present in the shell environment
- When the agent attempts to Read a skill-internal file (SKILL.md)
- Then the tool request is denied

`@CAP-session-bypass:1.3`
#### Scenario: Bypass active allows Glob of skill-internal file

- Given FSM_BYPASS is exported and non-empty in the shell environment
- When the agent attempts to Glob a pattern matching a skill-internal file
- Then the tool request is allowed

`@CAP-session-bypass:1.4`
#### Scenario: Bypass active allows Grep targeting skill-internal file

- Given FSM_BYPASS is exported and non-empty in the shell environment
- When the agent attempts to Grep with a path targeting a skill-internal file
- Then the tool request is allowed

`@CAP-session-bypass:1.5`
#### Scenario: Bypass active allows Read of hooks.json

- Given FSM_BYPASS is exported and non-empty in the shell environment
- When the agent attempts to Read a skill-internal file (hooks.json)
- Then the tool request is allowed

`@CAP-session-bypass:1.6`
#### Scenario: Bypass active allows Read of fsm.json

- Given FSM_BYPASS is exported and non-empty in the shell environment
- When the agent attempts to Read a skill-internal file (fsm.json)
- Then the tool request is allowed

`@CAP-session-bypass:1.7`
#### Scenario: Bypass exported as empty string denies Read

- Given FSM_BYPASS is exported as an empty string
- When the agent attempts to Read a skill-internal file (SKILL.md)
- Then the tool request is denied

`@CAP-session-bypass:1.8`
#### Scenario: Bypass not set denies Grep targeting skill-internal file

- Given FSM_BYPASS is not present in the shell environment
- When the agent attempts to Grep with a path targeting a skill-internal file
- Then the tool request is denied
