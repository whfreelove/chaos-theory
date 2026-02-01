# Resolved Gaps

<!-- GAP TEMPLATE - Same structure as gaps.md:
### GAP-XX: Title
- **Severity**: high|medium|low
- **Description**: ...
- **Category**: resolved
- **Decision**: ...
-->

### GAP-1: Multi-skill task interaction undefined
- **Severity**: medium
- **Description**: Design said "delete all existing task files" when FSM:TASKS detected, but didn't clarify interaction between multiple skills.
- **Category**: resolved
- **Decision**: Hybrid approach: no-op if skill has no fsm.json, track FSM-created tasks via `{"fsm": "skill-name"}` metadata, delete only FSM-tagged tasks when new fsm.json detected, preserve manual tasks. Current implementation deletes ALL FSM-tagged tasks (key existence check only). See GAP-33.

### GAP-2: Symbolic reference resolution rules undefined
- **Severity**: medium
- **Description**: Dependencies use symbolic refs (task subjects) but matching rules unspecified.
- **Category**: resolved
- **Decision**: Exact case-sensitive matching. Duplicate subjects in same block = error. Unresolvable references = validation failure.

### GAP-3: blockedBy output format ambiguous
- **Severity**: medium
- **Description**: Schema showed subject strings but actual task files use numeric IDs.
- **Category**: resolved
- **Decision**: Input uses symbolic refs (subject strings), hook resolves to numeric IDs, output task files contain numeric IDs in blockedBy/blocks arrays.

### GAP-4: Hook input structure unspecified
- **Severity**: high
- **Description**: Format of `tool_result` and FSM:TASKS extraction method unclear.
- **Category**: resolved
- **Decision**: Spike completed. `tool_response` contains `{success, commandName, allowedTools}` — NOT skill content. Design pivoted to companion `fsm.json` file approach.

### GAP-5: Plugin naming and capability unclear
- **Severity**: low
- **Description**: Name "finite-skill-machine" doesn't clearly communicate "task hydration" functionality.
- **Category**: resolved
- **Decision**: Keep "finite-skill-machine" as plugin name. Plugin will contain more components beyond this hook. Name reflects broader vision for skill-based state machines.

### GAP-6: Missing architecture context
- **Severity**: low
- **Description**: Overview jumps to implementation without explaining problem space.
- **Category**: resolved
- **Decision**: Problem space explained in proposal.md. Design document focuses on implementation mechanics. Component-specific rationale documented in situ.

### GAP-7: Silent failure behavior
- **Severity**: medium
- **Description**: Errors caused "write zero tasks" with only stderr output.
- **Category**: resolved
- **Decision**: Explicit failure behavior: hook must FAIL on errors (exit non-zero), agent and user receive notification, all validation errors reported in single message, silent failures rejected.

### GAP-8: ID assignment race condition
- **Severity**: medium
- **Description**: Concurrent hook execution could assign duplicate IDs.
- **Category**: resolved
- **Decision**: Documented assumption: single session, sequential hook execution, no concurrent access to task directory. Claude Code's plugin system executes hooks sequentially.

### GAP-9: Parsing and fail-closed behavior unspecified
- **Severity**: medium
- **Description**: "Write zero tasks" semantics unclear, no parsing algorithm defined.
- **Category**: resolved
- **Decision**: Atomic fail-closed: parse + validate ALL tasks first, only delete + write after full validation success, on any error hook fails, report ALL validation errors in single message.

### GAP-11: Skill directory location unknown
- **Severity**: high
- **Description**: How to locate a skill's directory from `commandName` (e.g., `my-plugin:my-skill`). Must mirror Claude Code's exact skill search order to find the same skill that ran (critical when duplicates exist).
- **Category**: resolved
- **Decision**: Use `~/.claude/plugins/installed_plugins.json` to find plugin installPath. Match scope to cwd (local > project > user priority). For non-plugin skills, check project then personal `.claude/skills/` directories.

