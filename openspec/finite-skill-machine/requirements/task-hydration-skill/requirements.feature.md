# Feature: Task Hydration Skill (task-hydration-skill)

<!--
MDG format. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

TERMINOLOGY (proposal language -> Gherkin keyword):
- "Capability" -> "Feature" (one Feature per capability)
- "Requirement" -> "Rule" (requirements are grouped as Rules)
-->

## Requirements

`@task-hydration-skill:1`
### Rule: Skill tool triggers FSM hook

The FSM hook SHALL execute as a PostToolUse hook after successful Skill tool invocations.

`@task-hydration-skill:1.1`
#### Scenario: Successful skill invocation triggers hook

- Given a skill with fsm.json is installed
- When the Skill tool completes successfully
- Then the FSM hook receives the tool input via stdin

`@task-hydration-skill:1.2`
#### Scenario: Valid input JSON parsed correctly

- Given stdin contains valid JSON with session_id, cwd, and tool_response.commandName
- When the hook parses stdin
- Then it extracts session_id for task directory path
- And it extracts commandName for skill location

`@task-hydration-skill:1.3`
#### Scenario: Missing session_id fails the hook

- Given stdin JSON lacks session_id field
- When the hook parses stdin
- Then it exits with non-zero code
- And the error message indicates missing session_id

`@task-hydration-skill:1.4`
#### Scenario: Missing commandName fails the hook

- Given stdin JSON lacks tool_response.commandName field
- When the hook parses stdin
- Then it exits with non-zero code
- And the error message indicates missing commandName

`@task-hydration-skill:1.5`
#### Scenario: Malformed stdin JSON fails the hook

- Given stdin contains invalid JSON
- When the hook attempts to parse stdin
- Then it exits with non-zero code
- And the error message describes the parse failure

`@task-hydration-skill:2`
### Rule: Hook locates fsm.json by commandName

The hook SHALL locate the skill's fsm.json using commandName and Claude Code's plugin resolution. When the registry is in v1 format, the hook SHALL emit a deprecation notice to stderr before proceeding with v1 resolution logic.

`@task-hydration-skill:2.1`
#### Scenario: Plugin skill fsm.json in skills directory

- Given commandName is "my-plugin:my-skill"
- And installed_plugins.json contains a matching entry
- When the hook searches for fsm.json
- Then it reads from {installPath}/skills/my-skill/fsm.json

`@task-hydration-skill:2.2`
#### Scenario: Plugin skill fsm.json in commands directory

- Given commandName is "my-plugin:my-command"
- And no fsm.json exists in the skills directory
- When the hook searches for fsm.json
- Then it reads from {installPath}/commands/my-command/fsm.json

`@task-hydration-skill:2.3`
#### Scenario: Non-plugin skill in project directory

- Given commandName has no colon
- And {cwd}/.claude/skills/{skill}/fsm.json exists
- When the hook searches for fsm.json
- Then it reads the project-local file

`@task-hydration-skill:2.4`
#### Scenario: Non-plugin skill falls back to user directory

- Given commandName has no colon
- And no project-local fsm.json exists
- When the hook searches for fsm.json
- Then it reads from ~/.claude/skills/{skill}/fsm.json

`@task-hydration-skill:2.5`
#### Scenario: No fsm.json found

- Given no fsm.json exists in any location
- When the hook completes
- Then it returns {"continue": true} without creating tasks

`@task-hydration-skill:2.6`
#### Scenario: v1 format registry emits deprecation notice

- Given installed_plugins.json is in v1 array format
- And commandName is "my-plugin:my-skill"
- When the hook reads installed_plugins.json
- Then stderr contains a deprecation notice
- And the hook proceeds with normal v1 plugin resolution

`@task-hydration-skill:2.7`
#### Scenario: Deprecation notice content and channel

- Given the hook detects v1 registry format
- When the deprecation notice is emitted
- Then the message advises updating to v2 format
- And the message is written to stderr, not stdout

