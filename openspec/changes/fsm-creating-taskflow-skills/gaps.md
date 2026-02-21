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

### GAP-32: Cycle correction path in CMP-descriptions after split/merge re-validation failure is undefined
- **Source**: logic-critic
- **Severity**: medium
- **Description**: CMP-descriptions specifies that after a confirmed split or merge, the pipeline does not continue until dependency graph re-validation passes, and the re-validation failure scenario directs the author to resolve the cycle before proceeding. However, neither CMP-descriptions nor the re-validation failure scenario specifies the correction path — whether the author resolves the cycle in-place within the description-writing phase, re-enters dependency mapping, or follows some other path. GAP-25 defined correction paths for cycle detection failures at CMP-final-validation, and GAP-27 established the pipeline gate after split/merge re-validation, but neither addresses the correction mechanism for cycles detected during the description phase. This concern is related to the resolved gaps but is not covered by them.

### GAP-33: dependency-mapping capability description uses mechanism language rather than user-facing outcome
- **Source**: functional-critic
- **Severity**: low
- **Description**: The dependency-mapping capability description in functional.md states that skill authors can encode dependency patterns "with automatic dependency graph updates and re-validation." The phrase "automatic dependency graph updates and re-validation" describes an internal mechanism rather than what the skill author observes or receives. Capability descriptions should express user-facing outcomes.

### GAP-34: Y-statement #3 contradicts CMP-skill-md and CMP-final-validation documented behavior
- **Source**: design-critic
- **Severity**: high
- **Description**: The Y-statement governing CMP-skill-md's independence (technical.md Decisions section) asserts that CMP-final-validation does not cover SKILL.md checks because SKILL.md content is functionally independent of fsm.json and the frontmatter check covers all applicable output correctness concerns. However, CMP-final-validation's responsibilities explicitly include a name-consistency check that reads SKILL.md content from disk. The CMP-skill-md component description also states that it "completes independently without feeding into CMP-final-validation," which contradicts the documented data-read dependency shown in the system overview diagram and described in CMP-final-validation's dependency list. The Y-statement's "accepting" clause and the component prose are inconsistent with the actual data dependencies.

### GAP-35: Agent-native topological renumbering in CMP-fsm-json-finalize is inconsistent with the cycle-detection justification
- **Source**: technical-critic
- **Severity**: medium
- **Description**: The Y-statement justifying the cycle detection Python script (technical.md Decisions section) rejects agent-native LLM reasoning because it is unreliable for correctness-critical checks. CMP-fsm-json-finalize's topological renumbering responsibility — sequentially renumbering all task IDs and updating all corresponding blockedBy cross-references atomically — is equally correctness-critical: an ID/blockedBy mismatch would produce a silently broken dependency graph. No justification is documented for why agent-native renumbering is acceptable here when it was rejected for cycle detection on the same reliability grounds.

### GAP-36: Intermediate partial fsm.json has no specified file path
- **Source**: implementation-critic
- **Severity**: medium
- **Description**: The technical design documents a progressive fsm.json construction pattern: CMP-dependency-map writes a partial fsm.json, CMP-descriptions reads and updates it in-place, and CMP-fsm-json-finalize reads and finalizes it. No file path for the intermediate partial fsm.json is documented. CMP-fsm-json-finalize's final output path requires the confirmed skill name (produced by CMP-skill-md, which runs concurrently), but the intermediate file path must be deterministic so CMP-descriptions can locate it before the skill name is confirmed. Without a specified path, implementors must infer or invent the location.

### GAP-37: CMP-fsm-json-finalize has no documented dependency on CMP-skill-md and no mechanism for acquiring the confirmed skill name
- **Source**: implementation-critic
- **Severity**: medium
- **Description**: CMP-fsm-json-finalize requires the confirmed skill name to populate the metadata.fsm field in each fsm.json entry, but its documented dependencies list only the partial fsm.json produced by CMP-dependency-map and updated by CMP-descriptions. CMP-skill-md — which determines and confirms the normalized skill name — runs concurrently with the dependency/description chain and writes only SKILL.md to disk. No mechanism is documented for CMP-fsm-json-finalize to acquire the confirmed skill name, and no task dependency or data-read dependency between CMP-skill-md and CMP-fsm-json-finalize is specified.

### GAP-38: Workflow-validation phase scenarios encode the success condition as a Then-step conditional rather than a Given precondition
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: The incremental validation scenarios in the workflow-validation requirements (Rule 1, phase-specific scenarios) express the success condition inside the Then step using "if" — for example, "Then validation passes if the step list contains at least one labeled step." The "if" clause encodes the precondition for success inside the outcome step. Per Gherkin normative guidance, Then steps must state unconditional observable outcomes; the success condition belongs in Given so that When and Then describe what happens unconditionally when that precondition holds.