### GAP-14: installed_plugins.json error handling undefined
- **Severity**: medium
- **Description**: What happens if `installed_plugins.json` doesn't exist, is malformed JSON, or lacks expected fields? Design uses fail-closed elsewhere but doesn't specify this case.
- **Category**: resolved
- **Decision**: Fail-closed. Hook fails with error if file is missing or malformed. Consistent with fail-closed philosophy.

### GAP-15: Circular dependency detection not specified
- **Severity**: medium
- **Description**: Design validates "Invalid dependency reference (ID not in same file)" but doesn't specify detection of circular dependencies (task 1 blockedBy 2, task 2 blockedBy 1).
- **Category**: resolved
- **Decision**: No detection. Mirrors Claude Code's task system, which also does not detect cycles.

### GAP-18: fsm metadata tag format ambiguity
- **Severity**: medium
- **Description**: Design says FSM-created tasks include `{"fsm": "skill-name"}` in metadata, but also says "detection checks for key existence only." This conflicts with resolved GAP-1, which documented `{"fsm": true}` as the tag format. Is the value `true` (delete all FSM tasks) or `"skill-name"` (delete only current skill's tasks)?
- **Category**: resolved
- **Decision**: Use `{"fsm": "skill-name"}` format. Key existence check detects FSM-created tasks. String value stored for potential future per-skill tracking.

### GAP-21: Skill re-invocation task update behavior
- **Severity**: medium
- **Description**: What happens if same skill is invoked twice in same session? Design says "New skill invocation replaces all previous FSM-created tasks" but doesn't specify: Does this mean re-hydration from fsm.json (fresh task set)? What if agent has already updated some tasks (status, owner, metadata)? Are those changes lost?
- **Category**: resolved
- **Decision**: Fresh hydration on re-invocation. All FSM-tagged tasks deleted and replaced with fresh tasks from fsm.json. Agent modifications ARE LOST. Re-invoking = "reset this workflow."

### GAP-27: Task file JSON schema format undefined
- **Severity**: high
- **Description**: Hook writes task files to `~/.claude/tasks/{session_id}/{id}.json` but the complete JSON schema for these files is not specified in the design. Without knowing the exact task file format, the hook cannot be implemented correctly.
- **Category**: resolved
- **Decision**: Documented exact task file schema in design.md § "Task File Schema" based on spike. Key discovery: `id` is a STRING, not a number.

### GAP-29: Testing strategy and tooling undefined
- **Severity**: high
- **Description**: Design explains hook architecture and components but provides no guidance on testing approach: no test framework specified, no methodology for simulating hook input/output, no E2E/integration test strategy, no guidance on verifying behavior correctness.
- **Category**: resolved
- **Decision**: pytest as test framework, tmpdir/tmp_path fixtures for filesystem operations, JSON fixtures for test data, subprocess execution for integration tests, no external dependencies beyond pytest.

### GAP-30: Hook-specific testing guidance missing
- **Severity**: medium
- **Description**: Several implementation-specific testing challenges lack guidance: testing atomic fail-closed behavior, testing installed_plugins.json resolution with scope precedence, simulating different hook execution contexts.
- **Category**: resolved
- **Decision**: Added hook-specific testing patterns: fixture patterns for task directories, installed_plugins.json fixtures with controlled scope entries, subprocess execution pattern, explicit atomicity test pattern.

### GAP-33: Multi-skill FSM task deletion scope ambiguous
- **Severity**: medium
- **Description**: Design states "Detection checks for key existence only" for identifying FSM-tagged tasks to delete, but also stores the skill name value in metadata (`{"fsm": "skill-name"}`). This creates ambiguity: when skill B is invoked, does it delete ALL tasks with an `fsm` metadata key, or only tasks where `fsm` equals skill B's name?
- **Category**: resolved
- **Decision**: Deletion checks for key existence only - any task with `fsm` metadata key is deleted when ANY skill with fsm.json is invoked. Skill name value stored for potential future use but not used for scoping deletion.

### GAP-17: Deletion failure recovery unspecified
- **Severity**: medium
- **Description**: Design specifies atomic fail-closed behavior where validation must succeed before deletion and writes occur. However, resolved GAP-9 only covers validation-first ordering. What happens if validation passes but deletion of FSM-tagged tasks fails?
- **Category**: resolved
- **Decision**: Keep fail-closed, add explicit error message. If deletion fails, fail with clear error: "Failed to delete task {id}: {error}. Manual cleanup required at ~/.claude/tasks/{session_id}/". Update design.md Error Handling section.

### GAP-34: Plugin scope filtering spec scenarios missing
- **Severity**: medium
- **Description**: Design specifies installed_plugins.json scope filtering with projectPath matching (local > project > user priority), but no Gherkin scenarios validate this behavior. Need scenarios covering: plugin exists in multiple scopes (local wins), plugin exists only in project scope, plugin exists only in user scope, and projectPath matching logic.
- **Category**: resolved
- **Decision**: Expand SCN-THS-3.1 Examples table with additional rows: local-only, project-only, user-only, projectPath matching, projectPath non-matching.

### GAP-35: Missing plugin entry behavior undefined
- **Severity**: medium
- **Description**: What happens if installed_plugins.json exists and is valid JSON, but does not contain an entry for the plugin specified in commandName? Design specifies fail-closed for missing/malformed file (GAP-14 resolution) but not for missing plugin entry within valid file.
- **Category**: resolved
- **Decision**: Fall back to non-plugin lookup. If plugin not found in installed_plugins.json, treat commandName as non-plugin skill: check {cwd}/.claude/skills/{skill}/ then ~/.claude/skills/{skill}/. Update design.md Skill Location section and add spec scenario.

### GAP-36: Hook stdin parsing spec scenarios missing
- **Severity**: high
- **Description**: No Gherkin scenarios validate that the hook correctly parses the input JSON schema from stdin. The hook relies on extracting `tool_response.commandName` and `session_id` from stdin, but no spec validates this parsing logic works correctly with the actual hook input format.
- **Category**: resolved
- **Decision**: Extend REQ-THS-1 with parsing scenarios: valid input parsed correctly, missing session_id fails, missing commandName fails, malformed JSON fails.

### GAP-37: Task file write success spec scenarios missing
- **Severity**: medium
- **Description**: No Gherkin scenarios validate that task files are written to the correct path with correct content. Current specs focus on validation failures and edge cases, but don't verify the happy path: files written to `~/.claude/tasks/{session_id}/{id}.json` with expected JSON structure.
- **Category**: resolved
- **Decision**: Add SCN-THS-4.7 extending "Valid fsm.json creates tasks" to verify: correct path (~/.claude/tasks/{session_id}/{id}.json), correct JSON structure, correct field values including string IDs and fsm metadata tag.

### GAP-41: installed_plugins.json missing vs plugin-not-found behavior conflated
- **Severity**: low
- **Description**: GAP-14 (resolved) states "fail-closed if file is missing or malformed" while GAP-35 (resolved) states "fall back to non-plugin lookup if plugin not found". The design wording conflates two distinct scenarios: (1) installed_plugins.json file doesn't exist, (2) file exists but plugin entry not found. Current wording could cause implementers to apply fallback when file is missing. Clarify: file missing = fail-closed with error "skill as written doesn't exist"; file exists but plugin not found = fall back to non-plugin lookup.
- **Category**: resolved
- **Decision**: Updated design.md Skill Location section to restructure into two explicit scenarios: (1) "installed_plugins.json missing or malformed" → fail-closed with error "Skill '{commandName}' not found - installed_plugins.json is missing or malformed"; (2) "Plugin not found in valid installed_plugins.json" → fall back to non-plugin skill lookup.
