# Tokamak

OpenSpec change management plugin for Claude Code. Manages the lifecycle of spec-driven changes from proposal through implementation to archive.

## Workflows

### Change Workflow (Greenfield)

For new features, fixes, or modifications where specs are designed before implementation.

```
new-change → [artifact creation] → critique-specs → resolve-gaps → ratify-specs
           → implement-change → merge-change → archive-change
```

Each change tracks two independent statuses:

- **specs-status**: `new` → `draft` → `reviewed` → `ratified` → `merged`
- **code-status**: `waiting` → `ready` → `in-progress` → `done`

| Stage | What happens |
|---|---|
| **new-change** | Creates change directory, selects triage policy and schema, initializes gap tracking |
| **Artifact creation** | Functional spec, technical design, BDD specs, and tasks are authored (via `opsx:continue`) |
| **critique-specs** | Parallel critics validate artifacts against each other and document gaps |
| **resolve-gaps** | Gaps are categorized, solutions designed, and documentation updated |
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
| **critique-specs-brownfield** | Critics validate internal consistency *and* accuracy against the actual codebase |
| **resolve-gaps-brownfield** | Resolutions favor updating documentation to match code reality |
| **validate-brownfield** | Combined critique + resolution validation pass |

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

### Spec Validation (Greenfield)

| Skill | Description |
|---|---|
| `critique-specs` | Run parallel critics against change artifacts and document gaps |
| `resolve-gaps` | Resolve gaps from critique findings |
| `validate-specs` | Validate artifacts before proceeding |
| `managing-spec-gaps` | Principles for gap lifecycle management |

### Spec Validation (Brownfield)

| Skill | Description |
|---|---|
| `critique-specs-brownfield` | Run critics against brownfield documentation, validating against actual codebase |
| `resolve-gaps-brownfield` | Resolve gaps favoring documentation updates to match code |
| `validate-brownfield` | Combined critique and resolution validation |

### Writing Guides

| Skill | Description |
|---|---|
| `writing-functional-specs` | Guidance for writing functional specifications |
| `writing-technical-design` | Creating technical design documents and architecture documentation |
| `writing-markdown-gherkin` | Writing BDD specs in Given-When-Then format |
| `writing-system-documentation` | Task-oriented technical documentation with progressive disclosure |
| `writing-yaml-adr` | Writing architectural decision records |
| `writing-y-statements` | Low-overhead decision documentation during feature development |
| `compressing-yadr` | Compressing YAML ADRs into Y-Statement format |
| `reviewing-yaml-adr` | Reviewing proposed ADRs for accept/reject/defer decisions |

### Utility

| Skill | Description |
|---|---|
| `init-schemas` | Initialize OpenSpec schemas in the current project |
| `verification-before-completion` | Run verification commands before claiming work is complete |

## Scripts

| Script | Purpose |
|---|---|
| `change_dashboard.sh` | Display lifecycle status table for all changes |
| `change_status.sh` | Read, write, and check fields in `.openspec.yaml` |
| `init_schemas.sh` | Copy bundled schemas into project |
| `next_gap.sh` | Find the next unresolved gap for processing |
| `resolve_triage_policy.py` | Initialize or query triage policy for a change |
| `run_critics.py` | Execute critic suite against change artifacts |
| `select_critics.py` | Select applicable critics for a given schema and stage |

## Schemas

| Schema | Purpose |
|---|---|
| `chaos-theory` | Default schema for greenfield and general changes |
| `chaos-theory-brownfield` | Brownfield documentation workflow for existing codebases |
| `chaos-theory-greenfield` | Explicit greenfield workflow for new projects |
