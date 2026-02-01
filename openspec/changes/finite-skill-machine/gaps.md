# Gaps

<!-- GAP TEMPLATE - Fields by workflow stage:
CRITIQUE adds: ID, Severity, Description
RESOLVE adds: Category, Decision

New gaps from critique should NOT have Category or Decision fields.
-->

### GAP-12: session_id availability not verified
- **Severity**: low
- **Description**: Hook relies on `session_id` from input to determine task directory path. Design doesn't specify behavior if session_id is missing or null.
- **Category**: defer-release
- **Decision**: Accept as MVP limitation. session_id has been stable in observed hook inputs. Add defensive check that logs warning and exits no-op if missing.

### GAP-13: Skill location edge cases unspecified
- **Severity**: low
- **Description**: commandName parsing when skill name contains `:` character (e.g., `my-plugin:my:skill`). Path matching for "contains" could incorrectly match sibling directories (e.g., `/foo/bar` matching `/foo/bar-baz`).
- **Category**: defer-release
- **Decision**: Use canonical path comparison (resolve symlinks, normalize). For commandName parsing, split on first `:` only. Document as limitation.

### GAP-16: installed_plugins.json format stability unknown
- **Severity**: low
- **Description**: Hook relies on Claude Code's internal `~/.claude/plugins/installed_plugins.json` file format for skill location. Design notes "May need updates if format changes" but does not specify detection or migration strategy for format changes.
- **Category**: defer-release
- **Decision**: Accept as known limitation. Format changes would require hook updates. Design already documents this dependency.

### GAP-19: Task status and owner field behavior unspecified
- **Severity**: low
- **Description**: Schema shows `status` and `owner` as optional fields in fsm.json. Can skills pre-set status to `in_progress` or `completed`? Can skills pre-assign owner? What are valid use cases for setting these vs leaving defaults?
- **Category**: defer-release
- **Decision**: Non-critical feature clarification. Skill authors can experiment; behavior can be documented later based on real usage patterns.

### GAP-20: Task metadata field purpose unclear
- **Severity**: low
- **Description**: Schema allows arbitrary metadata object in fsm.json. Design specifies hook adds `{"fsm": "..."}` tag. Should skills be able to add custom metadata fields, or is metadata reserved for FSM system use?
- **Category**: defer-release
- **Decision**: Schema allows arbitrary metadata; no harm in permitting custom fields alongside FSM's tag.

### GAP-22: Partial task completion error surface missing
- **Severity**: low
- **Description**: Design uses atomic fail-closed: validation passes → delete all FSM tasks → write new tasks. If write succeeds for tasks 1-3 but fails on task 4, what is the error state? Some tasks exist, some don't, but hook has already deleted old tasks.
- **Category**: defer-release
- **Decision**: If write fails mid-batch after deletion, some new tasks exist but old ones are gone. This is a known filesystem error state requiring manual recovery. Consistent with fail-closed philosophy.

### GAP-23: Optional field default behavior unspecified
- **Severity**: low
- **Description**: Schema shows several optional fields with defaults: `status` (default: `pending`), `owner`, `description`, `activeForm`, and `metadata`. Must hook write these fields explicitly to task files when omitted in fsm.json, or can they be omitted and inferred by Claude Code's task system? What are the default values for owner/description/activeForm when not specified in fsm.json?
- **Category**: defer-release
- **Decision**: Implementation detail. Hook will write explicit values for all optional fields for consistency. Status defaults to "pending", owner/description/activeForm default to empty string, metadata defaults to empty object (with fsm tag added).

### GAP-24: ID translation base value for empty task directory
- **Severity**: low
- **Description**: Design says "find max ID (call it `base`)" then `actual_id = base + local_id`. What is base if task directory is empty (no existing tasks)? Is it 0 (first task becomes ID 1) or -1 (first task becomes ID 0)?
- **Category**: defer-release
- **Decision**: Empty task directory means base=0, so first local ID 1 becomes actual ID 1. Standard max() behavior on empty set.

### GAP-25: skills vs commands directory precedence unspecified
- **Severity**: low
- **Description**: Design specifies checking for fsm.json in both `{installPath}/skills/{skill}/fsm.json` and `{installPath}/commands/{skill}/fsm.json` with the condition "if command is a directory". Two ambiguities: (1) What if fsm.json exists in both locations? Which takes precedence? (2) The phrase "if command is a directory" is unclear - does it mean the commands path is only checked when the command is implemented as a directory rather than a single file?
- **Category**: defer-release
- **Decision**: Acknowledge gap as acceptable for MVP, defer to future release

### GAP-26: Non-plugin skill location precedence unspecified
- **Severity**: low
- **Description**: Design says to check `{cwd}/.claude/skills/{skill}/fsm.json` then `~/.claude/skills/{skill}/fsm.json` for non-plugin skills. Implicit assumption is "first match wins" but not explicitly stated. What happens if fsm.json exists in both project and user skill directories?
- **Category**: defer-release
- **Decision**: Acknowledge gap as acceptable for MVP, defer to future release

### GAP-28: Gherkin spec violates "One Scenario = One Behavior" principle
- **Severity**: low
- **Description**: SCN-THS-3.1 in specs/task-hydration-service/spec.md uses Scenario Outline with Examples table to test multiple precedence rules in a single scenario. This violates the Gherkin principle that each scenario should test one specific behavior. Each precedence rule (local>project>user, plugin>non-plugin) should be its own scenario with concrete Given-When-Then steps for better clarity and debugging.
- **Category**: defer-release
- **Decision**: Acknowledge gap as acceptable for MVP, defer to future release.

