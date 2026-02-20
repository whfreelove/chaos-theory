## Context

The FSM plugin is a local Claude Code plugin with no deployment infrastructure. This change adds a new skill (`finite-skill-machine:creating-taskflow-skills`) that ships as a SKILL.md + fsm.json companion pair — pure content files with no code changes to `hydrate-tasks.py` or the hook system. The existing test infrastructure (pytest with subprocess-based `run_hook()`, `tmp_path` isolation) is not extended because the deliverables are content, not code.

## Objectives

`OBJ-structural-validity`: The delivered fsm.json passes the existing `validate_fsm_tasks` validation in `hydrate-tasks.py` — valid JSON array, required fields present (including `description`), unique IDs, all `blockedBy` references resolve.

`OBJ-requirements-coverage`: Each requirement rule in the requirements files has at least one corresponding scenario with a documented verification approach.

## Deployment

This change deploys via merge to main. The delivered files are placed at `plugins/finite-skill-machine/skills/creating-taskflow-skills/` — one SKILL.md and one fsm.json. No rollout strategy, feature flags, or deployment sequencing — new additive files only.

## Testing Strategy

### Verification modes

This change has two distinct verification modes:

1. **Structural validation** (automated at runtime): The fsm.json is validated by the existing `validate_fsm_tasks` function when the skill is invoked via `hydrate-tasks.py`. This catches structural defects — missing required fields, duplicate IDs, dangling `blockedBy` references, invalid JSON — without needing new test code. The `description` field SHALL be added to `validate_fsm_tasks` required field checks as part of this change so that empty or missing descriptions are caught at hydration time.

2. **Behavioral verification** (manual, author-driven): The 5 requirement capabilities describe agent behavior during the guided workflow. These are verified by invoking the skill and observing agent behavior, not by automated tests. The "code under test" is the agent following task descriptions, not a Python function.

No new behavioral verification pytest tests are added. Structural validation tests in the validation-enhancement group extend the existing hydration pipeline's field checking — these are code changes to `validate_fsm_tasks`, not behavioral tests. The structural validation path already exists in the hydration pipeline; behavioral verification is inherently manual because the outputs are agent actions guided by prose descriptions.

**Integration verification exclusion**: No integration test scenarios are defined for this change. The five capabilities form a sequential pipeline with validation gates, not bidirectional interactions that produce emergent behavior. Cross-capability coverage is captured by single-capability requirements. See `integration.feature.md` for the full rationale.

**CI/CD exclusion**: Behavioral verification is manual by design — no automated CI/CD integration is defined for behavioral tests because the outputs are agent actions guided by prose descriptions, not deterministic function outputs.

### Verification by design: confirmation gates

Multiple requirements specify that "the skill does not proceed until the author approves" (workflow-intake:2.3, 4.3, dependency-mapping:4.3). These confirmation gates use any mechanism that blocks skill execution until the author responds. The blocking mechanism is **inherently blocking** — the skill literally cannot proceed without a user response. The agent's execution pauses at the prompt and does not resume until the author provides input.

This means the blocking behavior is **guaranteed by construction**, not by testing. There is no code path where the skill could bypass a confirmation gate, because the underlying mechanism (waiting for user input) is a fundamental property of the execution model. Accordingly, no specific test infrastructure is needed to verify that confirmation gates block — the verification is that the mechanism exists in the task description, which is covered by behavioral verification.

### Coverage by capability

#### `workflow-intake`

| Rule | What it covers | Verification approach |
|------|---------------|----------------------|
| Rule 1: Input-based sources and brainstorming gap-filling | Source-specific guidance for existing skill, written steps; brainstorming gap-filling after input-based intakes; convergence to normalized step list | Manual: invoke skill with each intake type, verify guidance is source-specific; verify brainstorming reviews prior intake material and fills gaps; verify convergence produces a normalized step list |
| Rule 2: Existing skill transformation | Sequential step extraction, implicit parallelism identification, conditional logic decomposition (author chooses strategy), author review gate | Manual: provide an existing skill as input, verify extracted steps match the skill's structure; provide a skill with conditional branching, verify the skill presents decomposition options and incorporates the author's choice |
| Rule 3: Written step description intake | Well-structured acceptance, vague description prompting, overly large step splitting | Manual: provide written steps of varying quality, verify the skill prompts for clarification or splitting as appropriate |
| Rule 4: Brainstorming gap-filling | Gap identification from prior intake material; unordered idea organization when no prior material exists; overlapping idea consolidation; author confirmation gate; graceful termination when no steps emerge | Manual: invoke skill with input-based material, verify brainstorming identifies gaps and proposes additions; invoke skill with no input-based material, verify brainstorming guides from scratch; verify graceful termination when no steps emerge. **Empty-sources setup procedure**: start a fresh session, invoke the skill, provide no input to either input-based intake source (both tasks mark themselves complete with no output). Brainstorming receives zero prior material and guides the author through generating a full step list from scratch |

