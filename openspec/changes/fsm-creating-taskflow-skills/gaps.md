# Gaps

<!-- GAP TEMPLATE:
### GAP-XX: Title
- **Source**: <kebab-case with type suffix, e.g., functional-critic, implicit-detection>
- **Severity**: high|medium|low
- **Description**: ...
- **Triage**: check-in|delegate|defer-release|defer-resolution (added by resolve workflow)
- **Decision**: ... (added by resolve workflow)

CRITIQUE adds: ID, Source, Severity, Description
RESOLVE adds: Triage, Decision

New gaps from critique should NOT have Triage or Decision fields.

See tokamak:managing-spec-gaps for triage and status semantics.
-->

### GAP-1: "Compaction" is internal mechanism language in functional.md
- **Source**: functional-critic
- **Severity**: medium
- **Description**: Two passages in functional.md use the term "compaction" to explain why tasks must be self-contained. Compaction is a Claude Code internal mechanism, not a concept a skill author would reason about. The author's concern is that tasks remain executable without relying on earlier conversation context — the spec should be reframed in those terms.

### GAP-2: What Changes section uses internal workflow terminology
- **Source**: functional-critic
- **Severity**: low
- **Description**: The What Changes section in functional.md describes the user experience using internal workflow terms ("intake paths," "gap-filling step") rather than describing what skill authors receive. The Scope section already covers this concern more clearly; the What Changes entry is redundant and uses leakier language.

### GAP-3: OBJ-incremental-validation describes final validation as a pre-generation gate
- **Source**: design-critic
- **Severity**: high
- **Description**: OBJ-incremental-validation states that the final validation pass runs "before file generation," but the task dependency graph and component descriptions place CMP-final-validation after both CMP-skill-md and CMP-fsm-json-finalize have already written artifacts to disk. Final validation is a post-generation correctness check; an implementer reading the objective would design the wrong write order.

### GAP-4: blockedBy data flow from dependency mapping through to fsm.json finalization is unspecified
- **Source**: design-critic
- **Severity**: medium
- **Description**: CMP-fsm-json-finalize describes finalizing a "progressively-built fsm.json" assembled incrementally across prior phases, but neither CMP-dependency-map nor CMP-descriptions specifies building or appending to an intermediate fsm.json artifact. CMP-fsm-json-finalize's formal dependencies list only the enriched task list from CMP-descriptions, and that output format does not include a blockedBy field. The mechanism by which finalization acquires blockedBy values — and how those values flow through the pipeline — is undocumented across all three components.

### GAP-5: System overview diagram omits SKILL.md to Final Validation data dependency
- **Source**: design-critic
- **Severity**: low
- **Description**: The system overview diagram in technical.md shows the SKILL.md branch terminating without a connection to Final Validation, while the authoritative task dependency graph and surrounding prose both document that Final Validation reads the SKILL.md output for name consistency. Readers must manually reconcile the two diagrams.

### GAP-6: Python script for cycle detection lacks contract, location, and feasibility documentation
- **Source**: technical-critic
- **Severity**: high
- **Description**: CMP-dependency-map and CMP-final-validation both delegate cycle detection to "topological sort via programmatic tool invocation (Python script)" with no documentation of whether this script exists, where it is located, what its invocation interface is, how it should be tested, or why Python was selected over alternatives. Cycle detection is a core correctness guarantee; without the script's contract and justification, neither component can be implemented as specified.

### GAP-7: Deterministic node expansion during description writing lacks an implementable specification
- **Source**: technical-critic
- **Severity**: medium
- **Description**: The task-splitting behavior during description writing (deterministic node expansion) does not document what artifact the agent mutates, how newly allocated IDs are determined at that phase, or what "re-validate the dependency graph after splitting" invokes. The split mechanism is specified at the requirement level but lacks the implementation-level specification needed for mid-pipeline execution.

