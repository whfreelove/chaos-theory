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
- `self-contained-descriptions:2.1`–`2.2` + `workflow-validation:2.3` — Descriptions are checked for self-containment both during writing (cross-task references, continuation language) and during final validation (self-containment audit), catching implicit assumptions from dependency mapping
- `workflow-validation:1.1`–`1.7` — Incremental phase-gate validation at each handoff point catches per-phase issues before they propagate, including failure blocking (1.6) and correction-triggered re-validation (1.7)
- `workflow-validation:2.1`–`2.4` — Comprehensive final validation catches cross-cutting issues (structural integrity, cycles, self-containment) that span multiple artifacts, with specific failure identification and correction guidance

Additionally, format specifications are repeated verbatim in each consuming task description (per technical.md decision on self-contained format specs), preventing format drift between phases by design rather than by integration test.

**Forward-only pipeline prevents backward cascading of corrections, with one designed exception.** The pipeline is strictly forward: intake → normalize → dependencies → descriptions → fsm.json → final validation. Corrections happen within each phase before advancing. The one exception is during description writing: when the author confirms a split or merge suggestion, the partial fsm.json (built during the dependencies phase) is updated and the dependency graph is immediately re-validated before the next description is written. This cross-capability callback is captured by `self-contained-descriptions:3.4`–`3.6`: scenarios 3.4–3.5 specify the fsm.json update, re-validation, and pipeline gate for confirmed splits and merges, while scenario 3.6 specifies the decline path — when the author declines a suggestion, the description is accepted as-is and the phase continues to the next task. Re-validation after a confirmed split or merge cannot produce a cycle (both node expansion and blockedBy union are structure-preserving on acyclic graphs), so the re-validation gate is retained as component-level defense-in-depth in CMP-descriptions rather than as a scenario-level blocking path. Beyond this designed exception, downstream corrections cannot cascade backward: CMP-final-validation's in-place description corrections cannot invalidate the dependency graph (already finalized), cannot change the SKILL.md (independent and self-validated), and structural integrity is a read-only check.

**Step list modifications during dependency mapping precede descriptions.** CMP-dependency-map runs before CMP-descriptions in the pipeline. When the author restructures tasks during dependency mapping (adding, removing, or renaming steps per dependency-mapping:5.1-5.4), descriptions do not yet exist. The only artifact affected is the dependency graph itself, which dependency-mapping's existing scenarios already cover. No cross-capability impact on descriptions is possible because they have not been written yet.

Per schema guidance: *"Skip if all behaviors are testable within single-capability requirements."*
