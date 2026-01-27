## ADDED Requirements

### REQ-THS-1: Skill tool triggers FSM hook
The FSM hook SHALL execute as a PostToolUse hook after successful Skill tool invocations.

#### SCN-THS-1.1: Successful skill invocation triggers hook

- Given a skill with fsm.json is installed
- When the Skill tool completes successfully
- Then the FSM hook receives the tool input via stdin

#### SCN-THS-1.2: Valid input JSON parsed correctly

- Given stdin contains valid JSON with session_id, cwd, and tool_response.commandName
- When the hook parses stdin
- Then it extracts session_id for task directory path
- And it extracts commandName for skill location

#### SCN-THS-1.3: Missing session_id fails the hook

- Given stdin JSON lacks session_id field
- When the hook parses stdin
- Then it exits with non-zero code
- And the error message indicates missing session_id

#### SCN-THS-1.4: Missing commandName fails the hook

- Given stdin JSON lacks tool_response.commandName field
- When the hook parses stdin
- Then it exits with non-zero code
- And the error message indicates missing commandName

#### SCN-THS-1.5: Malformed stdin JSON fails the hook

- Given stdin contains invalid JSON
- When the hook attempts to parse stdin
- Then it exits with non-zero code
- And the error message describes the parse failure

### REQ-THS-2: Hook locates fsm.json by commandName
The hook SHALL locate the skill's fsm.json using commandName and Claude Code's plugin resolution.

#### SCN-THS-2.1: Plugin skill fsm.json in skills directory

- Given commandName is "my-plugin:my-skill"
- And installed_plugins.json contains a matching entry
- When the hook searches for fsm.json
- Then it reads from {installPath}/skills/my-skill/fsm.json

#### SCN-THS-2.2: Plugin skill fsm.json in commands directory

- Given commandName is "my-plugin:my-command"
- And no fsm.json exists in the skills directory
- When the hook searches for fsm.json
- Then it reads from {installPath}/commands/my-command/fsm.json

#### SCN-THS-2.3: Non-plugin skill in project directory

- Given commandName has no colon
- And {cwd}/.claude/skills/{skill}/fsm.json exists
- When the hook searches for fsm.json
- Then it reads the project-local file

#### SCN-THS-2.4: Non-plugin skill falls back to user directory

- Given commandName has no colon
- And no project-local fsm.json exists
- When the hook searches for fsm.json
- Then it reads from ~/.claude/skills/{skill}/fsm.json

#### SCN-THS-2.5: No fsm.json found

- Given no fsm.json exists in any location
- When the hook completes
- Then it returns {"continue": true} without creating tasks

### REQ-THS-3: Hook prefers specific plugin scopes
The hook SHALL prefer local > project > user scope when multiple plugin installations match.

#### SCN-THS-3.1: Scope precedence

- Given plugin is installed with <higher> and <lower> scopes
- And cwd matches both entries
- When the hook resolves the plugin
- Then it uses the <higher> scope installation

Examples:
| higher  | lower   |
| local   | project |
| local   | user    |
| project | user    |

#### SCN-THS-3.2: Local scope only

- Given plugin is installed only with local scope
- And projectPath matches cwd
- When the hook resolves the plugin
- Then it uses the local scope installation

#### SCN-THS-3.3: Project scope only

- Given plugin is installed only with project scope
- And projectPath matches cwd
- When the hook resolves the plugin
- Then it uses the project scope installation

#### SCN-THS-3.4: User scope only

- Given plugin is installed only with user scope
- When the hook resolves the plugin
- Then it uses the user scope installation

#### SCN-THS-3.5: projectPath matching

- Given plugin is installed with project scope
- And projectPath is "/projects/myapp"
- And cwd is "/projects/myapp/src/components"
- When the hook resolves the plugin
- Then it uses the project scope installation (cwd is under projectPath)

#### SCN-THS-3.6: projectPath non-matching

- Given plugin is installed with project scope
- And projectPath is "/projects/myapp"
- And cwd is "/projects/otherapp"
- When the hook resolves the plugin
- Then the project scope entry is not used