#### `dependency-mapping`

| Rule | What it covers | Verification approach |
|------|---------------|----------------------|
| Rule 1: Serial execution patterns | Linear chain encoding, explicit ordering for ambiguous steps | Manual: define a linear workflow, verify blocking relationships are encoded correctly |
| Rule 2: Parallel execution patterns | Independent task identification, parallel grouping confirmation | Manual: define independent tasks, verify no blocking relationships between them |
| Rule 3: Fan-in and fan-out patterns | Fan-out from single predecessor, fan-in to single successor, diamond pattern | Manual: define fan-out/fan-in workflows, verify dependency graph captures convergence and divergence |
| Rule 4: Author confirmation of graph | Dependency summary presentation, modification after review, approval gate | Manual: verify the skill presents a complete dependency summary and allows modifications |
| Rule 5: Step list modifications during dependency mapping | Author removes a task (graph updated, dangling refs removed); author adds a task (lightweight quality check applied, graph updated, new relationships prompted); author renames a task (label updated, relationships preserved); re-validation after each modification; lightweight quality check pass/fail boundary for added tasks (label present/non-empty, description specificity, actionability) | Manual: during dependency mapping, remove a task and verify graph updates correctly; add a task and verify the lightweight quality check runs before the task enters the graph — verify pass when label and description meet specificity and actionability criteria, verify fail when label is empty, description is vague, or task is not actionable; verify the skill prompts for blocking relationships with all existing tasks (predecessors and successors); rename a task and verify existing dependencies preserved. **Single-task boundary example**: when adding a task to a workflow with one existing task, the skill prompts for the new task's relationship to the single existing task — blocked by it, blocks it, or independent. Pass: the skill references the one existing task by name. Fail: the skill prompts generically without referencing the existing task |
| Rule 6: Single-task workflows | Empty dependency graph, immediate progression for single-task workflow | Manual: define a workflow with exactly one task, verify the task's blockedBy array is empty, verify the skill confirms the trivially empty graph and proceeds |

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
| Rule 2 (self-validation): SKILL.md self-validation | Self-validation failure triggers author correction and re-validation before SKILL.md is finalized | Manual: trigger a self-validation failure (e.g., remove a frontmatter field), verify the skill reports the issue, correct it, verify re-validation runs and passes |
| Rule 3: Correct directory structure | Files placed under `plugins/<plugin>/skills/<skill>/`; SKILL.md and fsm.json colocated; target directory created if it does not exist; existing directory detected with overwrite/rename/abort options | Manual: verify the skill instructs placement at the correct path; verify the skill creates the target directory when it does not exist; verify the skill detects an existing directory and offers overwrite/rename/abort options before placing files |

#### `workflow-validation`

