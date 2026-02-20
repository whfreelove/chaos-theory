## Context

**Audience**: Claude Code skill authors. This spec uses the term "compaction" intentionally — skill authors working with Claude Code understand that conversation context is periodically compacted, and task descriptions must remain executable without relying on pre-compaction context.

## Why

Creating FSM-enabled skills requires encoding dependency relationships, ensuring each task description is self-contained, and meeting structural conventions — all before the skill does any real work. Skill authors spend time debugging structural errors instead of designing workflows.

## Capabilities

### New Capabilities

- `workflow-intake`: Skill authors can define a workflow from one or both input sources (an existing skill, written step descriptions), with brainstorming as a gap-filling step
- `dependency-mapping`: Skill authors can encode serial, parallel, fan-in, and fan-out execution patterns as task dependencies, and can add, remove, or rename tasks with automatic dependency graph updates and re-validation
- `self-contained-descriptions`: Skill authors can write task descriptions that are fully self-contained — each task is executable without prior conversation context
- `skill-file-generation`: Skill authors can produce a deployable skill consisting of SKILL.md author documentation and an fsm.json task definition file
- `workflow-validation`: Skill authors can verify their workflow incrementally at each phase and through a comprehensive final check before deployment

### Modified Capabilities

None.

## User Impact

### Scope

- Multiple starting points for defining a workflow: analyzing an existing skill, providing written step descriptions, or both — with brainstorming to fill gaps
- Complex dependency patterns including parallel branches and convergence points
- Task descriptions that are self-contained — each task is the sole instruction source once the original skill text is compacted away
- Incremental validation at each phase and a comprehensive final check before deployment
- Produces a deployable FSM skill (SKILL.md + fsm.json)

### Out of Scope

- Modifications to runtime workflow execution behavior
- Changes to workflow file format specifications
- Auto-conversion of existing skills to FSM format
- Visual workflow editors or GUI tools
- Session resumption after workflow interruption

### Known Risks

- Dependency graphs for complex patterns (multi-stage fan-in/fan-out) are error-prone — incremental validation catches errors early
- Task granularity matters: overly broad tasks may lose important details during execution; tasks that are too small create unnecessary overhead — the skill must guide authors toward appropriately-sized tasks
- Intake sources may yield no usable material — brainstorming runs last to fill gaps or generate ideas from scratch; if brainstorming also yields nothing, the workflow terminates gracefully
- Session interruption requires restarting the workflow from the beginning — no resume capability exists

## What Changes

- Skill authors create new FSM skills through a guided workflow that handles structure, dependencies, and descriptions
- Skill authors receive guidance tailored to their starting point — existing skill analysis, written step descriptions, or both — with brainstorming to fill remaining gaps
- The skill validates work at each phase and runs a comprehensive final check before deployment
- Each task description is self-contained and serves as the sole instruction source — the author does not need to manage what context survives after compaction
