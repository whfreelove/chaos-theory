# Feature: Active Task Guard (active-task-guard)

<!--
DO NOT REMOVE THIS HEADER - it documents terminology mapping for editors.

MDG format. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

TERMINOLOGY (proposal language → Gherkin keyword):
- "Capability" → "Feature" (one Feature per capability)
- "Requirement" → "Rule" (requirements are grouped as Rules)

We use Gherkin syntax, so headers say "Feature" and "Rule".
-->

## Requirements

`@active-task-guard:1`
### Rule: The hook SHALL abort re-invocation when the invoking skill's tasks have mixed statuses

When re-invoking a skill, the hook SHALL check the status of all existing FSM tasks matching that skill. The hook SHALL allow re-invocation only when all matching tasks are uniformly `completed` (workflow done) or uniformly `pending` (nothing started). Any mix of statuses — including combinations like completed + pending, even without `in_progress` — indicates the workflow as a whole is in progress and the hook SHALL abort entirely (no deletes, no writes).

#### Background
- Given a skill with fsm.json is invoked
- And the hook has located a valid fsm.json

`@active-task-guard:1.1`
#### Scenario: Re-invoke with in_progress tasks aborts

- Given task 6 has metadata `{"fsm": "plugin-a:skill-a"}` and status "in_progress"
- When the hook hydrates for commandName "plugin-a:skill-a"
- Then the hook aborts with a non-zero exit code
- And no tasks are deleted
- And no new tasks are written

`@active-task-guard:1.2`
#### Scenario: Re-invoke with all completed tasks proceeds

- Given task 6 has metadata `{"fsm": "plugin-a:skill-a"}` and status "completed"
- And task 7 has metadata `{"fsm": "plugin-a:skill-a"}` and status "completed"
- When the hook hydrates for commandName "plugin-a:skill-a"
- Then the hook proceeds normally
- And task 6 is deleted
- And task 7 is deleted
- And new tasks from fsm.json are written

`@active-task-guard:1.3`
#### Scenario: Re-invoke with all pending tasks proceeds

- Given task 6 has metadata `{"fsm": "plugin-a:skill-a"}` and status "pending"
- And task 7 has metadata `{"fsm": "plugin-a:skill-a"}` and status "pending"
- When the hook hydrates for commandName "plugin-a:skill-a"
- Then the hook proceeds normally
- And task 6 is deleted
- And task 7 is deleted
- And new tasks from fsm.json are written

`@active-task-guard:1.4`
#### Scenario: First invocation with no existing tasks proceeds

- Given no tasks in the task directory match commandName "plugin-a:skill-a"
- When the hook hydrates for commandName "plugin-a:skill-a"
- Then the hook proceeds normally

`@active-task-guard:1.5`
#### Scenario: Mixed completed and pending tasks aborts

- Given task 6 has metadata `{"fsm": "plugin-a:skill-a"}` and status "completed"
- And task 7 has metadata `{"fsm": "plugin-a:skill-a"}` and status "pending"
- When the hook hydrates for commandName "plugin-a:skill-a"
- Then the hook aborts with a non-zero exit code
- And no tasks are deleted
- And no new tasks are written

`@active-task-guard:1.6`
#### Scenario: Mixed in_progress and completed tasks aborts

- Given task 6 has metadata `{"fsm": "plugin-a:skill-a"}` and status "in_progress"
- And task 7 has metadata `{"fsm": "plugin-a:skill-a"}` and status "completed"
- When the hook hydrates for commandName "plugin-a:skill-a"
- Then the hook aborts with a non-zero exit code
- And no tasks are deleted
- And no new tasks are written

`@active-task-guard:1.7`
#### Scenario: Corrupted task file during guard check aborts

- Given task 6 has metadata `{"fsm": "plugin-a:skill-a"}` and status "completed"
- And task 7 is an unreadable or malformed file
- When the hook hydrates for commandName "plugin-a:skill-a"
- Then the hook aborts with a non-zero exit code
- And no tasks are deleted
- And no new tasks are written

`@active-task-guard:1.8`
#### Scenario: Unrecognized status value triggers abort

- Given task 6 has metadata `{"fsm": "plugin-a:skill-a"}` and status "blocked"
- When the hook hydrates for commandName "plugin-a:skill-a"
- Then the hook aborts with a non-zero exit code
- And no tasks are deleted
- And no new tasks are written

`@active-task-guard:2`
### Rule: The abort message SHALL identify blocking tasks

The error message SHALL name the specific tasks preventing re-invocation, giving the agent enough information to resolve the conflict.

`@active-task-guard:2.1`
#### Scenario: Abort error is a JSON object with task IDs and message

- Given task 6 has metadata `{"fsm": "plugin-a:skill-a"}`, status "completed"
- And task 7 has metadata `{"fsm": "plugin-a:skill-a"}`, status "pending"
- When the hook hydrates for commandName "plugin-a:skill-a"
- Then stderr contains a JSON object
- And the JSON object has a "tasks" array containing `6` and `7`
- And the JSON object has a "message" field equal to "Related active task(s) must be resolved and verified first."

`@active-task-guard:2.2`
#### Scenario: Abort message never references internal mechanisms

- Given active FSM tasks exist for the invoking skill
- When the hook aborts
- Then the error message does not contain "hydration", "re-hydration", or "re-hydrate"
- And the error message does not suggest the agent "delete" or "just complete" tasks

`@active-task-guard:3`
### Rule: The guard SHALL only check the invoking skill's tasks

Active tasks from other skills SHALL NOT trigger the guard. The hook SHALL check only tasks matching the invoking skill's commandName.

`@active-task-guard:3.1`
#### Scenario: Other skill's active tasks do not block

- Given task 6 has metadata `{"fsm": "plugin-b:skill-b"}` and status "in_progress"
- When the hook hydrates for commandName "plugin-a:skill-a"
- Then the hook proceeds normally

`@active-task-guard:3.2`
#### Scenario: Mixed active tasks from multiple skills

- Given task 6 has metadata `{"fsm": "plugin-a:skill-a"}` and status "in_progress"
- And task 7 has metadata `{"fsm": "plugin-b:skill-b"}` and status "in_progress"
- And task 7 matches the invoking skill's commandName
- When the hook hydrates for commandName "plugin-b:skill-b"
- Then the hook aborts with a non-zero exit code
- And task 6 remains untouched
