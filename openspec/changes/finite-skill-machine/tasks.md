## 1. Plugin Scaffolding

- [ ] 1.1 Create plugin directory structure with plugin.json and hooks.json
- [ ] 1.2 Create hydrate-tasks.py script skeleton with stdin parsing

## 2. Skill Location

- [ ] 2.1 Implement installed_plugins.json parsing and scope filtering
- [ ] 2.2 Implement scope precedence logic (local > project > user)
- [ ] 2.3 Implement fsm.json path resolution for plugin skills (skills/ and commands/ directories)
- [ ] 2.4 Implement fsm.json path resolution for non-plugin skills (project and user directories)
- [ ] 2.5 Implement fallback from plugin to non-plugin lookup when plugin not found

## 3. fsm.json Validation

- [ ] 3.1 Implement JSON parsing with error handling
- [ ] 3.2 Validate required fields (id, subject) on each task entry
- [ ] 3.3 Detect and report duplicate IDs
- [ ] 3.4 Validate blockedBy/blocks references exist in same file
- [ ] 3.5 Aggregate multiple errors into single failure message

## 4. ID Translation

- [ ] 4.1 Read existing task files and find max ID
- [ ] 4.2 Translate local IDs to actual IDs (base + local_id)
- [ ] 4.3 Rewrite blockedBy/blocks arrays with translated IDs

## 5. Task File Output

- [ ] 5.1 Implement task file schema (string IDs, required arrays)
- [ ] 5.2 Merge fsm metadata tag with any custom metadata
- [ ] 5.3 Write task files to ~/.claude/tasks/{session_id}/{id}.json

## 6. FSM Task Cleanup

- [ ] 6.1 Scan task directory for tasks with fsm metadata key
- [ ] 6.2 Delete FSM-tagged tasks before writing new tasks
- [ ] 6.3 Preserve manual tasks (no fsm metadata key)

## 7. Atomic Fail-Closed Behavior

- [ ] 7.1 Parse and validate ALL tasks before any deletes or writes
- [ ] 7.2 On validation error: exit non-zero, leave existing tasks untouched
- [ ] 7.3 On write/delete failure: report error with manual cleanup path

## 8. Hook Response

- [ ] 8.1 Return {"continue": true} and exit 0 on success
- [ ] 8.2 Return {"continue": true} and exit 0 when no fsm.json found (no-op)
- [ ] 8.3 Exit non-zero with error message on any failure

## 9. Tests

- [ ] 9.1 Set up pytest with conftest.py and fixtures directory
- [ ] 9.2 Write unit tests for fsm.json validation (REQ-THS-4 scenarios)
- [ ] 9.3 Write unit tests for ID translation (REQ-THS-5 scenarios)
- [ ] 9.4 Write unit tests for scope precedence (REQ-THS-3 scenarios)
- [ ] 9.5 Write integration tests for full hook execution via subprocess
- [ ] 9.6 Write atomicity tests verifying no partial writes on error
