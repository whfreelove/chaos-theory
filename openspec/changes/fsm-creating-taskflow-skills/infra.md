## Context

The FSM plugin is a local Claude Code plugin with no deployment infrastructure. This change adds a new skill (`finite-skill-machine:creating-taskflow-skills`) that ships as a SKILL.md + fsm.json companion pair — pure content files with no code changes to `hydrate-tasks.py` or the hook system. The existing test infrastructure (pytest with subprocess-based `run_hook()`, `tmp_path` isolation) is not extended because the deliverables are content, not code.

## Objectives

`OBJ-structural-validity`: The delivered fsm.json passes the existing `validate_fsm_tasks` validation in `hydrate-tasks.py` — valid JSON array, required fields present (including `description`), unique IDs, all `blockedBy` references resolve.

`OBJ-requirements-coverage`: Each requirement capability has a documented verification approach.

## Deployment

This change deploys via merge to main. The delivered files are placed at `plugins/finite-skill-machine/skills/creating-taskflow-skills/` — one SKILL.md and one fsm.json. No rollout strategy, feature flags, or deployment sequencing — new additive files only.

## Testing strategy

### Verification modes

This change has two distinct verification modes:

1. **Structural validation** (automated at runtime): The fsm.json is validated by the existing `validate_fsm_tasks` function when the skill is invoked via `hydrate-tasks.py`. This catches structural defects — missing required fields, duplicate IDs, dangling `blockedBy` references, invalid JSON — without needing new test code. The `description` field SHALL be added to `validate_fsm_tasks` required field checks as part of this change so that empty or missing descriptions are caught at hydration time.

2. **Behavioral verification** (manual, author-driven): The 5 requirement capabilities describe agent behavior during the guided workflow. These are verified by invoking the skill and observing agent behavior, not by automated tests. The "code under test" is the agent following task descriptions, not a Python function.

No new pytest tests are added. The structural validation path already exists in the hydration pipeline; behavioral verification is inherently manual because the outputs are agent actions guided by prose descriptions.

**Integration verification exclusion**: No integration test scenarios are defined for this change. The five capabilities form a sequential pipeline with validation gates, not bidirectional interactions that produce emergent behavior. Cross-capability coverage is captured by single-capability requirements. See `integration.feature.md` for the full rationale.

### Relationship to tasks.yaml

The verification approaches documented in infra.md's Coverage by capability tables define *what* to verify and *how*. The `behavioral-verification` group in tasks.yaml provides *actionable implementation tasks* that execute these verification approaches — one task per capability. Each behavioral verification task derives its procedure from the corresponding capability's coverage table in this document.

### Verification by design: AskUserQuestion confirmation gates

Multiple requirements specify that "the skill does not proceed until the author approves" (workflow-intake:2.3, 4.3, dependency-mapping:4.3). These confirmation gates use AskUserQuestion (or equivalent user prompt) as the blocking mechanism. **AskUserQuestion is inherently blocking** — the skill literally cannot proceed without a user response. The agent's execution pauses at the prompt and does not resume until the author provides input.

This means the blocking behavior is **guaranteed by construction**, not by testing. There is no code path where the skill could bypass a confirmation gate, because the underlying mechanism (waiting for user input) is a fundamental property of the execution model. Accordingly, no specific test infrastructure is needed to verify that confirmation gates block — the verification is that the mechanism exists in the task description, which is covered by behavioral verification.

### Coverage by capability

#### `workflow-intake`

| Rule | What it covers | Verification approach |
|------|---------------|----------------------|
| Rule 1: Input-based sources and brainstorming gap-filling | Source-specific guidance for existing skill, written steps; brainstorming gap-filling after input-based intakes; convergence to normalized step list | Manual: invoke skill with each intake type, verify guidance is source-specific; verify brainstorming reviews prior intake material and fills gaps; verify convergence produces a normalized step list |
| Rule 2: Existing skill transformation | Sequential step extraction, implicit parallelism identification, conditional logic decomposition (author chooses strategy), author review gate | Manual: provide an existing skill as input, verify extracted steps match the skill's structure; provide a skill with conditional branching, verify the skill presents decomposition options and incorporates the author's choice |
| Rule 3: Written step description intake | Well-structured acceptance, vague description prompting, overly large step splitting | Manual: provide written steps of varying quality, verify the skill prompts for clarification or splitting as appropriate |
| Rule 4: Brainstorming gap-filling | Gap identification from prior intake material; unordered idea organization when no prior material exists; overlapping idea consolidation; author confirmation gate; graceful termination when no steps emerge | Manual: invoke skill with input-based material, verify brainstorming identifies gaps and proposes additions; invoke skill with no input-based material, verify brainstorming guides from scratch; verify graceful termination when no steps emerge |