`@task-hydration-skill:3`
### Rule: Hook prefers specific plugin scopes

The hook SHALL prefer local > project > user scope when multiple plugin installations match.

`@task-hydration-skill:3.1`
#### Scenario Outline: Scope precedence

- Given plugin is installed with <higher> and <lower> scopes
- And cwd matches both entries
- When the hook resolves the plugin
- Then it uses the <higher> scope installation

##### Examples
| higher  | lower   |
|---------|---------|
| local   | project |
| local   | user    |
| project | user    |

`@task-hydration-skill:3.2`
#### Scenario: Local scope only

- Given plugin is installed only with local scope
- And projectPath matches cwd
- When the hook resolves the plugin
- Then it uses the local scope installation

`@task-hydration-skill:3.3`
#### Scenario: Project scope only

- Given plugin is installed only with project scope
- And projectPath matches cwd
- When the hook resolves the plugin
- Then it uses the project scope installation

`@task-hydration-skill:3.4`
#### Scenario: User scope only

- Given plugin is installed only with user scope
- When the hook resolves the plugin
- Then it uses the user scope installation

`@task-hydration-skill:3.5`
#### Scenario: projectPath matching

- Given plugin is installed with project scope
- And projectPath is "/projects/myapp"
- And cwd is "/projects/myapp/src/components"
- When the hook resolves the plugin
- Then it uses the project scope installation (cwd is under projectPath)

`@task-hydration-skill:3.6`
#### Scenario: projectPath non-matching

- Given plugin is installed with project scope
- And projectPath is "/projects/myapp"
- And cwd is "/projects/otherapp"
- When the hook resolves the plugin
- Then the project scope entry is not used

`@task-hydration-skill:3.7`
#### Scenario: Plugin not in installed_plugins.json falls back to non-plugin lookup

- Given commandName is "my-plugin:my-skill"
- And installed_plugins.json exists but has no entry for "my-plugin"
- And {cwd}/.claude/skills/my-skill/fsm.json exists
- When the hook searches for fsm.json
- Then it reads from {cwd}/.claude/skills/my-skill/fsm.json

`@task-hydration-skill:4`
### Rule: Hook validates fsm.json atomically

The hook SHALL validate all tasks before any writes or deletes occur.

`@task-hydration-skill:4.1`
#### Scenario: Valid fsm.json creates tasks

- Given fsm.json contains valid task definitions
- When the hook processes the file
- Then task files are written to the task directory

`@task-hydration-skill:4.2`
#### Scenario: Malformed JSON fails the hook

- Given fsm.json contains invalid JSON
- When the hook processes the file
- Then it exits with non-zero code
- And the error message describes the parse failure

`@task-hydration-skill:4.3`
#### Scenario: Missing required field fails the hook

- Given a task entry lacks id or subject
- When the hook validates fsm.json
- Then it exits with non-zero code
- And the error identifies the missing field

`@task-hydration-skill:4.4`
#### Scenario: Duplicate IDs fail the hook

- Given two task entries share the same id
- When the hook validates fsm.json
- Then it exits with non-zero code
- And the error identifies the duplicate

`@task-hydration-skill:4.5`
#### Scenario: Invalid dependency reference fails the hook

- Given blockedBy references an ID not in fsm.json
- When the hook validates fsm.json
- Then it exits with non-zero code
- And the error identifies the invalid reference

`@task-hydration-skill:4.6`
#### Scenario: Multiple errors reported together

- Given fsm.json has multiple validation errors
- When the hook validates fsm.json
- Then all errors appear in a single message

`@task-hydration-skill:4.7`
#### Scenario: Task files written with correct path and structure

- Given fsm.json contains a valid task with id 1, subject "Set up environment", description "Install deps"
- And session_id is "abc-123"
- And the task directory has no existing tasks
- When the hook creates tasks
- Then a file is written to ~/.claude/tasks/abc-123/1.json
- And the file contains valid JSON with:
  - "id" as string "1" (not number)
  - "subject" as "Set up environment"
  - "description" as "Install deps"
  - "status" as "pending"
  - "owner" as empty string
  - "blocks" as empty array
  - "blockedBy" as empty array
  - "metadata" containing {"fsm": "<commandName>"}

