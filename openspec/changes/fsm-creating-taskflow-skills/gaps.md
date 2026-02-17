# Gaps

<!-- GAP TEMPLATE - Fields by workflow stage:
CRITIQUE adds: ID, Severity, Source, Description
RESOLVE adds: Category, Decision

New gaps from critique should NOT have Category or Decision fields.

See tokamak:managing-spec-gaps for gap creation quality and category semantics.
-->

## GAP-137
- **Severity**: Medium
- **Source**: implicit-detection
- **Description**: The Confirmation Gate Mechanism (technical.md) specifies that confirmation gates use "AskUserQuestion (or equivalent user prompt)" but does not define what qualifies as an "equivalent" prompt mechanism. The same phrasing appears in infra.md's verification-by-design section. An implementor writing task descriptions that instruct the agent to pause for author approval would not know whether alternative mechanisms (e.g., a plain text question without AskUserQuestion, TodoWrite with a question, or other prompting patterns) satisfy the "equivalent" qualifier. This could lead to inconsistent confirmation gate implementations across tasks, where some use AskUserQuestion and others use an undefined alternative.

## GAP-138
- **Severity**: Low
- **Source**: implicit-detection
- **Description**: The Progressive Construction Protocol's Recovery clause (technical.md, State Management section) states that if the agent loses the in-progress artifact, it should "reconstruct from the most recent complete phase output visible in conversation history." The procedure assumes that at least one complete phase output remains visible after context compaction. No guidance exists for the scenario where aggressive compaction removes all intermediate artifacts from the visible conversation history, leaving no recovery baseline. While this may be an unlikely edge case, the recovery procedure provides no fallback or detection mechanism for when its own precondition (a visible phase output) fails to hold.

## GAP-139
- **Severity**: Medium
- **Source**: implicit-detection
- **Description**: The Known Risks section (functional.md) documents that large workflows may have poor UX during dependency mapping because "no upper workflow size limit is defined, and no scalability criteria (pagination, search, grouping) exist for presenting tasks during dependency mapping." While this is acknowledged as a risk, neither functional.md nor technical.md provides any actionable guidance for the implementor: no recommended maximum task count, no warning threshold at which the skill should advise the author about potential UX issues, and no fallback presentation strategy. An implementor has no basis for deciding when or how to address UX degradation, leaving the behavior entirely undefined for workflows above some unspecified size.

## GAP-140
- **Severity**: Low
- **Source**: implicit-detection
- **Description**: During authoring, CMP-dependency-map assigns task IDs sequentially (technical.md: "Newly added tasks receive the next sequential ID (max existing ID + 1); existing task IDs remain stable during authoring"). However, CMP-fsm-json renumbers all task IDs to topological order ("Renumber all task IDs to topological order (sequential starting at 1) and update all blockedBy references to match the new IDs"). The documentation does not specify whether the author is informed that the IDs they interacted with during dependency mapping and description writing will change in the final output. If the author references task IDs from earlier phases (e.g., in notes, external documentation, or verbal communication), the renumbering could cause confusion. No guidance exists on whether the skill should present the ID mapping to the author or acknowledge the renumbering during finalization.

## GAP-141
- **Severity**: Medium
- **Source**: design-critic
- **Description**: The SKILL.md template specifies a `name` field and CMP-fsm-json writes a `metadata.fsm` block. No cross-artifact consistency requirement exists ensuring that the skill name recorded in SKILL.md matches the corresponding identifier written into the FSM JSON metadata. An author or implementor editing one artifact without updating the other would produce a skill bundle where the human-readable identity and the machine-readable FSM metadata disagree, with no validation step catching the mismatch.

## GAP-142
- **Severity**: High
- **Source**: technical-critic
- **Description**: The Progressive Construction Protocol specifies that "each phase updates all entries before completing" as an invariant, but no workflow-validation requirement scenario covers this invariant, and no observable criterion exists to verify it holds. The protocol is defined in technical.md without a corresponding testable requirement — an implementor has no external observation, intermediate state check, or author-visible confirmation to verify the invariant is satisfied at the handoff into CMP-fsm-json. The concern was independently raised by both the technical-critic (as a testability issue) and the logic-critic (as an absent workflow-validation requirement).

## GAP-143
- **Severity**: Medium
- **Source**: technical-critic
- **Description**: The dependency-mapping workflow specifies cycle detection using Kahn's algorithm at the graph review step. Kahn's algorithm is a graph-theoretic procedure typically implemented in code, but the FSM plugin executes agent-authored task descriptions in natural language. The technical design does not specify whether cycle detection is performed by the agent reasoning over the graph, by a programmatic tool invocation, or by some other mechanism. An implementor cannot determine the intended execution model, and the feasibility of correctly applying Kahn's algorithm within an agent execution context is unverified.