#### `dependency-mapping`

| Rule | What it covers | Verification approach |
|------|---------------|----------------------|
| Rule 1: Serial execution patterns | Linear chain encoding, explicit ordering for ambiguous steps | Manual: define a linear workflow, verify blocking relationships are encoded correctly |
| Rule 2: Parallel execution patterns | Independent task identification, parallel grouping confirmation | Manual: define independent tasks, verify no blocking relationships between them |
| Rule 3: Fan-in and fan-out patterns | Fan-out from single predecessor, fan-in to single successor, diamond pattern | Manual: define fan-out/fan-in workflows, verify dependency graph captures convergence and divergence |
| Rule 4: Author confirmation of graph | Dependency summary presentation, modification after review, approval gate | Manual: verify the skill presents a complete dependency summary and allows modifications |
| Rule 5: Step list modifications during dependency mapping | Author removes a task (graph updated, dangling refs removed); author adds a task (graph updated, new relationships prompted); author renames a task (label updated, relationships preserved); re-validation after each modification | Manual: during dependency mapping, remove a task and verify graph updates correctly; add a task and verify the skill prompts for blocking relationships with all existing tasks (predecessors and successors); rename a task and verify existing dependencies preserved |

#### `self-contained-descriptions`

| Rule | What it covers | Verification approach |
|------|---------------|----------------------|
| Rule 1: Sole instruction source | Self-contained descriptions accepted; missing context flagged; external references ("as described in the skill") caught; author can revise previously approved descriptions with re-validation; tasks presented one at a time in dependency order with skip and return navigation | Manual: write descriptions with and without external references, verify the skill flags non-self-contained ones; revise an approved description, verify re-validation runs; verify tasks are presented in dependency order and author can skip or return to previous tasks |
| Rule 2: No inter-task references | Named task references, "the previous task" references, implicit ordering assumptions | Manual: write descriptions referencing sibling tasks, verify the skill flags each reference type |
| Rule 3: Appropriate task sizing | Overly large descriptions prompt splitting; overly small prompt merging; appropriate size accepted | Manual: write descriptions of varying sizes, verify the skill recommends splitting, merging, or accepts as appropriate |
| Rule 4: activeForm auto-generation | Present-continuous form derived from task label; author confirmation or override; author-provided overrides accepted as-is without format validation (4.2) | Manual: define tasks with labels, verify the skill generates activeForm and allows override; override with non-present-continuous text and verify the skill accepts it without validation |

#### `skill-file-generation`

| Rule | What it covers | Verification approach |
|------|---------------|----------------------|
| Rule 1: SKILL.md generation | Valid YAML frontmatter with `name` and `description`; author-facing body language; correct directory placement; self-validation failure (missing frontmatter) triggers author correction and re-validation before SKILL.md is finalized | Manual: complete the workflow, verify generated SKILL.md has frontmatter and describes steps without internal identifiers; verify that a self-validation failure triggers author correction and re-validation before SKILL.md is finalized |
| Rule 2: Task definition file generation | All workflow steps present; dependencies encoded correctly; required fields (`id`, `subject`, `description`) per entry; display-friendly names auto-normalized to directory-safe format with author confirmation | Structural: `validate_fsm_tasks` checks required fields, unique IDs, and `blockedBy` resolution at runtime. Manual: verify step count matches workflow definition; provide a display-friendly name, verify normalization and confirmation prompt |
| Rule 3: Correct directory structure | Files placed under `plugins/<plugin>/skills/<skill>/`; SKILL.md and fsm.json colocated; target directory created if it does not exist; existing directory detected with overwrite/rename/abort options | Manual: verify the skill instructs placement at the correct path; verify the skill creates the target directory when it does not exist; verify the skill detects an existing directory and offers overwrite/rename/abort options before placing files |

#### `workflow-validation`