### GAP-39: Topological renumbering scenario bundles two independently falsifiable outcomes in a single Then step
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: The skill-file-generation scenario covering topological renumbering during fsm.json finalization bundles two independently verifiable outcomes — sequential ID assignment and author notification of the old-to-new mapping — in a single Then step. Each outcome can fail independently: an implementation could renumber correctly without presenting the mapping, or present the mapping without correct renumbering. These are distinct assertions that should be separated into individual Then clauses.

### GAP-40: Dependency-mapping task rename scenario title joins two behaviors with an em-dash
- **Source**: requirements-critic
- **Severity**: low
- **Description**: The dependency-mapping task rename scenario title uses an em-dash to join two behaviors in a single title, following the same anti-pattern addressed by GAP-16 for other scenarios. Per writing-markdown-gherkin guidance, scenario titles must name a single behavior being verified. The rename scenario was not corrected when GAP-16 resolved similar titles in the same requirements file.

### GAP-41: Author declining a split or merge suggestion has no specified behavior
- **Source**: requirements-coverage-critic
- **Severity**: medium
- **Description**: The self-contained-descriptions requirements specify the confirmed-acceptance path for both split and merge suggestions (scenarios 3.4 and 3.5), but no scenario covers what happens when the author declines. After a decline, it is unspecified whether the skill accepts the description as-is, re-evaluates it, prompts for a different resolution, or continues to the next task. The decline path is a primary alternative flow that must be defined to make the sizing rule complete.

### GAP-42: Self-contained-descriptions re-validation failure Scenario Outline examples describe logically unreachable states
- **Source**: verification-critic
- **Severity**: medium
- **Description**: The re-validation failure Scenario Outline in self-contained-descriptions (covering split and merge operations) specifies that the updated dependency graph contains a cycle after the confirmed operation. For the split row, the split mechanism applies the max+1 rule and inherits all parent and child relationships from the original task — this operation introduces no new edges that could create a back-edge, so a cycle cannot result from a correct split. For the merge row, the merge mechanism unions the blockedBy sets of two adjacent tasks (which share a direct edge), producing a graph that is a strict subgraph of the original — union of adjacent-node blockedBy entries cannot introduce a cycle in a previously acyclic graph. Both example rows describe states that are logically unreachable through correct execution of the specified mechanisms.

### GAP-43: Workflow-intake normalization and combined-intake scenarios produce identical observable outcomes
- **Source**: verification-critic
- **Severity**: low
- **Description**: The workflow-intake normalization scenario and the combined multi-source intake scenario both specify that the skill produces a unified normalized step list incorporating contributions from all active intake sources. The observable Then step outcome is functionally identical between the two scenarios. When two scenarios produce the same observable outcome, they cannot be independently falsified — a behavior that satisfies one necessarily satisfies the other, making one scenario redundant for verification purposes.

### GAP-44: infra.md Context section contradicts the Testing Strategy on code changes
- **Source**: design-for-test-critic
- **Severity**: high
- **Description**: The infra.md Context section states that this change delivers "pure content files with no code changes to hydrate-tasks.py or the hook system." The Testing Strategy section specifies adding the description field to the validate_fsm_tasks required field checks — an explicit code change to hydrate-tasks.py. The two sections directly contradict each other, leaving the scope of the deliverable ambiguous.

### GAP-45: No environment specification for the structural pytest validation tests
- **Source**: design-for-test-critic
- **Severity**: medium
- **Description**: The infra.md Testing Strategy specifies structural validation tests via pytest for the description field validation change to validate_fsm_tasks, but provides no environment specification: Python version, virtual environment setup, and pytest installation are not documented. The Verification Environment section covers only Claude Code and FSM plugin prerequisites for behavioral verification; it does not address the Python test execution environment needed to run the structural pytest tests. Without this specification, verifiers cannot reproduce the test environment.

### GAP-46: Scenario-specific setup omits the re-validation failure scenario precondition
- **Source**: design-for-test-critic
- **Severity**: low
- **Description**: The infra.md scenario-specific setup section documents directory-state preconditions for the directory-creation and collision-detection scenarios, but omits any precondition for the re-validation failure scenario in self-contained-descriptions. Triggering a cycle after a confirmed split or merge requires a specific dependency graph configuration — a precondition that must be established before exercising the scenario. Without this entry, verifiers have no documented setup path for that scenario.