## GAP-144
- **Severity**: Medium
- **Source**: requirements-critic
- **Description**: The self-contained-descriptions rule in the requirements file mixes normative strength within a single Then block — some clauses use SHALL and others use plain present tense. Mixing normative strength in the same Then block makes it ambiguous which obligations are mandatory and which are descriptive. A reader cannot determine from the requirement text alone which clauses impose testable obligations versus which describe expected behavior informally.

## GAP-145
- **Severity**: Medium
- **Source**: requirements-critic
- **Description**: The dependency-mapping Rule 5 preamble uses declarative present tense to express a mutability guarantee about the task list state. Declarative present tense does not carry the same normative force as SHALL and is not consistently interpreted as a testable obligation. An implementor reading this preamble alongside SHALL-phrased rules in the same file may not recognize the mutability guarantee as a binding constraint.

## GAP-146
- **Severity**: Medium
- **Source**: requirements-critic
- **Description**: The workflow-validation final validation rule's Then clause describes internal algorithm state — it references what the validation pass has internally determined — rather than specifying an observable output or behavior that a tester can verify from outside the component. A requirement whose Then clause refers to internal state cannot be independently tested without inspecting implementation internals, violating the testability standard for normative requirements.

## GAP-147
- **Severity**: Medium
- **Source**: requirements-critic
- **Description**: The dependency-mapping graph review rule contains a compound Then block that mixes a presentation obligation (displaying the graph to the author) with a capability assertion (the graph representation supports cycle detection). Compound Then blocks conflate multiple verifiable behaviors into a single requirement, making it impossible to satisfy or test each concern independently.

## GAP-148
- **Severity**: Low
- **Source**: requirements-critic
- **Description**: The workflow-intake scenarios for the no-modification path and the minor-adjustment path define "accepted" as the observable outcome. "Accepted" is an internal state label, not an observable behavior — a tester cannot observe whether intake has accepted a task without access to internal component state. The scenario outcomes for these paths do not specify what the author sees or what the agent produces as an externally visible result of acceptance.

## GAP-149
- **Severity**: Medium
- **Source**: requirements-coverage-critic
- **Description**: The requirements define scenarios for cycles introduced during the initial graph construction, but no scenario covers the case where a cycle is introduced by a task modification made during the dependency mapping graph review step. An author who modifies an existing dependency relationship during the interactive review could introduce a cycle not present at initial construction. The requirements do not specify what the workflow does when cycle detection fires in response to an author-initiated modification rather than an initial graph build.

## GAP-150
- **Severity**: Medium
- **Source**: validation-critic
- **Description**: The Brainstorming Gap Taxonomy (functional.md) defines depth and consistency as gap categories alongside coverage and clarity. No workflow-intake rule addresses depth gaps or consistency gaps, and infra.md defines no verification approach for detecting whether the intake process surfaces these categories. The taxonomy describes a classification the system is expected to support, but the intake requirements and verification infrastructure only demonstrably cover a subset of the defined categories.

## GAP-151
- **Severity**: Low
- **Source**: verification-critic
- **Description**: The infra.md coverage table for skill-file-generation defines rows for SKILL.md generation, the task definition file, and correct directory structure, but the requirements file defines an additional rule covering the SKILL.md self-validation path — where the generated SKILL.md is validated and re-generated if it fails self-validation. No coverage row exists for this self-validation and re-validation scenario. The verification approach for the self-validation failure path and the re-validation recovery is untracked in the coverage table. This concern was independently identified by the verification-critic and the design-for-test-critic.

## GAP-152
- **Severity**: Medium
- **Source**: verification-critic
- **Description**: The workflow-intake requirements include a scenario where all brainstorming sources are empty. The infra.md verification approach does not specify how to reproducibly establish this precondition — it requires ensuring that the context document, existing skill file, and any prior notes are all empty or absent simultaneously. Without a defined setup procedure for this boundary condition, the scenario cannot be reliably verified, making it effectively untestable in the behavioral verification environment described by infra.md.

## GAP-153
- **Severity**: Low
- **Source**: verification-critic
- **Description**: The dependency-mapping task-addition scenario specifies that the agent should prompt with relationship context relative to all existing tasks, but infra.md provides no boundary verification example for what "relationship prompting with all existing tasks" looks like at the boundary where the workflow contains exactly one existing task before the addition. Without a concrete boundary example, the verification approach cannot distinguish between a correct minimal-case prompt and an incomplete one.

## GAP-154
- **Severity**: Medium
- **Source**: design-for-test-critic
- **Description**: The dependency-mapping requirements define a rule for workflows containing a single task, specifying distinct behavior (no dependencies to map, immediate progression). The infra.md coverage table for dependency-mapping does not include a row for this single-task boundary case. An implementor using infra.md to guide behavioral verification has no documented approach for confirming the single-task path is exercised.

