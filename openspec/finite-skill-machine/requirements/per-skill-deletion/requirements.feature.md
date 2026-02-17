# Feature: Per-Skill Deletion (per-skill-deletion)

<!--
DO NOT REMOVE THIS HEADER - it documents terminology mapping for editors.

MDG format. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

TERMINOLOGY (proposal language → Gherkin keyword):
- "Capability" → "Feature" (one Feature per capability)
- "Requirement" → "Rule" (requirements are grouped as Rules)

We use Gherkin syntax, so headers say "Feature" and "Rule".
-->

## Requirements

`@per-skill-deletion:1`
### Rule: The hook SHALL delete only tasks whose fsm metadata value matches the invoking skill's commandName

The hook SHALL delete only tasks whose `fsm` metadata value matches the invoking skill's commandName during hydration. Tasks tagged with a different skill's commandName SHALL be preserved.

#### Background
- Given the task directory contains FSM-tagged tasks from multiple skills

`@per-skill-deletion:1.1`
#### Scenario: Invoking skill-b preserves skill-a tasks

- Given task 1 has metadata `{"fsm": "plugin-a:skill-a"}`
- And task 2 has metadata `{"fsm": "plugin-a:skill-a"}`
- When the hook hydrates for commandName "plugin-b:skill-b"
- Then task 1 remains in the task directory
- And task 2 remains in the task directory

`@per-skill-deletion:1.2`
#### Scenario: Invoking skill-a deletes only skill-a tasks

- Given task 1 has metadata `{"fsm": "plugin-a:skill-a"}`
- And task 2 has metadata `{"fsm": "plugin-b:skill-b"}`
- When the hook hydrates for commandName "plugin-a:skill-a"
- Then task 1 is deleted
- And task 2 remains in the task directory

`@per-skill-deletion:1.3`
#### Scenario: Manual tasks preserved alongside per-skill deletion

- Given task 1 has metadata `{"fsm": "plugin-a:skill-a"}`
- And task 5 has no `fsm` key in metadata
- When the hook hydrates for commandName "plugin-a:skill-a"
- Then task 1 is deleted
- And task 5 remains in the task directory

`@per-skill-deletion:1.4`
#### Scenario: Non-string fsm metadata value preserved as another skill's task

- Given task 1 has metadata `{"fsm": "plugin-a:skill-a"}`
- And task 5 has metadata `{"fsm": null}`
- And task 8 has metadata `{"fsm": 42}`
- When the hook hydrates for commandName "plugin-a:skill-a"
- Then task 1 is deleted
- And task 5 remains in the task directory
- And task 8 remains in the task directory

`@per-skill-deletion:2`
### Rule: The hook SHALL calculate max ID from all tasks except the invoking skill's FSM tasks

The hook SHALL calculate the max ID from all tasks except those about to be deleted (the invoking skill's FSM tasks), ensuring new task IDs do not collide with preserved tasks from other skills.

`@per-skill-deletion:2.1`
#### Scenario: ID offset includes other skills' FSM tasks

- Given task 3 has metadata `{"fsm": "plugin-a:skill-a"}`
- And task 10 has metadata `{"fsm": "plugin-b:skill-b"}`
- And task 5 has no `fsm` key in metadata
- When the hook hydrates for commandName "plugin-a:skill-a"
- Then the highest preserved task ID is 10 (max of preserved tasks: 5 and 10)
- And new tasks start at ID 11

`@per-skill-deletion:2.2`
#### Scenario: ID offset with no other tasks

- Given task 1 has metadata `{"fsm": "plugin-a:skill-a"}`
- And no other tasks exist
- When the hook hydrates for commandName "plugin-a:skill-a"
- Then there are no preserved tasks
- And new tasks start at ID 1

`@per-skill-deletion:2.3`
#### Scenario: Corrupted task file aborts hydration

- Given task 3 has metadata `{"fsm": "plugin-a:skill-a"}`
- And task 10 is an unreadable or malformed file
- When the hook hydrates for commandName "plugin-a:skill-a"
- Then the hook aborts with a non-zero exit code
- And no tasks are deleted
- And no new tasks are written