### GAP-8: CMP-dependency-map add-task behavior missing the prompt-for-dependencies step
- **Source**: implementation-critic
- **Severity**: medium
- **Description**: CMP-dependency-map describes uniform handling of add, remove, and rename task operations, but the add operation has a required behavioral distinction: the skill must prompt the author for the new task's dependencies before re-presenting the dependency graph. The current uniform phrasing implies the task is appended with empty dependencies, which differs meaningfully from the required prompt-first behavior.

### GAP-9: CMP-skill-md validation failure path is undocumented
- **Source**: implementation-critic
- **Severity**: medium
- **Description**: CMP-skill-md specifies self-validation of YAML frontmatter but does not document the failure path. Every other validating component in technical.md explicitly states that validation failures must be presented to the author for correction before the component completes. The absence of this failure path from CMP-skill-md leaves the correction behavior unspecified.

### GAP-10: Weak normative language in a dependency-mapping Then step
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: A Then step in the dependency-mapping requirements uses "can run simultaneously" to describe concurrent task execution. Then steps describing mandatory system behavior must use definitive language. The clause should be rewritten with definitive language or removed if it states an implication rather than an observable outcome.

### GAP-11: Author confirmation action placed inside a Then step
- **Source**: requirements-critic
- **Severity**: high
- **Description**: Two scenarios in the dependency-mapping requirements place an actor action ("the author confirms") inside a Then step. Then steps must describe the system's observable response only; actor actions belong in When steps. The affected scenarios require structural correction to separate the confirming action from the system response.

### GAP-12: Cycle detection scenario bundles three independently falsifiable outcomes in one Then step
- **Source**: requirements-critic
- **Severity**: high
- **Description**: The cycle detection scenario in the dependency-mapping requirements bundles three independently verifiable outcomes in a single Then step: rejection of the graph, identification of the tasks involved, and the resolution prompt. Each outcome can fail independently in an implementation. These must be separated into distinct scenarios or elevated to distinct Rules.

### GAP-13: Presentation-order scenario misclassified under self-containment rule
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: A scenario in the self-contained-descriptions requirements verifies that tasks are presented to the author in dependency order. This scenario is placed under the "Task descriptions must be self-contained" rule, which it cannot test. Presentation ordering is a separate concern; the misclassification means the self-containment rule's test suite can pass even when self-containment is broken.

### GAP-14: Then step describes internal non-execution rather than an observable outcome
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: A Then step in the self-contained-descriptions requirements describes an internal process that is not performed ("without format validation") rather than an externally observable outcome. There is no artifact or interaction to assert against. The Then step should state the observable result of the author's override being accepted.

### GAP-15: Multi-condition Then steps across workflow-validation scenarios
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: Several workflow-validation scenarios bundle multiple independently falsifiable conditions into single Then steps. Each condition can pass or fail independently of the others, making it impossible to identify which check failed. Each condition must become its own scenario or the rule must explicitly define the conditions as a named composite gate.

### GAP-16: Scenario titles in requirements join two behaviors with an em-dash
- **Source**: requirements-critic
- **Severity**: low
- **Description**: Two scenario titles in the requirements use an em-dash to concatenate what are effectively two behaviors. Scenario titles must name only the single behavior being verified; titles that suggest multiple behaviors are prohibited by the writing-markdown-gherkin guidance.

### GAP-17: Structural sub-components required by final validation are never defined upstream
- **Source**: requirements-coverage-critic
- **Severity**: high
- **Description**: The structural completeness check in workflow-validation requires that each task description contain specific structural sub-components (goal statement, specific actions, acceptance criteria), but the description-writing capability never defines or requires these sub-components. The task schema in skill-file-generation lists the actual required fields — none of which decompose into those sub-components. The workflow-validation scenario is inconsistent with the schema definition and conflates self-containment content with structural integrity, meaning a developer implementing the description phase would produce output that the final validator would incorrectly reject.

### GAP-18: Task removal leaves orphaned dependents without a reconnection specification
- **Source**: requirements-coverage-critic
- **Severity**: medium
- **Description**: The task removal scenario in the dependency-mapping requirements specifies that all blockedBy references to the removed task are cleared from remaining tasks, but does not address what happens to the ordering relationship between the removed task's predecessors and its dependents. Removing a middle node from a sequential chain silently converts sequential execution to parallel. The requirements are missing a scenario covering either automatic reconnection or an author prompt to resolve the disconnection.

