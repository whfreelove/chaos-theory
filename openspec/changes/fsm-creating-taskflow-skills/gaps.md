# Gaps

<!-- GAP TEMPLATE - Fields by workflow stage:
CRITIQUE adds: ID, Severity, Source, Description
RESOLVE adds: Category, Decision

New gaps from critique should NOT have Category or Decision fields.

See tokamak:managing-spec-gaps for gap creation quality and category semantics.
-->

### GAP-214: Merge mechanics during description writing are unspecified
- **Severity**: medium
- **Source**: implicit-detection
- **Description**: Self-contained-descriptions:3.2 specifies that the skill SHALL recommend merging overly small tasks into a related task, and CMP-descriptions responsibilities include this merge recommendation. However, no specification defines the mechanics for executing a merge during the description writing phase if the author accepts the recommendation. Splitting has fully defined deterministic mechanics (GAP-196): node expansion in the dependency graph, sequential ID assignment for new tasks, inherited dependency relationships, author warning, and post-split re-validation. The merge case has no equivalent specification — no definition of how the merged-away task is removed from the progressive artifact, how its dependency relationships are handled, how the task ID is retired, or whether re-validation runs after a merge. The forward-only pipeline principle (GAP-108, GAP-109) prevents returning to dependency mapping for task removal.

### GAP-215: "normalization confirmation step" leaks internal pipeline stage name in functional.md
- **Severity**: medium
- **Source**: resolution-leakage-detection
- **Description**: Resolution of GAP-201 introduced "normalization confirmation step" in functional.md workflow-intake capability description. "Normalization" is an internal pipeline stage name corresponding to the CMP-normalize component. The previous phrasing ("combining inputs through discussion") was replaced with a term that exposes internal pipeline structure. Functional language should describe the author experience (e.g., "reviewing and resolving overlaps during the step list confirmation step").

### GAP-216: "inherited dependency relationships and post-split re-validation" leaks mechanism names in functional.md
- **Severity**: medium
- **Source**: resolution-leakage-detection
- **Description**: Resolution of GAP-196 introduced "inherited dependency relationships and post-split re-validation" in functional.md self-contained-descriptions capability description. "Inherited dependency relationships" describes the internal node-expansion mechanism (parent/child propagation). "Post-split re-validation" names an implementation protocol. GAP-197 cleaned mechanism names from other capabilities in the same section but GAP-196's additions were not similarly abstracted.

### GAP-217: "intake pipeline" leaks architecture terms in functional.md Known Risks
- **Severity**: medium
- **Source**: resolution-leakage-detection
- **Description**: The functional.md Known Risks section contains "intake pipeline (two input-based sources plus brainstorming gap-filling)" which uses architecture terminology and parenthetical internal component structure. GAP-199 cleaned other Known Risks entries but did not address this one.

### GAP-218: "Requirements-level coverage" is spec-process language in functional.md Known Risks
- **Severity**: medium
- **Source**: resolution-leakage-detection
- **Description**: Resolution of GAP-190 introduced "Requirements-level coverage for the large-workflow warning behavior is deferred to future usage validation" in functional.md Known Risks. This is spec-process language about requirements coverage completeness, not a user-facing risk description. GAP-198 removed "deferred to implementation judgment" framing from Out of Scope entries but the same pattern was introduced in Known Risks by a later resolution.

### GAP-219: Implementation file names "SKILL.md and fsm.json" in functional.md capability boundary
- **Severity**: medium
- **Source**: resolution-leakage-detection
- **Description**: The functional.md What Changes capability boundary note contains "the skill generates SKILL.md and fsm.json files on disk" — specific implementation file names. The functional spec should describe the author experience ("deployable skill files") rather than implementation file names.

### GAP-220: dependency-mapping:5.4 missing from infra.md Rule 5 coverage
- **Severity**: medium
- **Source**: propagation-detection
- **Description**: Resolution of GAP-149 added dependency-mapping:5.4 (cycle introduced by modifying an existing dependency during graph review) but infra.md Rule 5 coverage table was not updated — "What it covers" only lists add/remove/rename operations and the verification approach has no step for modifying a dependency during review and verifying cycle detection rejects the modification.

### GAP-221: skill-file-generation:3.5 missing from infra.md task definition coverage
- **Severity**: medium
- **Source**: propagation-detection
- **Description**: Resolution of GAP-184 added skill-file-generation:3.5 (task IDs renumbered to topological order at finalization with old-to-new mapping presented to author) but infra.md task definition file generation coverage row was not updated — neither "What it covers" nor the verification approach mentions ID renumbering, topological ordering, or author notification of ID changes.

### GAP-222: Internal process exclusions in dependency-mapping:5.2 Then clause
- **Severity**: medium
- **Source**: resolution-normative-detection
- **Description**: Resolution of GAP-165 introduced implementation mechanism language in a Then clause: dependency-mapping:5.2 contains "And the lightweight check SHALL omit splitting guidance, iterative prompting for clarification, and full scope evaluation" — this specifies what internal check logic does NOT perform rather than an observable author-facing outcome. Then clauses must describe verifiable behavior, not internal process exclusions.

### GAP-223: Author-SHALL obligations in self-contained-descriptions:1.5
- **Severity**: medium
- **Source**: resolution-normative-detection
- **Description**: Resolution of GAP-93 introduced author-actor requirements in self-contained-descriptions:1.5. The Then clauses "And the author SHALL be able to skip to a specific task" and "And the author SHALL be able to return to revise a previously completed description" place SHALL obligations on the author rather than the skill. The skill is the actor that SHALL support these capabilities.

### GAP-224: Author-SHALL passive voice in skill-file-generation:3.5
- **Severity**: medium
- **Source**: resolution-normative-detection
- **Description**: Resolution of GAP-140 introduced a passive-voice requirement on the author actor in skill-file-generation:3.5. The Then clause "And the author SHALL be informed of all ID changes before finalization completes" makes the author the SHALL subject rather than the skill. The immediately preceding Then clause already says "the skill SHALL present the old-to-new ID mapping to the author" which makes the passive clause both normatively misplaced and redundant.