| Rule | What it covers | Verification approach |
|------|---------------|----------------------|
| Rule 1: Incremental phase validation | Intake output validated (labels, descriptions, minimum steps); dependency mapping validated (all tasks present, no dangling refs, no cycles); description writing validated (non-empty, non-placeholder, self-containment checklist per description); description phase failure (placeholder text caught, specific task reported); advancement blocked when skipped tasks have incomplete descriptions (1.3.2); phase-completion summary gate (summary of entries updated per construction phase, author confirms completeness before next phase begins) (1.7); advancement blocked and incomplete entries reported when phase-completion summary reveals skipped items (1.7.1); artifact recovery when in-context artifact is lost — skill reconstructs from most recent complete phase output and presents to author for verification (1.8); failure blocks progression | Manual: invoke skill, verify each phase gate blocks on invalid input and passes on valid input; verify self-containment checklist runs on each description during writing; verify placeholder text in a description is caught and reported; skip tasks during description writing and attempt to advance, verify the skill reports incomplete tasks and blocks advancement; verify the skill presents a phase-completion summary after each construction phase (dependency mapping, description writing) showing which entries were updated; verify the skill does not advance to the next phase until the author confirms the summary; verify the skill blocks advancement and reports specific incomplete entries when the summary reveals skipped items (1.7.1); simulate in-context artifact loss, verify the skill reconstructs from the most recent complete phase output and presents the reconstructed artifact for author verification (1.8) |
| Rule 2: Comprehensive final validation | Self-containment audit as cross-cutting safety net (with in-place correction), cycle detection, structural integrity (pass when all 5 core fields + metadata with correct types present; fail when field missing or wrong type with specific report; fail when metadata has empty fsm value (2.10); fail when blockedBy references non-existent task ID (2.11)), name consistency (metadata.fsm matches SKILL.md frontmatter name; fail when mismatch detected (2.12)) | Manual: complete workflow, verify final validation reports pass/fail per check with specific issues for failures; verify self-containment failures can be corrected in-place without phase regression; verify structural check catches missing fields and type mismatches; verify metadata content validation catches empty or wrong-key metadata; verify dangling blockedBy reference is caught and reported with the specific task entry and invalid reference; verify name-consistency check catches mismatch between metadata.fsm and SKILL.md name |
| Rule 3: Clear validation results | Passing validation confirms readiness; failing validation lists specific issues with actionable guidance | Manual: trigger both passing and failing validations, verify result presentation includes specific issues and guidance |

### Verification environment

#### Prerequisites

- **Claude Code CLI**: Installed and available on PATH. Required for invoking skills and executing the FSM hook pipeline.
- **FSM plugin enabled**: The `finite-skill-machine` plugin must be installed and active in the Claude Code plugin configuration.
- **Fresh session**: Each verification attempt should start a new Claude Code session to avoid state contamination from prior skill invocations. A fresh session ensures the task directory is clean and no prior FSM tasks interfere with verification.

#### Base setup steps

These steps apply to all verification scenarios.

1. **Ensure FSM plugin is in the plugins directory**: Verify that the `plugins/finite-skill-machine/` directory exists and contains the plugin configuration (`plugin.json`), hooks (`hooks/hooks.json`), and scripts (`scripts/hydrate-tasks.py`, `scripts/block-skill-internals.sh`).
2. **Verify the skill is deployed**: Confirm that `plugins/finite-skill-machine/skills/creating-taskflow-skills/` contains both `SKILL.md` and `fsm.json`.
3. **Start a new session**: Open a new Claude Code session. This ensures a clean task directory at `~/.claude/tasks/{session_id}/` with no pre-existing tasks.
4. **Invoke the skill**: Use the skill invocation command (e.g., `finite-skill-machine:creating-taskflow-skills`) to trigger the FSM hook pipeline. The hook should hydrate the skill's tasks into the session's task directory.
5. **Verify hydration succeeded**: Confirm that the task directory contains the expected task files (9 tasks for this skill). If the hook fails, check stderr output for validation or resolution errors before proceeding with behavioral verification.

#### Scenario-specific setup

Some verification scenarios require directory-state preconditions that must be established after base setup but before exercising the scenario:

- **Directory-creation scenario** (skill-file-generation:4.3): Remove the target skill directory (`plugins/<plugin>/skills/<skill>/`) if it exists, so the skill must create it during file placement.
- **Collision-detection scenario** (skill-file-generation:4.4): Pre-populate the target skill directory (`plugins/<plugin>/skills/<skill>/`) with existing files, so the skill detects the collision and offers resolution options.

#### Session management

- Each behavioral verification capability (workflow-intake, dependency-mapping, self-contained-descriptions, skill-file-generation, workflow-validation) may be verified in the same session or in separate sessions.
- If verifying in the same session, complete the full workflow end-to-end — the pipeline is forward-only and does not support partial re-execution.
- If verifying capabilities in separate sessions, each session requires a fresh invocation (step 3-4 above).

## Observability

Not applicable. No new log events, metrics, or alerts are introduced. The skill operates through the existing FSM hook pipeline which has no custom observability layer.

## Migration

Not applicable. All files are new additions. No rollout sequencing, rollback triggers, or data migration needed.
