## Why

Skills can define multi-step workflows, but getting tasks into the TaskList requires the agent to interpret definitions and create each task manually. This burns context, introduces variability, and limits what simpler/faster models can handle. Task hydration should be automatic and consistent.

## Capabilities

- `task-hydration-skill`: Automatic task creation from skill-defined workflows
- `v2-registry-parsing`: FSM can locate plugin install paths from the current `installed_plugins.json` format (version 2)
- `v1-registry-deprecation`: FSM still reads the legacy array-based registry format but emits a deprecation notice advising the user to update
- `scoped-task-management`: Skill authors can invoke multiple skills in the same session without cross-contamination — each skill's tasks are managed independently
- `active-work-protection`: Agents receive an explicit abort when re-invocation would destroy a partially-completed workflow, instead of silent data loss
- `CAP-session-bypass`: Developer can temporarily allow skill file access for the current shell session without disabling the plugin.
- `CAP-actionable-denial`: Developer sees how to allow skill file access directly in the denial message instead of being told to disable the whole plugin.

Cross-cutting test infrastructure capabilities (`contributor-reproduces-environment`, `ci-validates-pr`) are defined in `openspec/common/`.

## User Impact

### Scope

- **Skill authors** can ship complete task workflows via an `fsm.json` companion file; users get a ready-to-execute checklist on skill load
- **Users** see consistent task lists regardless of which model runs the skill
- **Simpler models** can handle complex workflows since task setup is automatic
- Plugin skills (`plugin:skill` invocations) that depend on install-path resolution start working again
- Users on the legacy registry format see a deprecation notice on each plugin skill invocation but experience no breakage
- Multi-skill sessions become safe: invoking skill-b no longer destroys skill-a's task workflow
- Re-invocation of a skill with a partially-completed workflow produces an explicit abort message instead of silent data loss
- Developers working on skill files (SKILL.md, fsm.json, hooks.json) who hit the deny wall during plugin or skill development can temporarily allow access for the current shell session without disabling the plugin.

### Out of Scope

- Changes to the `installed_plugins.json` format itself (owned by Claude Code, not this project)
- Migration tooling that converts v1 files to v2
- Multi-scope precedence changes (local > project > user priority stays the same)
- Changes to non-plugin skill resolution (local `.claude/skills/` lookup is unaffected)
- Explicit cross-skill ID conflict detection (offset prevents collisions by construction)
- Merge/reconciliation strategies for re-invoked skills (abort is the chosen behavior)
- Manual task management or task archival
- Concurrent skill invocations (parallel hook execution against the same session's task directory)
- Persistent bypass configuration changes
- Plugin-level enable/disable

### Current Limitations

- session_id edge cases (missing/null behavior)
- Skill name containing `:` character and sibling directory path matching
- Pre-setting task status/owner field semantics
- Custom metadata field governance
- Partial write failure recovery automation
- Optional field default inference by Claude Code task system
- ID translation base for empty directories
- skills/ vs commands/ directory precedence when both contain fsm.json
- Non-plugin skill location precedence (first-match-wins ambiguity)
- `blocks` field validation and ID translation parity with `blockedBy`
- Non-numeric task file handling during max ID calculation
- Task file read failure during FSM tag detection
- projectPath normalization for scope matching
- fsm.json root structure type validation (non-array root)
- Empty fsm.json array behavior
- Non-sequential local ID handling
- Skill rename implications on ID offset calculation
- Test scenario atomicity optimization
- Exhaustive abort message forbidden-term test coverage
- Write failure recovery test strategies (transient vs persistent I/O failures)
- Exhaustive allowlist reject-by-default test coverage
- Changes to which file patterns are blocked
- Individual denial message field coverage beyond the primary developer-visible text

### Planned Future Work

### Known Risks

- Dependency on `installed_plugins.json` internal format — may need hook updates if Claude Code changes this format
- **Format may change again**: the v2 format is an internal Claude Code file with no stability guarantee; a future v3 would require another update
- **Deprecation notice noise**: users who cannot control their registry format (e.g., pinned Claude Code version) will see the notice on every invocation with no way to act on it
- **Abort may frustrate rapid iteration**: developers re-invoking a skill during development will hit the guard if the workflow is partially complete; they'll need to resolve all tasks first. Re-invocation is allowed when the workflow has fully completed or hasn't started yet
- **Orphaned tasks from removed skills**: if a skill is uninstalled, its FSM tasks remain with no skill to clean them up (existing behavior, not introduced by this change)
- **Session bypass forgotten**: a developer who sets the bypass env var and forgets may have reduced protection for the rest of the session. This is acceptable because the access gate is a development guardrail, not a security boundary.

Test infrastructure risks (monorepo cross-contamination, version file validation, CI failure disambiguation, missing venv activation, exit code chain assumption, empty test discovery) are documented in `openspec/common/functional.md` Known Risks.

## Overview

- PostToolUse hook on the Skill tool reads a companion `fsm.json` file and hydrates the TaskList automatically
- Skills include `fsm.json` alongside `SKILL.md` to define task workflows
- Task dependencies use local numeric IDs in fsm.json, translated to actual string IDs at hydration time
- PreToolUse guard prevents the agent from reading SKILL.md/fsm.json directly; when access is denied, the message tells the developer how to set the bypass environment variable to allow access for the current session
- Setting a shell environment variable allows skill file access for the current session without disabling the plugin
- Plugin skill invocations (`plugin:skill`) resolve correctly against the current registry format instead of erroring out
- The legacy array-based registry format continues to work but now produces a deprecation notice on each use
- Error messages for genuinely missing or malformed registry files remain unchanged
- Each skill's tasks are managed independently using scoped task directories — invoking one skill does not affect another skill's tasks
- Re-invoking a skill with a partially-completed workflow aborts with an error identifying the blocking tasks, protecting work in progress from silent data loss
- The abort error provides the agent with the specific task IDs that must be resolved before re-invocation can proceed

Test infrastructure overview (dependencies, test execution, CI, README) is documented in `openspec/common/functional.md`.
