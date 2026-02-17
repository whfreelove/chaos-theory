# Feature: Finite Skill Machine Integration (integration)

<!--
OPTIONAL FILE - only create when capabilities interact in ways not captured
by single-capability requirements.

MDG format. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

PURPOSE: Cross-capability integration test scenarios.
- Tests interactions BETWEEN capabilities
- Does NOT duplicate single-capability requirements
- References involved capabilities with @capability-slug tags
-->

## Integration Scenarios

`@integration:1` `@per-skill-deletion` `@active-task-guard`
### Rule: Guard and scoped deletion agree on skill ownership

The active task guard and scoped deletion both filter tasks by `fsm` metadata value. When one skill has active tasks and another skill is invoked, the guard must not falsely trigger and deletion must not cross skill boundaries.

`@integration:1.1`
#### Scenario: Invoke skill-b while skill-a has active tasks

- Given task 6 has metadata `{"fsm": "plugin-a:skill-a"}` and status "in_progress"
- And task 7 has metadata `{"fsm": "plugin-b:skill-b"}` and status "pending"
- When the hook hydrates for commandName "plugin-b:skill-b"
- Then the guard passes (skill-b has no active tasks)
- And task 7 is deleted (scoped to skill-b)
- And task 6 remains untouched (belongs to skill-a)
- And new tasks from skill-b's fsm.json are written

`@integration:1.2`
#### Scenario: Re-invoke skill-a with all completed tasks while skill-b exists

- Given task 6 has metadata `{"fsm": "plugin-a:skill-a"}` and status "completed"
- And task 7 has metadata `{"fsm": "plugin-b:skill-b"}` and status "pending"
- When the hook hydrates for commandName "plugin-a:skill-a"
- Then the guard passes (all skill-a tasks are uniformly completed)
- And task 6 is deleted (scoped to skill-a)
- And task 7 remains in the task directory (belongs to skill-b)
- And new tasks from skill-a's fsm.json are written

`@integration:2` `@per-skill-deletion` `@active-task-guard` `@task-hydration-skill`
### Rule: Sequential multi-skill invocation preserves isolation

Invoking multiple skills in sequence produces a task directory where each skill's tasks coexist independently, and re-invocation respects both scoping and the active guard.

`@integration:2.1`
#### Scenario: Invoke skill-a then skill-b produces combined task set

- Given skill-a's fsm.json defines tasks [1, 2] and skill-b's fsm.json defines tasks [1, 2, 3]
- When skill-a is invoked first
- Then tasks 1 and 2 are created with `{"fsm": "plugin-a:skill-a"}`
- When skill-b is invoked second
- Then tasks 3, 4, 5 are created with `{"fsm": "plugin-b:skill-b"}` (offset by max ID 2)
- And tasks 1 and 2 from skill-a remain

`@integration:2.2`
#### Scenario: Re-invoke skill-a after skill-b with all tasks pending

- Given skill-a was invoked (tasks 1, 2 with `{"fsm": "plugin-a:skill-a"}`)
- And skill-b was invoked (tasks 3, 4, 5 with `{"fsm": "plugin-b:skill-b"}`)
- And all tasks have status "pending"
- When skill-a is re-invoked
- Then the guard passes (all skill-a tasks are pending)
- And tasks 1, 2 are deleted (scoped to skill-a)
- And tasks 3, 4, 5 remain (belong to skill-b)
- And new skill-a tasks are written starting at ID 6 (offset by max preserved ID 5)

`@integration:2.3`
#### Scenario: Re-invoke skill-a after agent starts working on skill-a tasks

- Given skill-a was invoked (tasks 1, 2 with `{"fsm": "plugin-a:skill-a"}`)
- And skill-b was invoked (tasks 3, 4, 5 with `{"fsm": "plugin-b:skill-b"}`)
- And task 1 has been updated to status "in_progress"
- When skill-a is re-invoked
- Then the guard aborts (task 1 is active for skill-a)
- And all 5 tasks remain unchanged

`@integration:3` `@per-skill-deletion` `@task-hydration-skill`
### Rule: ID offset integrity across scoped deletion

After scoped deletion removes only the invoking skill's tasks, the ID offset must account for all remaining tasks (manual + other skills) to prevent ID collisions.

`@integration:3.1`
#### Scenario: ID offset after scoped deletion with gaps

- Given task 1 has metadata `{"fsm": "plugin-a:skill-a"}`
- And task 5 has no `fsm` key (manual task)
- And task 10 has metadata `{"fsm": "plugin-b:skill-b"}`
- When skill-a is re-invoked with fsm.json defining tasks [1, 2]
- Then task 1 is deleted (scoped to skill-a)
- And the offset is 10 (max of preserved tasks 5 and 10)
- And new tasks are written as 11 and 12