| Rule | What it covers | Verification approach |
|------|---------------|----------------------|
| Rule 1: Incremental phase validation | Intake output validated (labels, descriptions, minimum steps); dependency mapping validated (all tasks present, no dangling refs, no cycles); description writing validated (non-empty, non-placeholder, self-containment checklist per description); description phase failure (placeholder text caught, specific task reported); advancement blocked when skipped tasks have incomplete descriptions (1.3.2); failure blocks progression | Manual: invoke skill, verify each phase gate blocks on invalid input and passes on valid input; verify self-containment checklist runs on each description during writing; verify placeholder text in a description is caught and reported; skip tasks during description writing and attempt to advance, verify the skill reports incomplete tasks and blocks advancement |
| Rule 2: Comprehensive final validation | Self-containment audit as cross-cutting safety net (with in-place correction), cycle detection, structural integrity (pass when all 5 core fields + metadata with correct types present; fail when field missing or wrong type with specific report; fail when metadata has empty fsm value (2.10); fail when blockedBy references non-existent task ID (2.11)) | Manual: complete workflow, verify final validation reports pass/fail per check with specific issues for failures; verify self-containment failures can be corrected in-place without phase regression; verify structural check catches missing fields and type mismatches; verify metadata content validation catches empty or wrong-key metadata; verify dangling blockedBy reference is caught and reported with the specific task entry and invalid reference |
| Rule 3: Clear validation results | Passing validation confirms readiness; failing validation lists specific issues with actionable guidance | Manual: trigger both passing and failing validations, verify result presentation includes specific issues and guidance |

## Verification Environment

### Prerequisites

- **Claude Code CLI**: Installed and available on PATH. Required for invoking skills and executing the FSM hook pipeline.
- **FSM plugin enabled**: The `finite-skill-machine` plugin must be installed and active in the Claude Code plugin configuration.
- **Fresh session**: Each verification attempt should start a new Claude Code session to avoid state contamination from prior skill invocations. A fresh session ensures the task directory is clean and no prior FSM tasks interfere with verification.

### Setup Steps

1. **Ensure FSM plugin is in the plugins directory**: Verify that the `plugins/finite-skill-machine/` directory exists and contains the plugin configuration (`plugin.json`), hooks (`hooks/hooks.json`), and scripts (`scripts/hydrate-tasks.py`, `scripts/block-skill-internals.sh`).
2. **Verify the skill is deployed**: Confirm that `plugins/finite-skill-machine/skills/creating-taskflow-skills/` contains both `SKILL.md` and `fsm.json`.
3. **Start a new session**: Open a new Claude Code session. This ensures a clean task directory at `~/.claude/tasks/{session_id}/` with no pre-existing tasks.
4. **Invoke the skill**: Use the skill invocation command (e.g., `finite-skill-machine:creating-taskflow-skills`) to trigger the FSM hook pipeline. The hook should hydrate the skill's tasks into the session's task directory.
5. **Verify hydration succeeded**: Confirm that the task directory contains the expected task files (9 tasks for this skill). If the hook fails, check stderr output for validation or resolution errors before proceeding with behavioral verification.

### Session Management

- Each behavioral verification capability (workflow-intake, dependency-mapping, self-contained-descriptions, skill-file-generation, workflow-validation) may be verified in the same session or in separate sessions.
- If verifying in the same session, complete the full workflow end-to-end — the pipeline is forward-only and does not support partial re-execution.
- If verifying capabilities in separate sessions, each session requires a fresh invocation (step 3-4 above).

## Verification Examples

Boundary examples for key scenario categories. Each example defines what qualifies as a pass or fail for that category, enabling consistent manual verification across different verification attempts.

> **Note**: These verification examples are reference material and acceptance criteria for the `behavioral-verification` tasks in tasks.yaml — benchmarks for consistent pass/fail decisions during manual behavioral testing. They are not separate implementation tasks.

### Vague descriptions (workflow-intake:3.2)

A description is "vague" when it does not specify what work is performed.

| Example | Verdict | Reasoning |
|---------|---------|-----------|
| "Handle the configuration" | Fail — vague | Does not specify what "handle" means — create? read? validate? modify? |
| "Set up the environment" | Fail — vague | Does not specify which environment or what "set up" entails |
| "Create a JSON configuration file with database host, port, and credentials fields" | Pass | Specifies the action (create), the artifact (JSON config file), and the content (specific fields) |
| "Validate that all required environment variables are set before the application starts" | Pass | Specifies the action (validate), the target (environment variables), and the timing (before start) |