`@task-hydration-skill:5`
### Rule: The hook SHALL translate local IDs to actual IDs

The hook SHALL offset local IDs by the maximum existing task ID, where "existing" now means all tasks **not** about to be deleted (manual tasks + other skills' FSM tasks).

`@task-hydration-skill:5.1`
#### Scenario: Empty task directory

- Given the task directory has no files
- When fsm.json defines local ID 1
- Then the written task has actual ID 1

`@task-hydration-skill:5.2`
#### Scenario: Existing tasks offset new IDs

- Given the task directory has max preserved task ID 5
- When fsm.json defines local IDs 1, 2, 3
- Then written tasks have actual IDs 6, 7, 8

`@task-hydration-skill:5.3`
#### Scenario: Dependencies use translated IDs

- Given fsm.json has blockedBy: [1] on local ID 2
- And translation produces actual IDs 6 and 7
- Then the written task has blockedBy: [6]

`@task-hydration-skill:6`
### Rule: Hook tags tasks with FSM metadata

The hook SHALL add {"fsm": "skill-name"} to each task's metadata.

`@task-hydration-skill:6.1`
#### Scenario: Created task includes fsm tag

- Given skill commandName is "my-plugin:my-skill"
- When the hook creates a task
- Then the task metadata contains {"fsm": "my-plugin:my-skill"}

`@task-hydration-skill:6.2`
#### Scenario: Custom metadata preserved

- Given fsm.json task has metadata {"custom": "value"}
- When the hook creates the task
- Then both fsm and custom keys exist in metadata

`@task-hydration-skill:7`
### Rule: The hook SHALL delete matching FSM-tagged tasks before writing

The hook SHALL delete only tasks whose `fsm` metadata value matches the invoking skill's commandName before writing new tasks. Tasks with different `fsm` values or no `fsm` key are preserved.

`@task-hydration-skill:7.1`
#### Scenario: Previous same-skill FSM tasks deleted

- Given the task directory contains tasks with `{"fsm": "plugin-a:skill-a"}`
- When the hook hydrates for commandName "plugin-a:skill-a"
- Then those tasks are deleted before new writes

`@task-hydration-skill:7.2`
#### Scenario: Manual tasks preserved

- Given the task directory contains tasks without fsm key
- When a skill with fsm.json is invoked
- Then those tasks remain untouched

`@task-hydration-skill:7.3`
#### Scenario: Deletion blocked by validation failure

- Given fsm.json has validation errors
- When the hook processes the file
- Then no existing tasks are deleted

`@task-hydration-skill:7.4`
#### Scenario: Deletion aborts on file system error

- Given a task file cannot be deleted due to a file system error
- When the hook attempts cleanup
- Then the hook aborts with an error
- And no new tasks are written
- And task files deleted before the failure are not restored

`@task-hydration-skill:7.5`
#### Scenario: Write failure after successful deletion is recoverable

- Given the task directory contains tasks with `{"fsm": "plugin-a:skill-a"}`
- And the hook successfully deletes all matching tasks
- When writing new tasks fails due to a file system error
- Then the hook aborts with a non-zero exit code
- And the task directory contains no tasks matching "plugin-a:skill-a"

`@task-hydration-skill:8`
### Rule: Hook returns continue on completion

The hook SHALL output {"continue": true} and exit 0 on success.

`@task-hydration-skill:8.1`
#### Scenario: Successful hydration

- Given fsm.json is valid
- When tasks are written successfully
- Then stdout contains {"continue": true}
- And exit code is 0

`@task-hydration-skill:8.2`
#### Scenario: No-op completion

- Given no fsm.json is found
- When the hook completes
- Then stdout contains {"continue": true}
- And exit code is 0

