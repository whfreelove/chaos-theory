`@post-tool-hook`
# Feature: post-tool-hook

The PostToolUse hook fires on Write and Edit tool calls. It maintains embedded metadata in the
plan file: session marker injection, content hash tracking, and verdict signal conversion.
The hook fails open — it exits silently on errors so the PreToolUse hook enforces at exit time.

---

`@post-tool-hook:1`
## Rule: Hook activation

### Scenario: Edit outside plan mode

- Given the agent is not in plan mode
- When the agent edits any file
- Then the hook SHALL NOT run

### Scenario: Edit non-plan file in plan mode

- Given the agent is in plan mode
- When the agent edits a file outside `~/.claude/plans/`
- Then the hook SHALL NOT run

### Scenario: Edit plan file in plan mode

- Given the agent is in plan mode
- When the agent edits a file in `~/.claude/plans/`
- Then the hook runs and maintains metadata

---

`@post-tool-hook:2`
## Rule: Metadata maintenance

### Background

- Given the agent is in plan mode
- And the agent edits a file in `~/.claude/plans/`

### Scenario: First edit injects session marker

- Given the plan file lacks a session marker
- When the hook processes the edit
- Then the hook injects `<!-- rodin:session=<session_id> -->` at the end of the file

### Scenario: Edit updates plan and gaps hashes

- Given the plan file has rodin metadata
- When the hook processes the edit
- Then the hook recomputes and updates the plan content hash
- And the hook recomputes and updates the gaps content hash

### Scenario: Verdict signal converted to validation metadata

- Given the plan file contains a `<!-- rodin:verdict:signal=... -->` comment
- When the hook processes the edit
- Then the signal is converted to `<!-- rodin:validation=... -->` metadata with a timestamp
- And the verdict signal comment is removed from the file

### Scenario: Content change resets validation to pending

- Given the plan file lacks a verdict signal
- When the hook processes the edit
- Then the validation status is set to `pending`