### Implicit ordering assumptions (self-contained-descriptions:2.3)

An "implicit ordering assumption" is a statement that depends on a prior task's output without explicitly stating the precondition.

| Example | Verdict | Reasoning |
|---------|---------|-----------|
| "At this point the configuration will already exist" | Fail — implicit | Assumes a prior task created the configuration; no explicit precondition |
| "Use the API client that was set up earlier" | Fail — implicit | References setup done by an unspecified prior task |
| "Read the configuration file at `config/settings.json`. If the file does not exist, create it with default values." | Pass | States what to do regardless of prior state — handles both cases |
| "Given a running PostgreSQL instance on localhost:5432, run the migration scripts." | Pass | States the precondition explicitly without assuming who established it |

### Overly broad descriptions (self-contained-descriptions:3.1)

A description is "overly broad" when it covers multiple distinct objectives or deliverables.

| Example | Verdict | Reasoning |
|---------|---------|-----------|
| "Set up the database, create the API endpoints, and write the frontend components" | Fail — too broad | Three distinct deliverables (database, API, frontend) in one task |
| "Validate the input, transform the data, and write the output" | Fail — too broad | Three distinct operations (validate, transform, write) that are independently testable and have separate failure modes — validation failure differs from transformation failure differs from write failure |
| "Create REST endpoints for user CRUD operations, including input validation and error responses" | Pass | Single cohesive objective (user CRUD API) with supporting details |

### External references (self-contained-descriptions:1.3)

An "external reference" is a phrase that points to content outside the description itself.

| Example | Verdict | Reasoning |
|---------|---------|-----------|
| "Follow the formatting rules described in the skill" | Fail — external ref | References "the skill" text which context compaction removes |
| "As mentioned in the previous section" | Fail — external ref | References context outside this description |
| "Format each entry as a JSON object with fields: id (integer), subject (string), description (string)" | Pass | Inlines the format specification directly |

### Self-containment checklist (workflow-validation:2.1)

The self-containment audit uses a concrete checklist instead of a "fresh agent" test. Each description must pass all four items. This approach is systematic, repeatable, and requires no special tooling.

| Checklist item | What to verify | Example pass | Borderline pass | Example fail |
|----------------|---------------|--------------|-----------------|--------------|
| (a) Goal statement | Description states what the task accomplishes | "Generate a JSON configuration file for the deployment pipeline" | "Prepare the deployment configuration so downstream tasks can reference it" — borderline because the goal is framed in terms of enabling other tasks, but it does state what this task produces (a deployment configuration). Passes because the outcome is concrete even if the motivation references downstream usage. | "Process the configuration" (no clear outcome) |
| (b) Specific actions | Description states what the agent should do | "Read the template at `config/template.json`, substitute environment-specific values, write the result to `config/production.json`" | "For each environment (dev, staging, production), generate the corresponding configuration file using the base template" — borderline because the actions are described at a high level without specifying file paths or substitution mechanics. Passes because the iteration pattern (each environment) and the action (generate from base template) are specific enough to act on. | "Handle the configuration appropriately" (no specific actions) |
| (c) Acceptance criteria | Description states how to know when done | "The task is complete when the configuration file passes JSON schema validation" | "Done when all configuration files exist and are non-empty" — borderline because "non-empty" is a weak criterion that does not verify correctness. Passes because the criterion is objectively checkable (file exists + non-empty), even though a stronger criterion would validate content. | No completion criteria stated |
| (d) No undefined references | Every term is defined within the description or includes a pointer to its definition in code or project documentation | "PostgreSQL" (defined externally — widely documented), "the `blockedBy` array defined earlier in this description" (defined in-description), "the INT-fsm-json schema (see `plugins/finite-skill-machine/` documentation)" (pointer to project docs) | "YAML frontmatter" — borderline because YAML frontmatter is a well-known markup convention but less universally documented than "PostgreSQL." Passes because YAML frontmatter has a widely understood definition in the static site generator and documentation tooling ecosystem. | "the normalized step list" (undefined in this description, defined in a sibling task, no pointer provided) |