## GAP-155
- **Severity**: Medium
- **Source**: logic-critic
- **Description**: The technical design describes CMP-skill-md and CMP-fsm-json as components that produce SKILL.md and the FSM JSON file respectively, but the mechanism by which these components write files to the filesystem is implicit. The design does not specify whether file writing is performed via a tool call, an agent instruction to the executor, or another mechanism. An implementor cannot determine the intended file-write pathway from the component descriptions alone, leaving the write mechanism undefined in the technical specification.

## GAP-156
- **Severity**: Low
- **Source**: test-tasks-critic
- **Description**: The infra.md Testing Strategy section does not acknowledge the absence of automated CI/CD integration for behavioral verification. Given that infra.md explicitly establishes manual verification as the verification approach and states that no new pytest tests are added, the omission may be intentional, but the strategy section provides no statement to that effect. A reader evaluating the testing coverage of this change cannot distinguish between an intentional choice to rely on manual verification and an oversight in CI/CD planning.

## GAP-157
- **Severity**: High
- **Source**: test-infra-critic
- **Description**: The behavioral verification tasks in the implementation plan do not include or reference a setup task that establishes the verification environment prerequisites described in infra.md. An agent executing the behavioral verification tasks in isolation would have no task-level instruction to prepare the prerequisite environment, risking verification runs that fail due to missing setup rather than actual behavioral defects. The gap between infra.md's environment description and the task-level execution instructions leaves the verification setup undocumented at the task level.

## GAP-158
- **Severity**: Medium
- **Source**: test-infra-critic
- **Description**: The infra.md Testing Strategy states that no new pytest tests are added as part of this change. The validation-enhancement tasks in the implementation plan add new pytest tests. The strategy claim and the task plan are contradictory, meaning either the strategy description is outdated relative to the task plan, or the validation-enhancement tasks exceed the scope described in the testing strategy. An implementor or reviewer reading both artifacts would receive conflicting signals about the testing scope of this change.

## GAP-159
- **Severity**: Low
- **Source**: test-infra-critic
- **Description**: The OBJ-requirements-coverage objective in infra.md describes a process goal — ensuring scenarios are written for each requirement rule — rather than a measurable operational outcome. A process goal is not falsifiable in the same way as an operational outcome: it cannot be verified at a point in time without re-running the process. The objective framing makes it difficult to determine when the objective is satisfied independently of performing the authoring work.

## GAP-160
- **Severity**: Low
- **Source**: functional-consistency-critic
- **Description**: The skill-file-generation capability introduces filesystem write operations that expand the FSM plugin's scope beyond what project-level functional documentation describes for the plugin. The project-level description characterizes the FSM plugin as operating on task lists and agent behavior, without reference to producing persistent skill files on disk. The change adds a materially new capability class — authoring-time file production — that is not reflected in the project-level functional boundary description.

## GAP-161
- **Severity**: Medium
- **Source**: technical-consistency-critic
- **Description**: This change defines a component using the identifier CMP-fsm-json. The same identifier is used by an existing project-level component in the technical architecture. Reusing the same component identifier across a change-local definition and a project-level definition creates ambiguity: references to CMP-fsm-json in shared documentation, cross-change specifications, or future critiques cannot be resolved to a single authoritative component without additional context about which scope is intended.

## GAP-162
- **Severity**: Medium
- **Source**: technical-consistency-critic
- **Description**: The project-level technical documentation includes a no-cycle-detection Y-statement scoped to runtime behavior, but the statement reads as a blanket constraint. This change adds authoring-time cycle detection as a new capability. The project Y-statement does not acknowledge the scope boundary between runtime and authoring-time, meaning the new authoring-time cycle detection appears to contradict the project-level constraint when read without that scope context. The project documentation requires an update at merge time to clarify the scope boundary.

## GAP-163
- **Severity**: Medium
- **Source**: implementation-critic
- **Description**: GAP-29 resolved the functional-level definition of a deployable skill — what the skill represents and what it produces. The technical definition of plugin discoverability remains undefined: no component in this change specifies what the FSM plugin requires to discover and register a newly generated skill beyond the file being placed in the expected directory structure. An implementor does not know whether additional registration steps, index updates, manifest changes, or plugin reload signals are required for the FSM plugin to recognize and expose the new skill after file generation. This gap is partial relative to GAP-29, which addressed the functional level but left the technical discoverability mechanism unspecified.

## GAP-164
- **Severity**: Medium
- **Source**: integration-coverage-critic
- **Description**: GAP-109 resolved the cross-capability concern for tasks added during the description phase, confirming that description-phase task additions are evaluated against intake-phase quality criteria. A distinct uncovered path remains: a task added during dependency mapping (per the dependency-mapping task-addition rule) bypasses the intake validation gate entirely. The label and initial description provided at the dependency-mapping step are never evaluated against intake-phase quality criteria for specificity, actionability, and scope. This leaves a path by which under-specified tasks can enter the task list without passing intake validation. This gap is partial relative to GAP-109, which addressed the description-phase path but left the dependency-mapping path unresolved.
