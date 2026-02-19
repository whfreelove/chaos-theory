# Feature: Creating Taskflow Skills Integration (integration)

<!--
OPTIONAL FILE - only create when capabilities interact in ways not captured
by single-capability requirements.

MDG format. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

PURPOSE: Cross-capability integration test scenarios.
- Tests interactions BETWEEN capabilities
- Does NOT duplicate single-capability requirements
- References involved capabilities with @capability-slug tags
-->

## No Integration Scenarios Required

The five capabilities (`workflow-intake`, `dependency-mapping`, `self-contained-descriptions`, `skill-file-generation`, `workflow-validation`) form a **sequential pipeline with validation gates** — not a bidirectional interaction that produces emergent behavior. This change delivers pure content files (a SKILL.md + fsm.json pair); no code-level runtime interactions exist where multiple capabilities' logic executes in the same function.

Cross-capability coverage is already captured by single-capability requirements:

- `workflow-intake:1.2` + `workflow-validation:1.1` — Intake output is validated before dependency mapping begins, ensuring intake-to-normalization quality
- `self-contained-descriptions:2.3` + `workflow-validation:2.1` — Descriptions are checked for self-containment both during writing and during final validation, catching implicit assumptions from dependency mapping
- `workflow-validation:1.1`–`1.6` — Incremental phase-gate validation at each handoff point catches per-phase issues before they propagate
- `workflow-validation:2.1`–`2.12` — Comprehensive final validation catches cross-cutting issues (cycles, self-containment, structural integrity, name consistency) that span multiple artifacts. CMP-final-validation fans in from CMP-fsm-json-finalize (blocking task dependency) and reads SKILL.md content produced by CMP-skill-md from disk for the name-consistency check (data-read dependency)

Additionally, format specifications are repeated verbatim in each consuming task description (per technical.md decision on self-contained format specs), preventing format drift between phases by design rather than by integration test.

**Forward-only pipeline prevents backward cascading of corrections.** The pipeline is strictly forward: intake → normalize → dependencies → descriptions → fsm.json → final validation. Corrections happen within each phase before advancing. CMP-final-validation's in-place description corrections cannot invalidate the dependency graph (already finalized), cannot change the SKILL.md (independent and self-validated), and structural integrity is a read-only check. No correction in a downstream phase can cascade backward to invalidate an upstream phase's output.

**Step list modifications during dependency mapping precede descriptions.** CMP-dependency-map runs before CMP-descriptions in the pipeline. When the author restructures tasks during dependency mapping (adding, removing, or renaming steps per dependency-mapping:5.1-5.3), descriptions do not yet exist. The only artifact affected is the dependency graph itself, which dependency-mapping's existing scenarios already cover. No cross-capability impact on descriptions is possible because they have not been written yet.

Per schema guidance: *"Skip if all behaviors are testable within single-capability requirements."*