### "No meaningful workflow material" threshold (workflow-intake:1.3)

"No meaningful workflow material" is defined as **zero extractable steps** after the input-based intake process completes. This creates a binary boundary: zero steps from input-based intakes means brainstorming generates a full step list from scratch; any steps (even vague ones) means brainstorming fills gaps in the existing material.

| Scenario | Input-based intake output | Brainstorming behavior |
|----------|--------------------------|----------------------|
| Author provides an existing skill with no discernible workflow steps | 0 steps | Brainstorming generates full step list from scratch |
| Author provides a single ambiguous sentence ("something about config") | 1 step (vague) | Brainstorming fills gaps — clarification handled by workflow-intake:3.2 path |
| Author provides three well-defined step descriptions | 3 steps | Brainstorming reviews for gaps, adds steps if needed, or marks complete with no output |
| Author provides no input to any intake source | 0 steps | Brainstorming generates full step list from scratch; if author declines, workflow terminates gracefully |

### Multi-source intake scenarios (workflow-intake:1.4)

When multiple intake sources contribute material, CMP-normalize concatenates all contributions and presents the combined list to the author. These test scenarios verify the skill's behavior across four multi-source intake patterns.

**Scenario A: Identical steps from two sources (duplicate detection)**

```
Source 1 (existing skill): "Validate configuration" — check all config files against schema
Source 2 (written steps): "Validate configuration" — check all config files against schema
```

Expected: CMP-normalize presents both steps to the author. The author sees the duplicate and removes one during the confirmation gate. The skill does not auto-deduplicate — per CMP-normalize's responsibilities, the author resolves duplicates since similar labels may serve different purposes.

**Scenario B: Same label, different description (conflict resolution)**

```
Source 1 (existing skill): "Set up environment" — install Python dependencies from requirements.txt
Source 2 (written steps): "Set up environment" — configure Docker containers and networking
```

Expected: CMP-normalize presents both steps to the author. The author sees the conflict — same label, different work — and either renames one step, merges them, or keeps both with clarified labels. The skill does not auto-resolve conflicts.

**Scenario C: Complementary non-overlapping steps (clean merge)**

```
Source 1 (existing skill): "Parse input files", "Validate schemas"
Source 2 (written steps): "Generate output report", "Deploy to staging"
```

Expected: CMP-normalize concatenates all four steps into a single list. No duplicates or conflicts. The author confirms the combined list during the normalization gate, potentially reordering steps to reflect the intended execution sequence.

**Scenario D: One source contributing nothing (skip handling)**

```
Source 1 (existing skill): marked complete with no output (author's input did not include an existing skill)
Source 2 (written steps): "Create database schema", "Seed test data", "Run migrations"
```

Expected: The input-based intake that had no material marks itself complete with no output. Brainstorming receives only the written steps material. CMP-normalize processes the written steps as the sole contributed material. The author sees only the written steps during confirmation.

### Dependency hint preservation through intake to dependency mapping

When written step descriptions contain embedded dependency hints, the intake phase preserves them as-is and the dependency mapping phase uses them as input for encoding relationships.

**Verification example:**

```
Written step input:
  Step 1: "Generate configuration" — create the base configuration files for all environments
  Step 2: "Validate configuration" — after the config is generated, validate all config files against their JSON schemas
```

Expected flow:
1. CMP-intake-written accepts both steps, preserving the dependency hint ("after the config is generated") in Step 2's description as-is
2. CMP-normalize presents both steps for author confirmation — the hint text remains intact in the description
3. CMP-dependency-map, when encoding relationships, recognizes the hint "after the config is generated" as evidence that Step 2 depends on Step 1 and proposes the blocking relationship to the author

The dependency hint is not validated or transformed during intake — it flows through as authored text and informs the dependency mapping conversation.

### Description phase failure (workflow-validation:1.3, 1.6)

A description fails the description writing phase validation when it contains only placeholder text. The skill catches non-substantive content, reports the specific task, and blocks progression until the author writes a real description.

| Example description | Verdict | Reasoning |
|--------------------|---------|-----------|
| "TODO: write this later" | Fail — placeholder | No substantive content; only a deferred note |
| "TBD" | Fail — placeholder | Abbreviation indicating content has not been written |
| "..." or "(placeholder)" | Fail — placeholder | Explicit placeholder markers |
| "Validate that the configuration file contains all required fields and report any missing entries" | Pass | Substantive description with action, target, and outcome |