### GAP-47: Workflow-validation final state scenario implies write-after-validate contrary to the design
- **Source**: logic-critic
- **Severity**: medium
- **Description**: The workflow-validation passing scenario (under the rule covering clear validation results) states that the skill confirms the workflow is "ready to be written to disk." This phrasing implies that file writing occurs after final validation passes. The technical design places CMP-skill-md and CMP-fsm-json-finalize — both of which write artifacts to disk — before CMP-final-validation in the task dependency graph. GAP-3 corrected the same write-order implication in OBJ-incremental-validation, but the corresponding requirement scenario retains the same misleading phrasing.

### GAP-48: No component is responsible for eliciting the plugin directory from the author
- **Source**: logic-critic
- **Severity**: medium
- **Description**: The skill-file-generation capability requires the skill to place files under a path of the form `plugins/<plugin>/skills/<skill>/`. CMP-skill-md and CMP-fsm-json-finalize both reference this path and guide the author on file placement. However, no component documents the responsibility for collecting the plugin directory (`<plugin>`) from the author. The skill name is handled by CMP-skill-md's normalization step, but the plugin directory is a separate authoring input that has no specified collection point.

### GAP-49: CMP-dependency-map presentation responsibility omits the degenerate single-task case
- **Source**: logic-critic
- **Severity**: low
- **Description**: CMP-dependency-map's responsibilities describe presenting the dependency graph for author review, but do not specify the presentation for the degenerate case where the workflow contains exactly one task. In this case there are no dependencies to show, yet the dependency-mapping requirements include an explicit scenario specifying that the skill confirms the trivially empty graph and proceeds. The component description does not align with this required behavior.

### GAP-50: Integration.feature.md pipeline gate justification cites only success-path scenarios
- **Source**: integration-critic
- **Severity**: medium
- **Description**: The integration.feature.md forward-only pipeline justification references self-contained-descriptions:3.4–3.5 as capturing the split/merge cross-capability callback. Those scenarios cover the confirmed-acceptance success path. The re-validation failure scenario added by GAP-27's resolution — which specifies that the pipeline does not continue when re-validation detects a cycle after a confirmed split or merge — is not cited. The justification paragraph is incomplete: it characterizes the split/merge callback as the only designed exception without accounting for the failure branch of that callback.

### GAP-51: Integration.feature.md dependency-mapping citation range excludes the predecessor-inheritance scenario
- **Source**: integration-critic
- **Severity**: low
- **Description**: The integration.feature.md step-list-modifications justification paragraph cites the dependency-mapping modification scenarios to support the claim that no cross-capability impact occurs. The citation range does not include the predecessor-inheritance scenario added by GAP-18's resolution, which specified that removing a middle-node task causes its dependents to inherit its predecessors. This scenario involves a structural graph transformation during dependency mapping that affects which tasks block which — a change that has implications for the description-writing phase's task ordering. The exclusion leaves the justification incomplete.

### GAP-52: Multi-capability cascade for cycle-correction backward traversal has no integration scenario
- **Source**: integration-coverage-critic
- **Severity**: medium
- **Description**: CMP-final-validation's cycle detection correction path directs the author to re-enter dependency mapping (CMP-dependency-map) to restructure offending dependencies. This is a backward traversal from a later pipeline stage to an earlier one, which the integration.feature.md's forward-only pipeline claim explicitly addresses for the split/merge case. However, no integration scenario covers this multi-capability cascade: re-entering dependency mapping after final-validation cycle detection requires descriptions (written by CMP-descriptions) to potentially be re-evaluated after the dependency graph changes, and the relationship between this backward traversal and the pipeline's claimed forward-only property is not addressed in integration.feature.md.

### GAP-53: The PreToolUse guard blocking disk reads of fsm.json conflicts with the progressive fsm.json construction pattern
- **Source**: technical-consistency-critic
- **Severity**: high
- **Description**: The FSM plugin's PreToolUse guard blocks the agent from reading SKILL.md and fsm.json directly. The technical design for this change documents a progressive fsm.json construction pattern in which CMP-descriptions must read and update the partial fsm.json that CMP-dependency-map wrote to disk. This cross-task disk read of fsm.json occurs within the authoring workflow and is a core part of the specified data flow. The technical context acknowledges the guard exists but neither the component specifications nor the data flow documentation addresses how the authoring workflow's fsm.json read operations interact with the guard — whether the guard applies to the intermediate partial fsm.json, whether an exemption exists, or whether the construction pattern must be redesigned to avoid the conflict.
