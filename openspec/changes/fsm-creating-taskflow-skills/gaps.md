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

### GAP-225: Additional author-SHALL obligation instances beyond GAP-223
- **Severity**: medium
- **Source**: requirements-critic
- **Description**: The pattern identified in GAP-223 — Then clauses placing SHALL obligations on the author rather than the skill — appears in additional requirement files beyond self-contained-descriptions:1.5. The dependency-mapping confirmation step, the workflow-intake multi-source combination scenario, and the skill-file-generation name normalization confirmation step each contain Then clauses that describe what the author SHALL be able to do rather than what the skill SHALL support or present. These instances extend the normative misplacement class documented in GAP-223 and require the same correction: the skill is the actor that SHALL provide the capability.

### GAP-226: CMP-final-validation Y-statement accepting clause is actively false
- **Severity**: high
- **Source**: design-critic
- **Description**: The Y-statement for the CMP-skill-md branching decision contains an accepting clause asserting that CMP-final-validation does not cover SKILL.md checks. CMP-final-validation explicitly includes a name-consistency check that requires reading SKILL.md content (added via a prior resolved gap). The accepting clause predates that addition and was never updated, making it an actively false statement about the validation architecture.

### GAP-227: Data Transformation table description entry reverses subject and object
- **Severity**: medium
- **Source**: design-critic
- **Description**: In technical.md's Data Transformation table, the Descriptions phase entry for fields added or modified uses a parenthetical that reverses subject and object, misrepresenting the transformation. The description field is rewritten to the self-contained version and activeForm is added as a new field; the parenthetical as written reads as if one field replaces the other rather than accurately characterizing which field is rewritten and which is added. The cumulative output column correctly shows both fields present, making the per-row description inconsistent with the cumulative column.

### GAP-228: Cycle detection build-vs-use choice has no Y-statement in Decisions section
- **Severity**: low
- **Source**: dependency-critic
- **Description**: technical.md prescribes cycle detection via a Python script. The Decisions section contains no Y-statement documenting the build-vs-use choice: implementing the algorithm from scratch versus using an existing graph library. The inline rationale in the component description explains why programmatic execution beats natural language reasoning, but omits evaluation of the existing-library alternative. A decision of this form — choosing to build rather than reuse — warrants a Y-statement so future implementors understand what was considered.

### GAP-229: artifact-recovery scenario Given clause anchored to unobservable LLM-internal state
- **Severity**: medium
- **Source**: requirements-critic
- **Description**: The workflow-validation artifact-recovery scenario includes a Given clause whose trigger condition is anchored to an LLM-internal mechanism. The trigger is not externally observable — no signal from outside the model can induce or verify this state boundary. The scenario specifies valid and observable recovery behavior in its Then clauses, but its precondition cannot be reproduced or confirmed by a verifier, making the scenario untestable as written.

### GAP-230: Author confirmation encoded as Then clause in dependency-mapping fully-parallel-workflow scenario
- **Severity**: low
- **Source**: requirements-critic
- **Description**: The dependency-mapping fully-parallel-workflow scenario ends with an author confirmation step placed as a Then clause extension, making author confirmation an expected system outcome rather than a subsequent actor action. Author confirmation is actor input, not a system observable, and belongs as a When clause in a follow-on scenario. The current placement makes the Then clause non-verifiable from the outside.

### GAP-231: Author-accepts-split path has no Rule or Scenario in requirement files
- **Severity**: medium
- **Source**: validation-critic
- **Description**: The skill-file-generation functional capability description includes task splitting with inherited dependency relationships and post-split handling. The mechanics for what happens when an author accepts a split recommendation were propagated to technical.md and tasks.yaml via prior resolved gaps, but no Rule or Scenario in the requirement files covers the author-accepts path through the split recommendation flow. The parallel merge case in GAP-214 has an analogous open gap for its acceptance mechanics.

### GAP-232: artifact-recovery scenario absent from infra.md Scenario-Specific Setup section
- **Severity**: medium
- **Source**: verification-critic
- **Description**: infra.md's Scenario-Specific Setup section documents preconditions for scenarios that require unusual initial state before behavioral verification. The artifact-recovery scenario has no corresponding entry. The coverage table references artifact loss simulation without specifying how to reliably produce the precondition, leaving verifiers without a consistent reproducible setup procedure for this scenario.

### GAP-233: Conflicting file placement models in skill-file-generation requirement scenarios
- **Severity**: medium
- **Source**: verification-critic
- **Description**: The skill-file-generation requirement file contains two scenarios describing mutually exclusive file placement models. One scenario places the obligation on the author to physically place files after receiving instructions from the skill; another scenario places the same obligation on the skill to autonomously create and populate the directory. The technical design established the autonomous placement model using the Write tool via a prior resolved gap. These two models cannot both be satisfied by the same implementation, making one scenario definitionally incorrect relative to the adopted design.

### GAP-234: Recovery path author verification step absent from technical.md State Management
- **Severity**: medium
- **Source**: logic-critic
- **Description**: A prior resolved gap added a requirement that after artifact reconstruction in the recovery path, the skill must present the reconstructed artifact to the author for verification. The gap outcome records propagation to requirements and infra.md but not to technical.md. The Recovery section in State Management describes reconstruction from conversation history but does not specify the author verification presentation step, leaving implementors without design authority for that behavior.

### GAP-235: CMP-final-validation output specification omits resolution guidance
- **Severity**: low
- **Source**: logic-critic
- **Description**: The workflow-validation requirements include a requirement that each reported issue in the final validation output includes guidance on how the author can resolve it. CMP-final-validation's output specification in technical.md lists structured pass/fail results with specific issues but does not mention resolution guidance as a required output element. CMP-final-validation is the only validation point with a defined structured output format, making the omission from its component specification a design gap even where the guidance may be implicit in conversational validation exchanges.

### GAP-236: First fsm-json implementation task has ambiguous or unverifiable done state
- **Severity**: medium
- **Source**: code-tasks-critic
- **Description**: The first task in the fsm-json implementation group instructs creating a complete JSON artifact with all entries present and all descriptions meeting self-containment requirements. Subsequent tasks in the same group each write individual entries. If the first task produces a complete artifact as described, the subsequent tasks are redundant. If the first task is intended as a skeleton, its done state includes a self-containment constraint that is only verifiable after the subsequent tasks complete. Either reading produces an ambiguous or unverifiable done state that cannot guide an implementor to a consistent stopping point.

### GAP-237: Behavioral-verification task for skill-file-generation Rule 1 omits failure path
- **Severity**: medium
- **Source**: test-infra-critic
- **Description**: The skill-file-generation behavioral-verification task in tasks.yaml covers the happy path for SKILL.md generation. The infra.md coverage table for skill-file-generation Rule 1 explicitly requires verifying that a self-validation failure triggers author correction and re-validation before finalization. The behavioral-verification task has no procedure step to exercise the failure path, leaving that coverage requirement unverified.

### GAP-238: active-work-protection mechanism description mismatch between functional.md files
- **Severity**: medium
- **Source**: functional-consistency-critic
- **Description**: The change's functional.md Known Risks section describes the active-work-protection mechanism using folder-monitoring language. The project-level functional.md describes the same mechanism as invocation-based. If the project description is accurate, the mechanism mismatch means the Known Risk both overstates one concern (file writes triggering the guard) and omits another (the overwrite path during file generation is unprotected by an invocation-based guard). The discrepancy leaves ambiguity about which description is authoritative.
