# Tokamak

OpenSpec change management plugin for Claude Code. Manages the lifecycle of spec-driven changes from proposal through implementation to archive.

## Workflows

### Change Workflow

For new features, fixes, or modifications where specs are designed before implementation.

```
new-change → [artifact creation] → sculpt-specs → [critique/resolve CLI]
           → ratify-specs → implement-change → merge-change → archive-change
```

Each change tracks two independent statuses:

- **specs-status**: `new` → `draft` → `reviewing` → `ratified` → `merging` → `merged`
- **code-status**: `waiting` → `ready` → `in-progress` → `done`

| Stage | What happens |
|---|---|
| **new-change** | Creates change directory, selects triage policy and schema, initializes gap tracking |
| **Artifact creation** | Functional spec, technical design, BDD specs, and tasks are authored (via `opsx:continue`). Moves to `draft`. |
| **sculpt-specs** | Freeform design refinement — reads all artifacts holistically, identifies cross-cutting tensions, revises directly. Iterative; promote to `reviewing` when coherent. |
| **critique** (CLI) | `run_critique_specs.py <change-dir>` — parallel critics validate artifacts and document gaps |
| **resolve** (CLI) | `run_resolve_gaps.py <change-dir>` — gaps categorized, solutions designed, documentation updated |
| **ratify-specs** | Reviewed specs are locked, unlocking implementation |
| **implement-change** | Tasks from the ratified change are implemented with lifecycle tracking |
| **merge-change** | Change artifacts are merged into project documentation |
| **archive-change** | Completed change is moved to archive after both tracks reach terminal state |

### Brownfield Documentation Workflow

For existing codebases where documentation is reverse-engineered from code.

**Key principle**: code is ground truth. Documentation must match what exists, not what was intended.

| Stage | What happens |
|---|---|
| **new-change** | Creates change with `--schema chaos-theory-brownfield` |
| **Artifact creation** | Documentation reverse-engineered from existing code |
| **critique** (CLI) | `run_critique_specs.py <change-dir>` — auto-detects brownfield schema, loads brownfield-specific critics |
| **resolve** (CLI) | `run_resolve_gaps.py <change-dir>` — resolutions favor updating documentation to match code reality |

## Skills Reference

### Change Lifecycle

| Skill | Description |
|---|---|
| `new-change` | Create a new change with triage policy and gap tracking |
| `implement-change` | Implement tasks from a ratified change |
| `merge-change` | Merge change artifacts into project documentation |
| `archive-change` | Archive a completed change |
| `change-dashboard` | View lifecycle status of all changes at a glance |
| `ratify-specs` | Lock reviewed specs to unlock implementation |

### Spec Validation

| Skill | Description |
|---|---|
| `sculpt-specs` | Freeform holistic design refinement for specs in `draft` state |
| `validate-specs` | Validate artifacts before proceeding |
| `managing-spec-gaps` | Principles for gap lifecycle management |

Critique and resolve are user-invoked CLI tools (see Scripts below), not agent skills. Both are schema-agnostic — they auto-detect brownfield/greenfield from `.openspec.yaml`.

### Writing Guides

| Skill | Description |
|---|---|
| `writing-functional-specs` | Guidance for writing functional specifications |
| `writing-technical-design` | Creating technical design documents and architecture documentation |
| `writing-markdown-gherkin` | Writing BDD specs in Given-When-Then format |
| `writing-infra-specs` | Conceptual guidance for writing infrastructure specifications |
| `writing-system-documentation` | Task-oriented technical documentation with progressive disclosure |
| `writing-yaml-adr` | Writing architectural decision records |
| `writing-y-statements` | Low-overhead decision documentation during feature development |
| `compressing-yadr` | Compressing YAML ADRs into Y-Statement format |
| `reviewing-yaml-adr` | Reviewing proposed ADRs for accept/reject/defer decisions |

### Utility

| Skill | Description |
|---|---|
| `onboard` | Bootstrap a project for brownfield documentation — initializes OpenSpec, explores codebase, creates first change |
| `init-schemas` | Initialize OpenSpec schemas in the current project |
| `verification-before-completion` | Run verification commands before claiming work is complete |

## Scripts

### Workflow CLIs

| Script | Purpose |
|---|---|
| `run_critique_specs.py` | Standalone CLI for the critique-specs workflow |
| `run_resolve_gaps.py` | Standalone CLI for the resolve-gaps workflow |

### Orchestration

| Script | Purpose |
|---|---|
| `run_critics.py` | Execute critic suite against change artifacts |
| `run_resolvers.py` | Parallel resolver orchestrator (per-file gap resolution) |
| `run_solvers.py` | Parallel solver orchestrator (explore → solve phases) |
| `select_critics.py` | Select applicable critics for a given schema and stage |

### Utilities

| Script | Purpose |
|---|---|
| `change_dashboard.sh` | Display lifecycle status table for all changes |
| `change_status.sh` | Read, write, and check fields in `.openspec.yaml` |
| `group_gaps.py` | Group gaps by primary file for parallel resolution |
| `init_schemas.sh` | Copy bundled schemas into project |
| `list_skills.py` | List spec-writing skills needed for a change's artifact types |
| `next_gap.sh` | Find the next unresolved gap for processing |
| `record_findings.py` | Persist validation output to `findings.json` |
| `resolve_artifacts.py` | Schema-agnostic artifact resolver for resolve-gaps and ratify-specs |
| `resolve_triage_policy.py` | Initialize or query triage policy for a change |
| `spec_utils.py` | Shared utilities library |
| `split_spec.py` | Section extractor for `chaos-theory-lite` single-file specs |

## Schemas

| Schema | Purpose |
|---|---|
| `chaos-theory` | Default schema for greenfield and general changes |
| `chaos-theory-brownfield` | Brownfield documentation workflow for existing codebases |
| `chaos-theory-greenfield` | Explicit greenfield workflow for new projects |
| `chaos-theory-lite` | Lightweight single-file spec workflow |