### GAP-19: Confirmed-acceptance path for split and merge suggestions is undefined
- **Source**: requirements-coverage-critic
- **Severity**: medium
- **Description**: The split and merge suggestion scenarios in the self-contained-descriptions requirements end at the suggestion or author prompt without specifying the confirmed-acceptance outcome. Whether the task list is modified, whether the dependency graph is updated, and whether the pipeline continues or loops back after the author confirms is not defined in any requirement.

### GAP-20: integration.feature.md justification cites requirement scenario tags that do not exist
- **Source**: validation-critic
- **Severity**: medium
- **Description**: The integration.feature.md file justifies omitting integration scenarios by citing specific requirement scenario tags, but those tags do not exist in the change's requirements files. The cited scenario ranges extend beyond what was actually specified, making the argument that cross-capability coverage is already captured by single-capability requirements unverifiable against the actual requirement set.

### GAP-21: Multi-source intake interaction sequence is unspecified and untested
- **Source**: validation-critic
- **Severity**: medium
- **Description**: When both intake sources are provided simultaneously, the requirements cover only the normalization outcome, not the user interaction sequence. Which source is processed first and how the results are combined is unspecified. The scope of each intake capability's scenarios is bounded to single-source use, leaving the combined intake path without coverage.

### GAP-22: infra.md coverage table references requirement scenario IDs that do not exist
- **Source**: design-for-test-critic
- **Severity**: high
- **Description**: The infra.md coverage table references requirement scenario IDs that do not exist in the requirements files. The scenario-specific setup section also references scenario IDs in skill-file-generation that are beyond the last defined scenario. The infra documents verification approaches for behaviors that have no traceable requirement, breaking the traceability chain from infra to requirements.

### GAP-23: Cycle detection scenario absent from infra.md coverage table
- **Source**: design-for-test-critic
- **Severity**: medium
- **Description**: The dependency-mapping coverage row in infra.md covers fan-out, fan-in, and diamond pattern scenarios but omits the cycle detection scenario. Cycle detection requires a distinct setup and is a correctness-critical behavior. No verification approach is documented for it.

### GAP-24: No verification command for validate_fsm_tasks structural code change
- **Source**: design-for-test-critic
- **Severity**: low
- **Description**: The infra classifies the validate_fsm_tasks code change as automated structural verification but provides no runnable verification command. The testing strategy completeness checklist requires verification commands for all automated verification paths.

### GAP-25: Correction paths for non-self-containment failures at final validation are undefined
- **Source**: logic-critic
- **Severity**: medium
- **Description**: CMP-final-validation documents a correction mechanism only for self-containment failures. The correction paths for cycle detection failures and structural integrity failures are undefined. The requirements specify that actionable correction guidance must be provided for all failure types, but the design does not document what guidance applies or whether a failure type requires re-entering an earlier phase.

### GAP-26: Task merge mechanism is unspecified in the component design
- **Source**: logic-critic
- **Severity**: medium
- **Description**: CMP-descriptions specifies the split mechanism in detail (deterministic node expansion with dependency inheritance and re-validation) but provides no equivalent specification for merges. The design leaves undefined which task ID survives a merge, how blockedBy relationships from both tasks are reconciled, whether the dependency graph is re-validated, and what "adjacent" means in the context of a dependency graph.

### GAP-27: Description-phase task restructuring invalidates the finalized dependency graph
- **Source**: integration-coverage-critic
- **Severity**: high
- **Description**: The description phase can trigger task splits and merges after dependency mapping has been finalized. The integration.feature.md argument that the pipeline is forward-only covers only modifications made during the dependency-mapping phase, not structural changes triggered by the description phase. When a split or merge occurs during description writing, the finalized dependency graph becomes stale. No scenario covers the dependency graph update and re-validation that must occur before the pipeline can continue.