### GAP-31: blocks field validation missing from spec
- **Severity**: low
- **Description**: SCN-THS-4.5 specifies that invalid `blockedBy` references fail validation, but the spec does not cover validation of `blocks` references. The design schema (fsm.json Format) shows both `blockedBy` and `blocks` can contain dependency references. An invalid ID in `blocks` should also trigger validation failure for consistency.
- **Category**: defer-release
- **Decision**: Acknowledge gap as acceptable for MVP, defer to future release.

### GAP-32: blocks field ID translation missing from spec
- **Severity**: low
- **Description**: REQ-THS-5 and SCN-THS-5.3 only demonstrate ID translation for `blockedBy` arrays. The design schema shows `blocks` also uses local IDs that require translation to actual IDs. No scenario covers `blocks` field translation behavior.
- **Category**: defer-release
- **Decision**: Acknowledge gap as acceptable for MVP, defer to future release.

### GAP-38: Non-numeric task file handling unspecified
- **Severity**: low
- **Description**: Design specifies "find max ID" from existing task files to calculate ID offset, but doesn't specify behavior when task directory contains files with non-numeric IDs or non-standard filenames (e.g., "temp.json", "backup-1.json", "abc.json"). Should these be ignored, cause an error, or be handled differently?
- **Category**: defer-release
- **Decision**: Ignore non-numeric filenames when calculating max ID. Only files matching pattern `^\d+\.json$` are considered task files. Consistent with Claude Code's task file naming convention.

### GAP-39: Task file read failure during FSM tag detection unspecified
- **Severity**: low
- **Description**: REQ-THS-7 requires reading existing task files to check for fsm metadata key before deletion. Design doesn't specify behavior if a task file exists but cannot be read (corrupted JSON, permission denied, file locked). Should the hook fail-closed, skip the unreadable file, or treat it as non-FSM?
- **Category**: defer-release
- **Decision**: Fail-closed on read errors. Consistent with design's fail-closed philosophy. Hook should fail with clear error message identifying the unreadable file.

### GAP-40: projectPath normalization for scope matching unspecified
- **Severity**: low
- **Description**: Design specifies projectPath "must match or contain" cwd for local/project scope filtering, but doesn't specify path normalization rules. Potential ambiguities include: trailing slash handling ("/projects/myapp" vs "/projects/myapp/"), symlink resolution, and case sensitivity on case-insensitive filesystems (macOS). GAP-13 addresses skill path normalization but not projectPath matching.
- **Category**: defer-release
- **Decision**: Apply same normalization as GAP-13: resolve symlinks, normalize paths, strip trailing slashes before comparison. Case sensitivity follows filesystem behavior (case-insensitive on macOS).

### GAP-42: No-op detection across skill location paths not explicitly tasked
- **Severity**: low
- **Description**: Design specifies "If no fsm.json found, no-op (skill has no predefined tasks)" but no task explicitly covers implementing this detection logic. The no-op case must be detected after exhausting all location checks (plugin skills/, commands/, non-plugin project, non-plugin user, fallback paths). Task 8.2 covers the response but not the detection logic itself.
- **Category**: defer-release
- **Decision**: Acknowledge gap as acceptable for MVP, defer to future release.

### GAP-43: Error aggregation testing not explicitly tasked
- **Severity**: low
- **Description**: SCN-THS-4.6 requires "Multiple errors reported together" and design specifies "Aggregate multiple errors into single failure message", but Task 9.2 "Write unit tests for fsm.json validation (REQ-THS-4 scenarios)" doesn't explicitly call out testing the aggregation behavior. Need test cases verifying: multiple missing fields reported together, duplicate IDs AND invalid dependencies both reported, error message format for aggregated errors.
- **Category**: defer-release
- **Decision**: Acknowledge gap as acceptable for MVP, defer to future release.

### GAP-44: fsm.json root structure validation unspecified
- **Severity**: low
- **Description**: Design shows fsm.json as a JSON array at root level (lines 19-32), and error handling specifies "Malformed JSON in fsm.json" triggers failure. However, there's no explicit validation that fsm.json must be an array. What happens if fsm.json contains valid JSON but wrong type (e.g., `{"tasks": [...]}` object, or `"string"`, or `123`)? Should this fail validation or attempt to process it?
- **Category**: defer-release
- **Decision**: Acknowledge gap as acceptable for MVP, defer to future release.

### GAP-45: Empty fsm.json array behavior unspecified
- **Severity**: low
- **Description**: Design doesn't specify behavior when fsm.json is an empty array `[]`. Should this trigger no-op (equivalent to missing fsm.json), delete all FSM-tagged tasks and write nothing (consistent with fresh hydration), or fail validation (no tasks to hydrate)?
- **Category**: defer-release
- **Decision**: Acknowledge gap as acceptable for MVP, defer to future release.

### GAP-46: Non-sequential local ID handling unspecified
- **Severity**: low
- **Description**: Schema describes `id` field as "Local offset ID (1, 2, 3...)" (line 39), suggesting sequential numbering, and all examples use sequential IDs (1, 2, 3). However, no validation rule explicitly requires IDs to be sequential or start from 1. What happens if fsm.json has non-sequential IDs (e.g., [1, 5, 10]) or starts from 0? Are these valid or should they trigger validation failure?
- **Category**: defer-release
- **Decision**: Acknowledge gap as acceptable for MVP, defer to future release.

