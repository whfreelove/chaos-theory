## Why

Creating FSM-enabled skills requires understanding the structural conventions, encoding dependency relationships between tasks, and ensuring each step's description is self-contained enough to be the sole instruction source after context compaction. Skill authors spend time debugging structural errors instead of designing workflows.

## Capabilities

### New Capabilities

- `workflow-intake`: Skill authors can transform workflows from two input-based sources — existing skills and written step descriptions — with brainstorming as a gap-filling step that builds on whatever material the input-based sources produced, reviewing and resolving overlaps during the normalization confirmation step when material spans multiple sources
- `dependency-mapping`: Skill authors can encode serial, parallel, fan-in, and fan-out execution patterns as task dependencies that preserve intended workflow order, and can add, remove, or rename tasks during dependency mapping with automatic updates to the dependency graph and prompted author interaction for new dependency relationships, plus re-validation
- `self-contained-descriptions`: Skill authors can write small, focused task descriptions where each task contains all context needed to execute independently — the sole source of truth once the original skill text is compacted away — and can split tasks during description writing, with inherited dependency relationships and post-split re-validation
- `skill-file-generation`: Skill authors can produce a deployable skill with author-facing documentation and a structured workflow definition
- `workflow-validation`: Skill authors can verify generated workflows incrementally — including feedback on each description's completeness as it is written — and through a comprehensive final check before deployment

### Modified Capabilities

None.

## User Impact

### Scope

- Supports multiple starting points for defining a workflow: analyzing an existing skill, providing written step descriptions, or both — with brainstorming to fill gaps from whatever material those starting points produce
- Complex workflows with parallel branches and convergence points
- Self-contained task descriptions where each task is the sole source of truth when the agent picks it up
- Validates work at each step and runs a comprehensive final check before deployment
- Produces a deployable skill in the FSM plugin

### Out of Scope

- Modifications to runtime workflow execution behavior
- Changes to workflow file format specifications
- Runtime workflow modification after task creation
- Auto-conversion of all existing skills to FSM format
- Visual workflow editors or GUI tools
- Exact wording of how capabilities are described to skill authors
- Verifiable criteria distinguishing "targeted questions" from "generic questions" in brainstorming intake guidance (workflow-intake:4.2)
- Session resumption or recovery after workflow interruption
- Recovery when all intermediate work is lost from the conversation — the skill validates at each step, making total loss unlikely; recovery is deferred to a future release
- Upper limit on how large the in-progress workflow artifact can grow — real-world usage will reveal actual limits before a formal boundary is needed
- Verification of SKILL.md body content completeness — the skill verifies frontmatter structure; body content coverage is not enforced
- Precise boundary between minor formatting adjustments and substantive content changes during written step intake
- SKILL.md body content template or section structure guidelines — body structure is flexible as long as content uses author-facing language without internal identifiers
- Author-initiated cancellation during a workflow phase — the existing confirmation gates naturally handle this; the skill waits for the author's response at each step

### Known Risks

- Dependency graphs for complex patterns (multi-stage fan-in/fan-out) are error-prone — incremental validation catches errors early
- The intake pipeline (two input-based sources plus brainstorming gap-filling) increases skill complexity — each step must be thorough enough to stand alone
- Task granularity matters: overly broad tasks may lose important details during execution, while tasks that are too small create unnecessary overhead — the skill must guide authors toward appropriately-sized tasks
- Input-based intake sources may yield no usable material — brainstorming runs sequentially after them to fill gaps or generate ideas from scratch; if brainstorming also yields nothing, the workflow terminates gracefully
- Session interruption requires restarting the workflow from the beginning — no resume capability exists
- Large workflows may have poor UX during dependency mapping when presenting all tasks for relationship specification — the skill warns the author and suggests grouping related tasks for review, but no hard upper limit is enforced. Requirements-level coverage for the large-workflow warning behavior is deferred to future usage validation
- Authoring-time file writes may trigger the FSM plugin's active-work protection — the plugin monitors the skill folder for in-progress tasks, and a partially written fsm.json could be detected. The skill validates at each step before writing files, making this unlikely since files are written near the end of the workflow

## Brainstorming Gap Taxonomy

The Brainstorming Gap Taxonomy is a post-hoc evaluation framework, not an intake-time detection mechanism. The four categories below are used when verifiers evaluate whether brainstorming effectively filled gaps in prior intake material — not when the intake process itself runs. During intake, the brainstorming step simply identifies gaps and fills them; these categories structure how verifiers assess whether that gap-filling was thorough.

When evaluating brainstorming effectiveness, verifiers assess against four categories:

1. **Structural gaps** — Missing workflow phases. The intake material describes some phases of the workflow but omits entire phases that a complete workflow would include (e.g., intake material covers setup and execution but has no validation or cleanup phase).
2. **Depth gaps** — Phases with insufficient detail to act on. A phase is named or mentioned but lacks enough specificity for an agent to execute it (e.g., "handle configuration" without specifying what configuration actions are performed).
3. **Coverage gaps** — Workflow paths not represented. The intake material covers the primary path but omits alternative paths, error paths, or conditional branches that the workflow must handle (e.g., only the success path is described, with no guidance for what happens when validation fails).
4. **Consistency gaps** — Contradictions between steps. Two or more steps describe conflicting actions, expectations, or sequencing (e.g., one step says "validate before writing" while another says "write first, validate after").

These categories provide a concrete checklist for evaluating whether the brainstorming step correctly identified all gaps in the prior intake material.

## What Changes

- Skill authors create new FSM skills through a guided workflow that handles structure, dependencies, and descriptions
- Two input-based intake paths provide dedicated guidance for each source type (existing skill, written steps), with brainstorming as a gap-filling step that builds on prior intake material
- The skill validates work at each phase and runs a comprehensive final check before deployment
- Each task description is self-contained and serves as the sole instruction source — the author does not need to worry about what context survives after compaction
- **Capability boundary expansion**: This change expands the FSM plugin's capability boundary to include authoring-time file production — the skill generates SKILL.md and fsm.json files on disk. The project-level functional description will be updated at merge time to reflect the expanded boundary