#### SCN-THS-3.7: Plugin not in installed_plugins.json falls back to non-plugin lookup

- Given commandName is "my-plugin:my-skill"
- And installed_plugins.json exists but has no entry for "my-plugin"
- And {cwd}/.claude/skills/my-skill/fsm.json exists
- When the hook searches for fsm.json
- Then it reads from {cwd}/.claude/skills/my-skill/fsm.json

### REQ-THS-4: Hook validates fsm.json atomically
The hook SHALL validate all tasks before any writes or deletes occur.

#### SCN-THS-4.1: Valid fsm.json creates tasks

- Given fsm.json contains valid task definitions
- When the hook processes the file
- Then task files are written to the task directory

#### SCN-THS-4.2: Malformed JSON fails the hook

- Given fsm.json contains invalid JSON
- When the hook processes the file
- Then it exits with non-zero code
- And the error message describes the parse failure

#### SCN-THS-4.3: Missing required field fails the hook

- Given a task entry lacks id or subject
- When the hook validates fsm.json
- Then it exits with non-zero code
- And the error identifies the missing field

#### SCN-THS-4.4: Duplicate IDs fail the hook

- Given two task entries share the same id
- When the hook validates fsm.json
- Then it exits with non-zero code
- And the error identifies the duplicate

#### SCN-THS-4.5: Invalid dependency reference fails the hook

- Given blockedBy references an ID not in fsm.json
- When the hook validates fsm.json
- Then it exits with non-zero code
- And the error identifies the invalid reference

#### SCN-THS-4.6: Multiple errors reported together

- Given fsm.json has multiple validation errors
- When the hook validates fsm.json
- Then all errors appear in a single message

#### SCN-THS-4.7: Task files written with correct path and structure

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

### REQ-THS-5: Hook translates local IDs to actual IDs
The hook SHALL offset local IDs by the maximum existing task ID.

#### SCN-THS-5.1: Empty task directory

- Given the task directory has no files
- When fsm.json defines local ID 1
- Then the written task has actual ID 1

#### SCN-THS-5.2: Existing tasks offset new IDs

- Given the task directory has max ID 5
- When fsm.json defines local IDs 1, 2, 3
- Then written tasks have actual IDs 6, 7, 8

#### SCN-THS-5.3: Dependencies use translated IDs

- Given fsm.json has blockedBy: [1] on local ID 2
- And translation produces actual IDs 6 and 7
- Then the written task has blockedBy: [6]

### REQ-THS-6: Hook tags tasks with FSM metadata
The hook SHALL add {"fsm": "skill-name"} to each task's metadata.

#### SCN-THS-6.1: Created task includes fsm tag

- Given skill commandName is "my-plugin:my-skill"
- When the hook creates a task
- Then the task metadata contains {"fsm": "my-plugin:my-skill"}

#### SCN-THS-6.2: Custom metadata preserved

- Given fsm.json task has metadata {"custom": "value"}
- When the hook creates the task
- Then both fsm and custom keys exist in metadata

### REQ-THS-7: Hook deletes FSM-tagged tasks before writing
The hook SHALL delete tasks with fsm metadata key before writing new tasks.

#### SCN-THS-7.1: Previous FSM tasks deleted

- Given the task directory contains FSM-tagged tasks
- When a skill with fsm.json is invoked
- Then all FSM-tagged tasks are deleted before new writes

#### SCN-THS-7.2: Manual tasks preserved

- Given the task directory contains tasks without fsm key
- When a skill with fsm.json is invoked
- Then those tasks remain untouched

#### SCN-THS-7.3: Deletion blocked by validation failure

- Given fsm.json has validation errors
- When the hook processes the file
- Then no existing tasks are deleted

### REQ-THS-8: Hook returns continue on completion
The hook SHALL output {"continue": true} and exit 0 on success.

#### SCN-THS-8.1: Successful hydration

- Given fsm.json is valid
- When tasks are written successfully
- Then stdout contains {"continue": true}
- And exit code is 0

#### SCN-THS-8.2: No-op completion

- Given no fsm.json is found
- When the hook completes
- Then stdout contains {"continue": true}
- And exit code is 0