### Overly small descriptions (self-contained-descriptions:3.2)

A description is "overly small" if it cannot meaningfully populate all 4 self-containment checklist items (goal statement, specific actions, acceptance criteria, no undefined references). When the checklist items become trivially redundant, the task should be considered for merging with a related task.

| Example | Verdict | Reasoning |
|---------|---------|-----------|
| "Delete the temp file" | Fail — too small | Goal and action are identical; no meaningful acceptance criteria beyond "file deleted"; checklist items collapse into one statement |
| "Set the flag to true" | Fail — too small | Single trivial operation; goal, action, and criteria are all the same thing; should merge into the task that uses the flag |
| "Run the linter" | Fail — too small | No standalone outcome; should merge with the task that acts on linter results |
| "Validate all configuration files against their JSON schemas, report validation errors with file path and line number, and fix auto-fixable formatting issues" | Pass | Clear goal (validation), specific actions (validate, report, fix), distinct acceptance criteria (all files validated, errors reported, formatting fixed) |

### activeForm generation (self-contained-descriptions:4.1)

activeForm is derived as present-continuous form from task labels. Boundary cases test edge conditions in the transformation.

| Task label | Expected activeForm | Reasoning |
|-----------|-------------------|-----------|
| "Validate dependencies" | "Validating dependencies" | Standard: verb → present-continuous form |
| "Set up test environment" | "Setting up test environment" | Standard: phrasal verb → present-continuous form |
| "Running tests" | "Running tests" | Already in present-continuous form — keep as-is |
| "Configuration setup" | "Setting up configuration" | Non-verb label — restructure to verb-first present-continuous form |
| "Deploy to production" | "Deploying to production" | Standard: verb → present-continuous form |

Author override per self-contained-descriptions:4.1-4.2 handles remaining edge cases that do not fit these patterns — overrides are accepted as-is without format validation.

### Cycle detection test cases (workflow-validation:2.2, dependency-mapping:3.4)

Cycle detection uses Kahn's algorithm (BFS-based topological sort). These test cases verify correct behavior for acyclic, single-cycle, and multi-cycle graphs.

> **Note**: The expected output for each test case describes *semantic content* to verify (which tasks are correctly identified as cycle participants), not exact phrasing or format. Consistent with the conversational validation mode defined in technical.md, verification checks that the skill reports the correct set of involved tasks — not that it uses a specific output template.

**Test case 1: Acyclic graph (should pass)**

```
Tasks: A, B, C, D
Dependencies: B blockedBy [A], C blockedBy [A], D blockedBy [B, C]
```

Expected: Kahn's algorithm consumes all 4 nodes. No cycle reported. Validation passes.

**Test case 2: Single cycle (should fail)**

```
Tasks: A, B, C
Dependencies: A blockedBy [C], B blockedBy [A], C blockedBy [B]
```

Expected: Kahn's algorithm consumes 0 nodes (all have in-degree >= 1). Report unconsumed nodes: A, B, C. Validation fails with cycle involving tasks A, B, C.

**Test case 3: Multi-cycle with shared node (should fail)**

```
Tasks: A, B, C, D, E
Dependencies: B blockedBy [A], A blockedBy [C], C blockedBy [B], D blockedBy [C], E blockedBy [D], D blockedBy [E]
```

Expected: Kahn's algorithm consumes 0 nodes. Report unconsumed nodes: A, B, C, D, E. Two cycles exist (A-B-C and D-E) with C as a shared node connecting them.

**Test case 4: Partial cycle with acyclic prefix (should fail, report only cycle participants)**

```
Tasks: A, B, C, D
Dependencies: B blockedBy [A], C blockedBy [B], D blockedBy [C], C blockedBy [D]
```

Expected: Kahn's algorithm consumes A (in-degree 0), then B (in-degree drops to 0). C and D remain unconsumed. Report unconsumed nodes: C, D. Tasks A and B are not in the cycle.

## Observability

Not applicable. No new log events, metrics, or alerts are introduced. The skill operates through the existing FSM hook pipeline which has no custom observability layer.

## Migration

Not applicable. All files are new additions. No rollout sequencing, rollback triggers, or data migration needed.
