# Resolved Gaps

<!-- GAP TEMPLATE - Same structure as gaps.md:
### GAP-XX: Title
- **Severity**: high|medium|low
- **Description**: ...
- **Category**: resolved|superseded|deprecated
- **Superseded by**: GAP-XX (only when Category is superseded)
- **Decision**: ...
- **Outcome**: ... (optional — records what actually changed in artifacts after Decision was applied)
- **Rationale**: ... (only when Category is deprecated — must cite specific evidence: artifact change, code evidence, or context shift)
- **Current approach**: ... (only when Category is superseded — points to up-to-date information)
-->

### GAP-1: Intake path selection mechanism undefined
- **Severity**: high
- **Description**: The requirements (workflow-intake:1.1) imply explicit author selection of intake path ("When the author selects the `<intake_path>` intake path"), but the technical design states "the agent evaluates each, performs the one that applies, and marks the other two complete" — implying automated detection. The technical design lacks feasibility detail on how the agent determines which intake path applies, what signals or author interaction enable this determination, and what happens if the agent misidentifies the path. Additionally, no testability mechanism exists for verifying the skip-evaluation behavior (TECH-3), and the intake applicability evaluation criteria are underspecified (COMPONENT-3). Sources: Technical TECH-1, TECH-3; Design COMPONENT-3; Logic GAP-2.
- **Category**: superseded
- **Superseded by**: GAP-44
- **Decision**: Agent evaluates input and proposes which intake path applies; author confirms before work begins. CMP-normalize is path-agnostic ("collect whatever workflow material exists and normalize"). Adds an author confirmation step to intake path detection.
- **Current approach**: Intake paths are non-exclusive sources (GAP-44 resolution). Each intake task evaluates whether the author's input includes material for its source and contributes applicable material. The "pick one path" framing was removed. CMP-normalize concatenates all contributions. See technical.md intake component descriptions and GAP-44 for the definitive approach.

### GAP-2: activeForm field generation not specified
- **Severity**: high
- **Description**: CMP-descriptions produces `{task_id, task_label, description, activeForm}` entries and CMP-fsm-json encodes `activeForm` in JSON output, but no component specifies how activeForm is generated (e.g., transforming task labels into present-continuous form like "Validating dependencies"). Requirements also lack a scenario covering activeForm generation behavior. Sources: Logic GAP-1; Coverage user-behaviors-2.
- **Category**: resolved
- **Decision**: CMP-descriptions auto-generates activeForm by deriving present-continuous form from task labels. Presents generated values to author for confirmation/override. Add activeForm generation to CMP-descriptions responsibilities and add a requirement scenario for the behavior.

### GAP-3: Data flow schema mismatch between normalize and dependency-map
- **Severity**: high
- **Description**: The data flow table in technical.md shows CMP-normalize outputting `{label, description}` pairs, but CMP-dependency-map's output adds `task_id` and `blockedBy[]` fields that appear without documented derivation from the normalize output. The schema transformation from `{label, description}` to `{task_id, task_label, blockedBy[]}` is implicit — it's unclear whether task_id is generated sequentially, whether task_label maps directly to label, or whether additional fields are introduced. Source: Design ARCH-1.
- **Category**: resolved
- **Decision**: Document explicit data transformation chain in technical.md. CMP-dependency-map assigns sequential task IDs (after dependencies order the tasks, not at normalize). Each phase adds specific fields to the cumulative artifact. Add a Data Transformation section to technical.md.

### GAP-4: Inter-phase state storage unspecified
- **Severity**: high
- **Description**: The technical design defines a 10-component pipeline with data flowing between phases but does not specify how intermediate artifacts (normalized step list, dependency table, enriched task list) are stored or passed between components. Since FSM tasks execute as independent agent turns, the mechanism by which CMP-dependency-map accesses CMP-normalize's output is unspecified. Source: Design ARCH-4.
- **Category**: superseded
- **Superseded by**: GAP-31
- **Decision**: Conversation context is the primary state-passing mechanism between tasks (consistent with how FSM tasks already work). Document this in technical.md. Consider progressive fsm.json construction as a context-reduction strategy for long workflows.
- **Outcome**: technical.md now defines 9 components with explicit Data Transformation and State Management sections.
- **Current approach**: Progressive construction is the standard workflow (GAP-31 resolution). The skill builds all task stubs first, then iteratively adds fields across all tasks as each phase completes. Conversation context is no longer framed as the "primary" mechanism.

### GAP-5: Ambiguity resolution in requirements lacks observable criteria
- **Severity**: high
- **Description**: Several requirement scenarios specify that the skill resolves ambiguity or evaluates quality but provide no observable criteria for verification. For example, workflow-intake:2.2 says "the skill prompts for clarification on vague descriptions that lack specificity about what work is performed" — but "vague" and "lack specificity" are subjective terms without testable thresholds. Source: Requirements testability-1.
- **Category**: resolved
- **Decision**: Replace subjective terms with concrete observable criteria in requirements. E.g., replace "vague descriptions that lack specificity" with "descriptions that do not specify what work is performed."
- **Outcome**: workflow-intake:3.2 now reads "descriptions that do not specify what work is performed" — subjective terms removed.

### GAP-6: Weak normative language ("can") in author action scenarios
- **Severity**: high
- **Description**: Multiple requirement scenarios use "can" instead of "SHALL" for author actions, creating ambiguity about whether these are optional capabilities or required behaviors. For example, workflow-intake:4.1 "Then the author can add new steps" — is the skill required to support adding new steps, or merely permitted to? Requirements should use normative language (SHALL/SHALL NOT/MAY) consistently. Source: Requirements normative-1.
- **Category**: resolved
- **Decision**: Change "can" to "SHALL be able to" where the skill must support the action. Keep "MAY" only for truly optional behaviors.
- **Outcome**: "can" replaced with "SHALL be able to" in affected scenarios across requirements.

### GAP-7: Confirm vs modify mutually exclusive in one scenario
- **Severity**: high
- **Description**: Some requirement scenarios combine mutually exclusive actions (confirm vs modify) in a single scenario. For example, "the author can confirm, add, remove, reorder, or rename steps" contains a confirmation path and multiple modification paths that should be separate scenarios to maintain atomicity. A single scenario cannot test both "author confirms unchanged" and "author modifies" — these are distinct behaviors. Source: Requirements atomicity-1.
- **Category**: resolved
- **Decision**: Split compound confirm/modify scenarios into separate atomic scenarios: one for "author confirms without changes" and one for "author modifies steps."
- **Outcome**: Compound scenarios split into atomic scenarios (e.g., workflow-intake:2.3 for confirm, 2.4 for modify).

### GAP-8: No scenario for blocks vs blockedBy direction
- **Severity**: high
- **Description**: Requirements cover encoding dependencies as `blockedBy` arrays but include no scenario testing the user-facing distinction between "blocks" and "blockedBy" directionality. When an author says "task A blocks task B," the skill must encode this as `blockedBy: [A]` on task B — but no requirement scenario verifies this directional mapping is presented correctly to the author or encoded correctly. Source: Coverage user-behaviors-1.
- **Category**: resolved
- **Decision**: Add a requirement scenario to dependency-mapping that tests directional encoding: author declares blocking relationship, skill encodes as blockedBy on the blocked task.
- **Outcome**: dependency-mapping:1.3 now tests blockedBy directional encoding.

### GAP-9: Description field not validated in structural validation
- **Severity**: high
- **Description**: The infra.md documents `validate_fsm_tasks` as performing structural validation on generated fsm.json, but the validation function (per existing code) checks for required fields like `id` and `subject`. The `description` field — which is the primary deliverable of the self-contained-descriptions capability — is not listed as a validated field in the structural checks. If `description` is empty or missing, structural validation would not catch it. Source: Verification testability-1.
- **Category**: resolved
- **Decision**: Add description field to validate_fsm_tasks required field checks in hydrate-tasks.py. Catches empty/missing descriptions at hydration time.

### GAP-10: Validation failure recovery paths unspecified
- **Severity**: medium
- **Description**: Requirements workflow-validation:1.4-1.6 describe a correction loop (validation fails → author corrects → re-validates → proceeds), but the technical design does not specify the mechanics. If CMP-normalize detects a step with no description, does it: (a) fail/block the task, (b) loop internally within the same task execution, or (c) create a correction task? The risk section mentions "CMP-normalize gate provides a recovery point" but does not define what recovery entails. Without clear mechanics, requirements 1.6 cannot be implemented. Sources: Design ARCH-5; Logic GAP-5.
- **Category**: resolved
- **Decision**: Agent loops internally within each task. Task description includes: "If validation fails, present the issue, ask author to correct, then re-validate before completing the task." The correction loop happens within a single task execution.

### GAP-11: INT-fsm-json output specification inconsistency
- **Severity**: medium
- **Description**: The technical design's data flow table shows CMP-fsm-json outputting fields per "INT-fsm-json schema," but the component responsibilities section lists a different field set. The data flow table references `{id, subject, description, activeForm, blockedBy}` while the full INT-fsm-json schema includes additional fields (`metadata`, `owner`, `status`, `blocks`). It's unclear which is the authoritative output specification. Source: Design ARCH-2.
- **Category**: resolved
- **Decision**: CMP-fsm-json outputs the 5 core fields (id, subject, description, activeForm, blockedBy) plus metadata with {"fsm": "skill-name"}. Other optional fields (owner, status, blocks) omitted — defaults apply at hydration time.

### GAP-12: CMP-descriptions authoring model ambiguous
- **Severity**: medium
- **Description**: CMP-descriptions' responsibilities include both guiding the author ("Guide the author to include goal, constraints, and expected outcome") and performing detection ("Detect and flag external references"). It's unclear whether the component is primarily an interactive guide (author writes, skill reviews) or an automated generator (skill writes, author approves). The technical design uses both patterns without distinguishing. Source: Design COMPONENT-1.
- **Category**: resolved
- **Decision**: Skill generates descriptions from the intake understanding of tasks, presents drafts to author for approval/editing. The authoring model is "skill generates, author approves/edits."
- **Outcome**: CMP-descriptions now says "Generate description drafts from the intake understanding; present each draft to the author for approval or editing."

### GAP-13: Prohibited terms list missing from technical.md
- **Severity**: medium
- **Description**: CMP-skill-md and CMP-final-validation both reference "prohibited terms" with an inline list (`fsm.json`, `hydration`, `hydrate`, `hook`, `PostToolUse`, `PreToolUse`, `task file`, `task directory`, `.json`). This list appears in component responsibilities but is not defined as a shared specification. If different components use different lists, prohibited terms could slip through one check but be caught by another — or vice versa. Source: Design COMPONENT-2.
- **Category**: superseded
- **Superseded by**: GAP-120
- **Decision**: Define a named SPEC-prohibited-terms specification in technical.md with the canonical list. Components reference it by name rather than repeating inline.
- **Outcome**: SPEC-prohibited-terms defined as named specification in technical.md. Components reference by name.
- **Current approach**: GAP-120 removed the SPEC-prohibited-terms named specification from technical.md entirely. Automated prohibited term scanning was replaced by author judgment during SKILL.md writing.

### GAP-14: Self-contained descriptions conflict with intake convergence
- **Severity**: medium
- **Description**: The self-containment principle (each task description is the sole instruction source after compaction) conflicts with the intake convergence pattern (three intake paths → normalize). CMP-normalize must access output from whichever intake task ran, but if task descriptions are truly self-contained, CMP-normalize's description cannot reference "the output from CMP-intake-existing" — it must describe what to normalize without knowing which intake path was taken. The technical design doesn't address how self-containment applies to the normalize fan-in point. Source: Technical TECH-2.
- **Category**: superseded
- **Superseded by**: GAP-88
- **Decision**: Resolved together with GAP-1. CMP-normalize is path-agnostic — it says "collect whatever workflow material exists and normalize into step list format" without referencing which intake path ran. Self-containment preserved because the description doesn't need to know the source.
- **Current approach**: GAP-88 restructured intake from three parallel paths fanning into normalize to (IE|IW) → IB → N (two input-based intakes fan into brainstorming, then normalize). The "three intake paths → normalize" convergence pattern no longer exists. CMP-normalize's path-agnostic design (this gap's decision) remains the current approach in technical.md.

### GAP-15: OBJ-incremental-validation implementation unclear
- **Severity**: medium
- **Description**: The technical design states that incremental validation is "embedded within each phase task" as a design objective (OBJ-incremental-validation), but the component descriptions show validation responsibilities distributed inconsistently. Some components have explicit validation steps (CMP-normalize: "Validate the normalized list: at least two steps, no empty descriptions") while others reference validation indirectly. The boundary between embedded phase validation and CMP-final-validation's comprehensive checks is blurry. Source: Design OBJECTIVE-1.
- **Category**: resolved
- **Decision**: Add an explicit validation scope table to technical.md mapping each check to its location: phase checks handle format/completeness within one phase, final checks handle cross-cutting concerns (cycles, self-containment, prohibited terms).
- **Outcome**: CMP-normalize now validates "at least one step" (changed from two per GAP-19 decision).

### GAP-16: "Should" normative language in dependency-mapping:4.2
- **Severity**: medium
- **Description**: Requirement scenario dependency-mapping:4.2 uses "should" instead of "SHALL" for a normative statement. In MDG format, "should" indicates a recommendation rather than a requirement, creating ambiguity about whether this behavior is mandatory. Source: Requirements normative-2.
- **Category**: resolved
- **Decision**: Change "should" to "SHALL" in dependency-mapping:4.2 to make the behavior mandatory and unambiguous.
- **Outcome**: dependency-mapping:4.2 now uses "SHALL" instead of "should."

### GAP-17: Internal identification without observable output
- **Severity**: medium
- **Description**: Some requirement scenarios describe internal agent actions ("the skill identifies...") without specifying an observable output. For verification purposes, identification must produce a visible artifact (e.g., a message to the author, a flag in output) — otherwise the scenario is untestable. Source: Requirements testability-2.
- **Category**: resolved
- **Decision**: Remove the "identifies" step and merge into the next observable step. E.g., "Then the skill flags the missing context and prompts the author to add it."

### GAP-18: "Tailored to" lacks observable criteria
- **Severity**: medium
- **Description**: Requirement scenarios using "tailored to" or similar adaptive language lack specific criteria for what constitutes appropriate tailoring. Without observable benchmarks, these scenarios cannot be verified as passing or failing. Source: Requirements testability-3.
- **Category**: resolved
- **Decision**: Replace "tailored to" with concrete observable behavior specific to each intake path. E.g., "presents extraction guidance for existing skills" vs "presents brainstorming prompts."

### GAP-19: Missing single-step workflow boundary scenario
- **Severity**: medium
- **Description**: Requirements specify "at least two discrete steps" as a minimum, but no scenario tests the boundary condition where an author provides input that yields exactly one step. The skill's behavior when the minimum is not met (reject? prompt for more steps? suggest splitting?) is not covered by any requirement scenario. Source: Coverage boundary-conditions-1.
- **Category**: resolved
- **Decision**: Remove the minimum-2-steps constraint. A single-step FSM workflow is valid (author may expand later). Update all three intake tasks and CMP-normalize to accept 1+ steps.
- **Outcome**: Minimum changed to 1 step across all artifacts. CMP-normalize validates "at least one step."

### GAP-20: No scenario for duplicate labels or IDs
- **Severity**: medium
- **Description**: Requirements cover dependency validation and structural integrity but include no scenario for duplicate task labels or duplicate IDs in the generated output. If two steps have the same label, or if ID generation produces duplicates, the behavior is unspecified. Source: Coverage boundary-conditions-2.
- **Category**: resolved
- **Decision**: Close gap — duplicate labels are not a problem. IDs are auto-generated sequentially so cannot collide. Duplicate labels are valid (author distinguishes by description). No requirement changes needed.

### GAP-21: Metadata field handling unspecified in fsm.json generation
- **Severity**: medium
- **Description**: The INT-fsm-json schema includes `metadata`, `owner`, `status`, and `blocks` fields beyond the core `{id, subject, description, activeForm, blockedBy}` set. CMP-fsm-json's responsibilities only address the core fields. It's unspecified whether metadata (e.g., `{"fsm": "skill-name"}` per anti-clobber convention), owner, status defaults, or computed `blocks` arrays should be populated. Source: Logic GAP-3.
- **Category**: resolved
- **Decision**: Resolved together with GAP-11. CMP-fsm-json populates metadata with {"fsm": "skill-name"} following anti-clobber convention. Other optional fields omitted.
- **Outcome**: CMP-fsm-json now explicitly includes metadata {"fsm": "skill-name"} in responsibilities.

### GAP-22: Author confirmation gate enforcement mechanism unspecified
- **Severity**: medium
- **Description**: Multiple components specify author confirmation gates (CMP-normalize, CMP-intake-brainstorm, CMP-dependency-map) where the task must "not advance until the author approves." However, in a task-based workflow where tasks complete atomically, the mechanism for pausing mid-task, awaiting author input, incorporating modifications, and then completing is not defined. Source: Logic GAP-4.
- **Category**: resolved
- **Decision**: Tasks use AskUserQuestion (or equivalent user prompt) within task execution to implement confirmation gates. The task pauses, gets author approval, then completes. Document this mechanism in technical.md.

### GAP-23: Flowchart ordering reference misplaced
- **Severity**: low
- **Description**: The architecture section references a flowchart for component ordering, but the reference appears in a location that doesn't align with the actual mermaid diagram placement in the document. Source: Design CONTEXT-1.
- **Category**: resolved
- **Decision**: Clarified which flowchart the "authoritative ordering" reference applies to — added explicit qualifier specifying this skill's task dependency graph vs the parent FSM hydration pipeline.


### GAP-25: functional.md "Why" section describes technical process
- **Severity**: medium
- **Description**: The "Why" section in functional.md describes implementation-level details ("reverse-engineering task file structure from validation code," "manually constructing dependency graphs," "context compaction"). A functional spec should describe the user problem in domain terms, not the technical process that causes it. Source: Functional IMPL-LEAK-1.
- **Category**: resolved
- **Decision**: Rewrite "Why" section in user terms. Keep "context compaction" since it's an external mechanism users deal with, but remove references to "task file structure from validation code" and "manually constructing dependency graphs."
- **Outcome**: Why section rewritten to "understanding the structural conventions, encoding dependency relationships between tasks."

### GAP-26: functional.md "What Changes" describes internal mechanics
- **Severity**: high
- **Description**: The "What Changes" section references internal mechanics ("invokes `finite-skill-machine:creating-taskflow-skills`," "incremental validation checks at each phase," "task descriptions fully replace it"). This exposes plugin architecture and compaction mechanics that belong in the technical spec, not the functional description of what changes for the user. Source: Functional IMPL-LEAK-2.
- **Category**: resolved
- **Decision**: Rewrite "What Changes" to be user-facing. Remove plugin architecture references ("invokes finite-skill-machine:creating-taskflow-skills") and compaction mechanics. Frame as what the author experiences.
- **Outcome**: What Changes section rewritten in user-facing terms. Plugin invocation and compaction mechanics removed.

### GAP-27: functional.md Scope describes internal architecture
- **Severity**: medium
- **Description**: The Scope section describes "three separate intake paths with dedicated guidance per source type, converging into shared downstream steps" and "incremental validation woven throughout plus comprehensive final validation pass" — these are architectural details about how the skill is structured internally, rather than the user-facing scope of what the change delivers. Source: Functional IMPL-LEAK-3.
- **Category**: superseded
- **Superseded by**: GAP-88
- **Decision**: Rewrite Scope as user experience. Replace "three separate intake paths converging into shared downstream steps" with "supports three starting points." Replace "incremental validation woven throughout" with "validates work at each step."
- **Outcome**: Scope rewritten as "Supports three starting points" and "Validates work at each step."
- **Current approach**: GAP-88 restructured intake architecture from three parallel sources to two input-based intakes plus sequential brainstorming. Scope now reads "Supports multiple starting points for defining a workflow: analyzing an existing skill, providing written step descriptions, or both — with brainstorming to fill gaps."

### GAP-28: functional.md Out of Scope references internal components
- **Severity**: low
- **Description**: The Out of Scope section references "task hydration script or hook system," "task file schema or validation rules" — internal implementation components that should not appear in a functional spec. Out of scope items should be framed in user-facing terms. Source: Functional IMPL-LEAK-4.
- **Category**: resolved
- **Decision**: Rewrote Out of Scope items in user-facing terms — changed "task hydration script or hook system" to "runtime workflow execution behavior" and "task file schema or validation rules" to "workflow file format specifications."

### GAP-29: skill-file-generation capability leaks file structure
- **Severity**: medium
- **Description**: The skill-file-generation capability description mentions "a SKILL.md + task definition pair" which partially exposes the file structure to the functional level. The functional spec should describe what the author gets (a deployable skill) not how it's stored (specific file pairs). Source: Functional IMPL-LEAK-5.
- **Category**: resolved
- **Decision**: Abstract to "deployable skill" — change "produce a SKILL.md + task definition pair" to "produce a deployable skill with author-facing documentation and a structured workflow definition."
- **Outcome**: Capability now reads "produce a deployable skill with author-facing documentation and a structured workflow definition."

### GAP-30: Known Risks contains implementation concerns
- **Severity**: low
- **Description**: The Known Risks section includes "skill text that teaches task authoring must carefully avoid exposing internal file structure" and "tasks that are too large risk partial context loss within a single task" — both reference implementation concerns (file structure, context windows) rather than user-facing risks. Source: Functional IMPL-LEAK-6.
- **Category**: resolved
- **Decision**: Rewrote Known Risks in user-facing terms — changed "skill text that teaches task authoring must carefully avoid exposing internal file structure" to "generated skill documentation may inadvertently reveal how the workflow is stored" and "tasks that are too large risk partial context loss within a single task" to "overly broad tasks may lose important details during execution."

### GAP-32: Description validation scope ambiguous in infra.md
- **Severity**: low
- **Description**: infra.md states the description field "should be added" to validate_fsm_tasks required field checks but does not classify this as in-scope work for this change, a tracked task, or a future enhancement. The "should" creates ambiguity about whether structural validation of the description field is a deliverable of this change or a deferred recommendation.
- **Category**: resolved
- **Decision**: Changed "should be added" to "SHALL be added as part of this change" in infra.md to clarify scope.

### GAP-33: Self-containment audit verification mechanism undefined
- **Severity**: high
- **Description**: CMP-final-validation must audit self-containment but no specification exists for how to detect references to SKILL.md text, sibling task references, or assumed context beyond explicit prohibited terms. SPEC-prohibited-terms (GAP-13 resolved) covers explicit terms like `fsm.json`, `hydration`, `hook`, but not subtle violations such as implicit assumptions ("at this point the configuration will already exist") or references to earlier phase outputs. The validation algorithm for detecting these contextual dependencies is unspecified. Similar to GAP-13 (resolved), which addresses only explicit prohibited terms.
- **Category**: superseded
- **Superseded by**: GAP-38 → GAP-53 → GAP-57
- **Decision**: Use reference-free description test combined with context-dependency extraction. For each description: (1) extract all noun phrases and verify each refers to something defined within the description itself or is a well-known external concept — flag any that implicitly assume context from elsewhere; (2) present each description to a "fresh agent" test — if any statement requires prior knowledge not present in the description, flag it. This two-layer approach catches both syntactic dependencies (noun phrases referencing undefined context) and semantic dependencies (assumptions that only make sense with prior knowledge).
- **Current approach**: Concrete self-containment checklist: (a) goal statement, (b) specific actions, (c) acceptance criteria, (d) no undefined references — every term is either defined within the description or includes a pointer to its definition in code or project documentation. See GAP-57 for the definitive checklist item (d) wording.

### GAP-34: dependency-mapping:3.4 tests author capability not system output
- **Severity**: medium
- **Description**: dependency-mapping:3.4 states "the author SHALL be able to identify every blocking relationship" and "the author SHALL be able to verify which tasks are parallel-eligible" — these describe author capability rather than the skill's observable behavior or output. Requirements should specify what the skill produces that enables these capabilities, not the author's ability to use it. Similar to GAP-6 (resolved), which changed "can" to "SHALL be able to" — GAP-6's resolution created this pattern of capability-focused language.
- **Category**: resolved
- **Decision**: Merge dependency-mapping:3.4 into Rule 4 (author confirmation). Remove scenario 3.4 entirely. Ensure Rule 4 scenarios cover the complex graph case (fan-out + fan-in combined) — the existing 4.1 scenario already requires presenting "every task and its blocking relationships" and distinguishing "serial chains from parallel groups." The complex-graph review is a natural fit for Rule 4's confirmation flow rather than Rule 3's encoding guidance. [Note: dependency-mapping:3.4 was subsequently reused for the cycle detection scenario added by GAP-36. The "remove scenario 3.4 entirely" instruction referred to the old capability-focused scenario, not the current cycle detection scenario.]

### GAP-35: Cycle detection algorithm unspecified
- **Severity**: medium
- **Description**: CMP-final-validation specifies cycle detection as a responsibility but provides no algorithm, complexity bounds, or output format for detected cycles. When a cycle is found, it's unclear whether the validation reports the minimal cycle, all cycles, or just signals that a cycle exists. The mechanism for identifying which tasks participate in the cycle is undefined.
- **Category**: resolved
- **Decision**: Prescribe topological sort for cycle detection. Perform a topological sort on the dependency graph — if the sort does not consume all nodes, the unconsumed nodes are involved in cycle(s). Report the set of unconsumed task IDs and labels. O(V+E) complexity, deterministic. Does not report exact cycle paths, but for small author-created workflows the involved-node set is sufficient to identify and fix the issue.

### GAP-36: No scenario for dependency cycle detection during dependency mapping phase
- **Severity**: medium
- **Description**: Cycles are only caught at final validation (workflow-validation:2.2), wasting the description-writing phase if a cycle is introduced during dependency mapping. If CMP-dependency-map produces a cycle, the author continues through CMP-descriptions and CMP-skill-md before discovering the issue at CMP-final-validation. Early detection would prevent wasted effort on tasks that will fail validation.
- **Category**: resolved
- **Decision**: Add cycle detection to CMP-dependency-map's existing validation responsibility. CMP-dependency-map already validates "all dependency references point to existing tasks" — add "no circular dependencies exist" to the same validation step using topological sort (consistent with GAP-35). Add a requirement scenario to dependency-mapping for early cycle detection. CMP-final-validation retains its cycle check as a final safety net.

### GAP-37: No scenario for empty/no input to intake path
- **Severity**: medium
- **Description**: No scenario covers an author selecting an intake path but providing no meaningful input (e.g., selecting brainstorming intake but declining to provide ideas, or selecting existing-skill intake but providing no workflow material). The skill's behavior when the intake phase yields nothing to normalize is unspecified.
- **Category**: superseded
- **Superseded by**: GAP-88
- **Decision**: When an intake path (existing-skill or written-steps) yields no meaningful input, the skill suggests falling back to the brainstorming intake path to help the author generate ideas from scratch. This provides cross-path recovery rather than simply blocking — the author gets guided support instead of a dead end. Add a scenario covering the fallback behavior.
- **Current approach**: GAP-88 eliminated the fallback mechanism. Brainstorming now always runs sequentially after input-based intakes, filling gaps with awareness of what intakes already contributed. No cross-path fallback exists; brainstorming is a mandatory sequential step.

### GAP-31: Progressive fsm.json construction threshold undefined
- **Severity**: low
- **Description**: technical.md states progressive fsm.json construction "may" be needed when "full conversation history may approach context limits" but provides no threshold, heuristic, or trigger for when the author should switch from default conversation-context state passing to the progressive construction approach. The condition under which this optimization applies is undefined.
- **Category**: resolved
- **Decision**: Make progressive construction the default approach, eliminating the threshold question entirely. Instead of "conversation context is the primary state-passing mechanism with progressive construction as an optimization," progressive construction (building all task stubs first, then iteratively adding fields) becomes the standard workflow. Remove the conditional framing from State Management.

### GAP-38: "Well-known external concept" in self-containment audit undefined
- **Severity**: medium
- **Description**: CMP-final-validation's self-containment audit (GAP-33 resolution) accepts noun phrases that refer to a "well-known external concept" but this term is undefined. Without criteria for what qualifies as "well-known" vs requiring explicit definition within the description, the audit's false-positive and false-negative rates are unpredictable. For example, is "REST API" well-known? Is "blockedBy array"? The boundary is unspecified.
- **Category**: superseded
- **Superseded by**: GAP-53 → GAP-57
- **Decision**: Remove the noun-phrase extraction layer from the self-containment audit. Rely solely on the "fresh agent" test — if a fresh agent with no prior knowledge of this workflow can execute the description, all references are sufficiently clear. This eliminates the subjective "well-known" boundary by replacing it with a single pragmatic test: can the description stand alone?
- **Current approach**: Concrete self-containment checklist replaces the "fresh agent" test. Checklist item (d): "no undefined references — every term is either defined within the description or includes a pointer to its definition in code or project documentation." See GAP-57 for the definitive wording.

### GAP-39: No guard for dual intake path output
- **Severity**: low
- **Description**: CMP-normalize collects "whatever workflow material exists" path-agnostically, but no guard or validation detects the condition where the agent mistakenly performs two intake paths (e.g., both existing-skill and brainstorming) producing duplicate or conflicting step lists. The normalize component would silently merge or choose between them with no defined behavior.
- **Category**: superseded
- **Superseded by**: GAP-44
- **Decision**: Accept risk as negligible. Each intake task has explicit applicability criteria and requires author confirmation before proceeding. Dual execution would require the agent to fail applicability checks on two tasks simultaneously AND have the author confirm both. The existing design provides sufficient guard through the applicability criteria + author confirmation gate.
- **Current approach**: Intake paths are non-exclusive sources (GAP-44); dual intake is intended behavior, not a mistake. Each intake task contributes whatever material applies; CMP-normalize concatenates all contributions. The concern no longer applies.

### GAP-40: Structural integrity check only lists 3 of 5 core fields
- **Severity**: medium
- **Description**: CMP-final-validation structural integrity check lists required fields as "id, subject, description" but CMP-fsm-json defines 5 core fields including activeForm and blockedBy. The structural integrity check at final validation does not verify the presence of activeForm or blockedBy, creating a gap where these fields could be missing from generated output without being caught.
- **Category**: resolved
- **Decision**: Update CMP-final-validation's structural integrity check to include all 5 core fields: id, subject, description, activeForm, blockedBy. The required field list should match CMP-fsm-json's output specification.

### GAP-41: Brainstorming has no fallback when it yields no output
- **Severity**: low
- **Description**: GAP-37's resolution adds fallback from existing-skill and written-steps intake paths to brainstorming when they yield no output. However, brainstorming is the terminal fallback — no behavior is specified for when brainstorming itself yields no usable output (e.g., author declines to provide any ideas). The skill's behavior at this terminal dead-end is undefined.
- **Category**: superseded
- **Superseded by**: GAP-100
- **Decision**: Graceful exit. If brainstorming yields no usable steps after the author declines to provide ideas, the skill acknowledges the author isn't ready to define a workflow and suggests returning later. The workflow terminates cleanly rather than looping indefinitely.
- **Current approach**: GAP-100 restates this concern without the fallback framing that was eliminated by GAP-88. The graceful exit decision remains current.

### GAP-42: activeForm scenario misplaced under wrong Rule
- **Severity**: low
- **Description**: Scenario @self-contained-descriptions:2.4 (activeForm generation from task label) is placed under Rule 2 (no inter-task references) but is unrelated to inter-task references. activeForm generation is a distinct concern from self-containment. The scenario's placement under Rule 2 creates confusion about whether activeForm generation has a self-containment dimension or is simply miscategorized.
- **Category**: resolved
- **Decision**: Move @self-contained-descriptions:2.4 to a new Rule 4 under self-contained-descriptions: "The skill SHALL auto-generate activeForm from task labels." Renumber the scenario as @self-contained-descriptions:4.1. This separates the activeForm generation concern from the inter-task reference concern.

### GAP-24: Decision 5 rationale incomplete
- **Severity**: low
- **Description**: Decision 5 (self-contained format specs repeated in each consuming task) provides the trade-off analysis but the rationale could be strengthened with a concrete example showing what breaks if format specs are NOT repeated. Source: Design DECISION-1.
- **Category**: resolved
- **Decision**: Extend the parenthetical in Decision 5's Y-statement: change "(which would violate self-containment since descriptions must stand alone after compaction)" to "(which would violate self-containment since descriptions must stand alone after compaction — without the repeated format spec, the agent would have no field definitions to follow)."

### GAP-44: Intake path evaluation criteria for multi-match input undefined
- **Severity**: medium
- **Description**: The technical design specifies that "the agent evaluates each [intake path], performs the one that applies, and marks the other two complete" (per GAP-1 resolution, with author confirmation). However, no evaluation criteria define what makes an intake path "apply." When author input could plausibly match multiple paths (e.g., an existing skill description that also contains brainstorming-style notes), the agent has no specified basis for proposing one path over another. GAP-1 (resolved) added author confirmation but did not define the evaluation signal that drives the initial proposal. Source: Design critic.
- **Category**: superseded
- **Superseded by**: GAP-88
- **Decision**: Reframe intake paths as non-exclusive sources. The three intake sources are not mutually exclusive — author input may span multiple sources (e.g., an existing skill plus brainstormed additions). The agent and author combine inputs through discussion. CMP-normalize collects from all sources contributed during intake. Remove the "pick one path" framing from intake task applicability.
- **Current approach**: GAP-88 reclassified brainstorming from a parallel intake source to a sequential gap-filling step. Current architecture has two input-based intake sources (existing skill, written steps) that fan into brainstorming, which fills gaps with awareness of prior contributions, then normalize. The "three intake sources" framing no longer applies.

### GAP-46: Progressive construction timing conflicts with parallel SKILL.md and fsm.json generation
- **Severity**: medium
- **Description**: The State Management section defines progressive fsm.json construction as the default workflow (per GAP-31 resolution), where the fsm.json is built incrementally across phases. However, the task dependency graph shows CMP-skill-md and CMP-fsm-json as potentially parallel tasks (both depend on CMP-descriptions completing). If the fsm.json is progressively constructed throughout earlier phases, CMP-fsm-json's role becomes finalization rather than generation — but the component's responsibilities describe full generation ("Encode all tasks..."). The progressive construction model and the generation model are not reconciled. Source: Design critic.
- **Category**: resolved
- **Decision**: Redefine CMP-fsm-json as finalization. Since progressive construction builds the fsm.json incrementally across earlier phases, CMP-fsm-json's role is finalization — validating, formatting, and writing the final artifact — not full generation. Update CMP-fsm-json responsibilities to reflect finalization role. Reconciles progressive construction with dependency graph.

### GAP-47: Weak normative language "will" in workflow-intake:1.1
- **Severity**: high
- **Description**: Scenario @workflow-intake:1.1, line 24 uses weak normative language: "And the guidance explains how `<source_material>` will be transformed into workflow steps." The word "will" indicates future prediction rather than a normative requirement. Requirements SHALL use MUST/SHALL for mandatory behavior per MDG conventions. Prior normative fixes addressed "can" (GAP-6) and "should" (GAP-16) but not "will." Change "will be transformed" to "SHALL be transformed" or rephrase to "And the guidance explains how to transform `<source_material>` into workflow steps." Source: Requirements critic.
- **Category**: resolved
- **Decision**: Rephrase to active voice: change "And the guidance explains how `<source_material>` will be transformed into workflow steps" to "And the guidance explains how to transform `<source_material>` into workflow steps." Removes future tense, uses active voice.

### GAP-48: No scenario for author modifying previously approved task descriptions
- **Severity**: medium
- **Description**: The self-contained-descriptions capability covers initial description authoring (Rules 1-3) and activeForm generation (Rule 4), but no scenario addresses the author returning to modify an already-approved description. Other capabilities include explicit modify-after-review scenarios (dependency-mapping:4.2, workflow-intake:2.4, 4.4), but self-contained-descriptions has no equivalent. Authors frequently revisit earlier descriptions while writing later ones (e.g., discovering shared preconditions that must be inlined differently). The skill's behavior for iterating on previously completed descriptions is unspecified. Source: Coverage critic.
- **Category**: resolved
- **Decision**: Add a modify-after-review scenario to self-contained-descriptions, consistent with other capabilities' patterns. Author can return to revise an approved description during the description writing phase. Re-validation applies to the modified description.

### GAP-49: No scenario for final validation self-containment failure requiring cross-phase correction
- **Severity**: medium
- **Description**: workflow-validation:2.1 covers the self-containment check and 2.4 covers reporting issues, but no scenario addresses the correction loop when final validation fails on a self-containment issue specifically. Unlike intra-phase corrections (covered by 1.6, per GAP-10 resolution), fixing a self-containment failure may require the author to re-enter the description writing phase for one or more tasks — the correction is not a simple in-place fix. The skill's behavior when final validation failures require returning to a previous phase's artifacts has no scenario. Source: Coverage critic.
- **Category**: resolved
- **Decision**: In-place correction during final validation. When final validation detects a self-containment issue, the author edits the description directly within the final validation task. No phase regression needed — the correction and re-validation happen in-place, consistent with GAP-10's intra-task correction loop pattern.

### GAP-50: No scenario for skill name or plugin name validation
- **Severity**: medium
- **Description**: skill-file-generation:1.1 and 4.1 reference the author specifying a plugin name and skill name, which flow into directory paths (`plugins/<plugin>/skills/<skill>/`) and metadata (`{"fsm": "skill-name"}`). No scenario covers invalid names — names with spaces, special characters, empty strings, or names conflicting with existing skills/plugins. Authors commonly provide display-friendly names ("My Cool Skill") rather than directory-safe names ("my-cool-skill"), and the skill's behavior for normalizing or rejecting such input is unspecified. Source: Coverage critic.
- **Category**: resolved
- **Decision**: Auto-normalize with author confirmation. Skill converts display-friendly names to directory-safe format (lowercase, hyphens, no special chars) and presents the normalized name to the author for confirmation. Consistent with the "skill proposes, author confirms" pattern used throughout.

### GAP-51: No requirement scenario for structural validation at final validation
- **Severity**: medium
- **Description**: GAP-40 (resolved) updated CMP-final-validation's structural integrity check to include all 5 core fields (id, subject, description, activeForm, blockedBy). However, no requirement scenario in workflow-validation covers this structural check at final validation time. skill-file-generation:3.3 specifies required fields during generation, but generation correctness and validation correctness are separate concerns. A requirement scenario verifying the final validation catches missing or malformed fields in the generated task definition would close this gap. Source: Coverage critic.
- **Category**: resolved
- **Decision**: Add both passing and failing scenarios. Add @workflow-validation:2.6 (all 5 core fields + metadata present, structural check passes) and @workflow-validation:2.7 (field missing, reports specific missing field). Consistent with Rule 1's pass/fail pattern.

### GAP-52: No test data management strategy for complex requirement scenarios
- **Severity**: high
- **Description**: The requirements define scenarios covering complex authoring behaviors (vague descriptions, overlapping ideas, implicit ordering assumptions), but infra.md provides no guidance on test data construction. For example, workflow-intake:3.2 requires "descriptions that do not specify what work is performed" as verification input, but no canonical examples are provided. Similarly, self-contained-descriptions:2.3 requires "implicit ordering assumptions" — these demand carefully constructed test inputs. Manual verification without standardized test data will produce inconsistent results across different verification attempts. Source: Design for Test critic.
- **Category**: resolved
- **Decision**: Add a "Verification Examples" section to infra.md with boundary examples for key scenario categories. Define what makes inputs "vague," "implicit ordering," etc. with concrete pass/fail boundary examples. Keeps test guidance co-located with the test strategy.

### GAP-53: No infrastructure for "fresh agent" self-containment audit
- **Severity**: high
- **Description**: CMP-final-validation (per GAP-33/38 resolutions) relies on a "fresh agent" test: "present each description to a fresh agent with no prior knowledge of the workflow" and verify it can execute independently. However, infra.md provides no mechanism for: (1) isolating a description from the conversation history that generated it, (2) presenting it to an agent instance with no workflow knowledge, (3) verifying whether the agent has sufficient context. Without this infrastructure, the fresh agent test in workflow-validation:2.1 and self-contained-descriptions requirements cannot be executed systematically. Source: Design for Test critic.
- **Category**: superseded
- **Superseded by**: GAP-57
- **Decision**: Replace "fresh agent" test with a concrete self-containment checklist. Each description must contain: (a) goal statement — what the task accomplishes, (b) specific actions — what the agent should do, (c) acceptance criteria — how to know when done, (d) no undefined references — every noun phrase is either defined in the description or is a well-known concept. Systematic, repeatable, no special tooling needed. Update infra.md and technical.md (CMP-final-validation) accordingly.
- **Current approach**: GAP-57 replaced checklist item (d) wording across all spec locations. Current item (d): "no undefined references — every term is either defined within the description or includes a pointer to its definition in code or project documentation." The "well-known concept" boundary was removed.

### GAP-54: Topological sort verification mechanism undefined in test infrastructure
- **Severity**: medium
- **Description**: Requirement workflow-validation:2.2 specifies cycle detection using topological sort and reporting "unconsumed task IDs and labels" (per GAP-35 resolution). infra.md does not specify how to verify the topological sort was performed correctly or that reported cycle participants are accurate. `validate_fsm_tasks` performs field presence checks, not graph algorithms. There is no test infrastructure for verifying dependency graph analysis correctness. Source: Design for Test critic.
- **Category**: resolved
- **Decision**: Specify Kahn's algorithm as the cycle detection implementation and add test cases with expected outputs to infra.md. Provide example dependency graphs: (1) acyclic graph — should pass, (2) single cycle (A-B-C-A) — report nodes A, B, C, (3) multi-cycle with shared node. Concrete verification targets for manual testing.

### GAP-55: Author confirmation gate blocking behavior untestable
- **Severity**: medium
- **Description**: Multiple requirements specify author confirmation gates where "the skill does not proceed until the author approves" (workflow-intake:2.3, 4.3, dependency-mapping:4.3). GAP-22 (resolved) specifies AskUserQuestion as the mechanism. However, infra.md's uniform "Manual: invoke skill, verify X" approach provides no guidance on systematically testing that progression blocks on rejection and advances on approval. The test environment lacks tooling to simulate author approval/rejection responses and verify blocking behavior enforcement. Source: Design for Test critic.
- **Category**: resolved
- **Decision**: Document AskUserQuestion as self-verifying in infra.md. The AskUserQuestion mechanism is inherently blocking — the skill literally cannot proceed without a user response. The blocking behavior is guaranteed by construction, not by testing. Add a rationale note to infra.md explaining this verification-by-design approach.

### GAP-56: Missing negative test data for prohibited term detection
- **Severity**: medium
- **Description**: Requirement skill-file-generation:2.1 is a Scenario Outline with 8 prohibited terms from SPEC-prohibited-terms (per GAP-13 resolution), but infra.md provides no test SKILL.md examples containing these terms for negative testing. The manual verification approach "verify generated SKILL.md contains none of the prohibited terms" only tests the positive case (clean output). It does not verify the skill would catch a SKILL.md that accidentally included "fsm.json" or "task directory." Without negative test cases and verification tooling, the detection requirement cannot be systematically verified. Source: Design for Test critic.
- **Category**: superseded
- **Superseded by**: GAP-120
- **Decision**: Add a verification protocol to infra.md: for each prohibited term in SPEC-prohibited-terms, the verifier inserts the term into the generated SKILL.md, re-runs the prohibited term scan, and confirms the term is detected and flagged. Systematic negative testing without pre-built fixtures.
- **Current approach**: GAP-120 removed the prohibited term verification protocol from infra.md. SKILL.md quality relies on author judgment rather than automated term scanning.

### GAP-57: "Well-known concept" boundary reintroduced despite GAP-38 resolution
- **Severity**: medium
- **Description**: GAP-38 (resolved) removed the "well-known external concept" boundary from the self-containment audit because the term was undefined and created unpredictable audit results. The resolution replaced it with a "fresh agent" test. GAP-53 (resolved) then replaced the "fresh agent" test with a concrete self-containment checklist, but checklist item (d) reintroduces the exact phrase: "every noun phrase is either defined in the description or is a well-known concept." This language appears in three locations — technical.md CMP-final-validation responsibilities, infra.md self-containment checklist verification examples, and workflow-validation:2.1 scenario — all using the undefined "well-known concept" boundary that GAP-38 identified as problematic. The infra.md examples (e.g., "PostgreSQL" as well-known) partially mitigate the ambiguity but do not define the boundary criteria. Source: Documentation gap analysis.
- **Category**: resolved
- **Decision**: Replaced "well-known concept" with concrete, verifiable language across all three locations. Checklist item (d) now reads: "no undefined references — every term is either defined within the description or includes a pointer to its definition in code or project documentation." Updated in technical.md (CMP-final-validation), infra.md (verification examples), and workflow-validation:2.1 (requirement scenario).

### GAP-58: Verification example uses unresolved "Borderline" verdict
- **Severity**: low
- **Description**: The "Overly broad descriptions" verification example table in infra.md includes the example "Validate the input, transform the data, and write the output" with a "Borderline" verdict and reasoning "depends on whether each is independently testable." Verification examples are intended to define what qualifies as pass or fail for consistent manual verification across attempts (per infra.md preamble). A "Borderline" verdict with a conditional "depends on" clause does not provide a deterministic pass/fail boundary — the verifier must make a subjective judgment about independent testability without criteria for that judgment. This undermines the stated purpose of the verification examples section. Source: Documentation gap analysis.
- **Category**: resolved
- **Decision**: Changed "Borderline" verdict to "Fail — too broad" with specific reasoning: three distinct operations (validate, transform, write) that are independently testable and have separate failure modes. Verification examples must provide deterministic pass/fail boundaries, not conditional judgments.

### GAP-61: CMP-normalize does not specify multi-source conflict handling
- **Severity**: low
- **Description**: GAP-44 (resolved) reframed intake paths as non-exclusive sources where author input may span multiple sources. CMP-normalize "collects whatever workflow material exists" path-agnostically. However, no specification exists for how CMP-normalize handles duplicate or conflicting steps when combining material from multiple sources (e.g., an existing skill contributes step "Validate config" and brainstorming also produces "Validate configuration" — are these merged, flagged as duplicates, or both kept?). The normalize component's conflict resolution behavior is undefined. Source: Design critic.
- **Category**: resolved
- **Decision**: CMP-normalize concatenates all contributions from all intake sources and presents the combined list to the author during the existing confirmation gate. No automatic deduplication — the author resolves duplicates/conflicts during the confirmation step. Similar labels may serve different purposes, so human judgment is appropriate.

### GAP-62: Weak normative "will" in self-contained-descriptions:1.3
- **Severity**: medium
- **Description**: Scenario @self-contained-descriptions:1.3 uses weak normative language: "the original skill text will not be available after context compaction." The word "will" indicates future prediction rather than a normative requirement. GAP-47 (resolved) fixed the same class of issue in workflow-intake:1.1 but did not sweep for other instances. Requirements SHALL use normative language per MDG conventions. Source: Requirements critic.
- **Category**: resolved
- **Decision**: Rephrase to active voice consistent with GAP-47's resolution pattern: change "the original skill text will not be available after context compaction" to "context compaction removes the original skill text."

### GAP-63: No scenario for combining material from multiple intake sources
- **Severity**: medium
- **Description**: GAP-44 (resolved) explicitly reframed intake paths as non-exclusive sources where "author input may span multiple sources (e.g., an existing skill plus brainstormed additions)." However, no requirement scenario tests the combined-source workflow. All intake scenarios assume a single source type. There is no scenario verifying that CMP-normalize correctly combines material from two or more intake sources, that the author can review the combined step list, or that the merged output is coherent. The non-exclusive framing was added as a design decision but lacks requirements-level verification. Source: Coverage critic.
- **Category**: resolved
- **Decision**: Add one scenario to workflow-intake Rule 1 covering the multi-source case: author provides material spanning two sources, CMP-normalize combines them, author reviews the merged step list.

### GAP-64: No failure scenario for description writing phase validation gate
- **Severity**: medium
- **Description**: workflow-validation Rule 1 specifies incremental validation at each phase. Scenarios 1.4 and 1.5 cover specific failure cases for intake and dependency mapping phases respectively, but no scenario covers a specific failure case for the description writing phase. Scenario 1.3 specifies what the skill checks (non-empty, non-placeholder) but 1.6 only covers generic "author corrects and re-validates." The asymmetry means the description phase validation failure path lacks a concrete example of what triggers it and how it's reported. Source: Coverage critic.
- **Category**: resolved
- **Decision**: Add a failure scenario for the description writing phase: a task description contains only placeholder text (e.g., "TODO: write this later"), the skill catches it as non-substantive content, reports the specific task, and blocks progression until the author writes a real description.

### GAP-65: "No meaningful workflow material" threshold undefined
- **Severity**: medium
- **Description**: The intake fallback scenario specifies fallback behavior when an intake path "yields no meaningful workflow material," and GAP-37 (resolved) added this fallback. However, "no meaningful workflow material" is not defined — no threshold, heuristic, or criteria distinguish "no meaningful material" from "some but insufficient material." For example, if an author provides a single ambiguous sentence, does this count as "no meaningful material" (triggering fallback) or "vague material" (triggering clarification prompts)? The boundary between the two behaviors is unspecified. Source: Verification critic.
- **Category**: superseded
- **Superseded by**: GAP-88
- **Decision**: Define "no meaningful workflow material" as zero extractable steps after the intake process completes. Binary threshold: zero steps → suggest fallback to brainstorming; any steps (even vague ones) → use the clarification path (workflow-intake:3.2). This creates a clean boundary between emptiness (fallback) and vagueness (clarification).
- **Current approach**: GAP-88 made brainstorming always run sequentially after input-based intakes. When zero steps exist from prior intakes, brainstorming generates from scratch. The "suggest fallback" mechanism was replaced by mandatory sequential execution; the zero-step threshold now determines brainstorming's starting point (from scratch vs. gap-filling) rather than triggering a fallback.

### GAP-66: "Overly small" task description threshold undefined
- **Severity**: medium
- **Description**: self-contained-descriptions:3.2 specifies that the skill "prompts the author to consider merging" overly small descriptions, but no definition, threshold, or verification examples exist for what constitutes "overly small." GAP-52 (resolved) added verification examples to infra.md for vague descriptions, implicit ordering, overly broad descriptions, and external references — but not for overly small descriptions. The "Overly broad descriptions" section defines a clear boundary (multiple distinct objectives/deliverables), but the inverse boundary for "overly small" is missing. Source: Verification critic.
- **Category**: resolved
- **Decision**: Define "overly small" through self-containment checklist alignment. A description is "overly small" if it cannot meaningfully populate all 4 self-containment checklist items (goal statement, specific actions, acceptance criteria, no undefined references). If the checklist items become trivially redundant for a task, that task should be considered for merging with a related task.

### GAP-69: Prohibited term scan algorithm unspecified
- **Severity**: medium
- **Description**: SPEC-prohibited-terms (GAP-13 resolved) defines the canonical term list, and GAP-56 (resolved) added a verification protocol for testing detection. However, neither specifies the scanning algorithm — string matching, regex, case-sensitive or case-insensitive. Variations like "FSM.json" vs "fsm.json," "hydration-pipeline" vs "hydration," or "task_file" vs "task file" may or may not be caught depending on the implementation. The verification protocol tests that each exact term is detected but does not cover case or format variations. Source: Design for Test critic.
- **Category**: superseded
- **Superseded by**: GAP-120
- **Decision**: Specify case-insensitive substring matching as the scanning algorithm. This catches variations like "FSM.json" and "hydration-pipeline." The curated term list minimizes false positives. Manual verification per the GAP-56 protocol catches edge cases.
- **Current approach**: GAP-120 removed SPEC-prohibited-terms and all associated scanning. No scanning algorithm specification is needed.

### GAP-70: Structural validation lacks field type verification
- **Severity**: medium
- **Description**: The structural validation scenarios (workflow-validation:2.6-2.7) and GAP-40 (resolved) specify checking for field presence of all 5 core fields plus metadata. However, no specification addresses field type validation. If `blockedBy` is present but is a string instead of an array, or if `id` is a string instead of a number, the structural check's behavior is undefined. Field presence and field type correctness are separate concerns — presence checking alone cannot catch type errors. Source: Design for Test critic.
- **Category**: resolved
- **Decision**: Add explicit field type expectations to the structural integrity check: `id` (integer), `subject` (string), `description` (string), `activeForm` (string), `blockedBy` (array of integers), `metadata` (object with `fsm` key).

### GAP-71: activeForm format verification has no test cases
- **Severity**: low
- **Description**: self-contained-descriptions:4.1 specifies that the skill generates activeForm in "present-continuous form" from task labels. GAP-52 (resolved) added verification examples for other scenario categories but not for activeForm transformation. Edge cases like labels already in continuous form ("Running tests"), past-tense labels ("Validated schema"), or non-verb labels ("Configuration") have no specified expected outputs. Without boundary examples, verifiers cannot consistently assess whether the skill's activeForm generation is correct. Source: Design for Test critic.
- **Category**: resolved
- **Decision**: Add activeForm verification examples to infra.md with boundary cases: "Validate dependencies" → "Validating dependencies" (standard), "Running tests" → keep as-is (already continuous), "Configuration setup" → "Setting up configuration" (non-verb label). Author override per self-contained-descriptions:4.1 handles remaining edge cases.

### GAP-72: Metadata content validation missing
- **Severity**: low
- **Description**: skill-file-generation:3.3 requires each task entry to contain `metadata` with the skill name, and GAP-11/21 (resolved) specify the format as `{"fsm": "skill-name"}`. However, structural validation (workflow-validation:2.6) only verifies metadata field presence, not content correctness. If metadata is present but malformed (e.g., `{"fsm": ""}`, `{"wrong-key": "skill-name"}`, or `{}`), validation would pass. Source: Design for Test critic.
- **Category**: resolved
- **Decision**: Extend CMP-final-validation's structural integrity check to verify metadata content: metadata must be an object containing an `fsm` key with a non-empty string value matching the skill name.

### GAP-74: Self-containment checks deferred entirely to final validation
- **Severity**: medium
- **Description**: The validation scope table (GAP-15 resolution) intentionally places self-containment auditing at CMP-final-validation as a "cross-cutting concern." CMP-descriptions only validates "non-empty, non-placeholder" descriptions. This means descriptions can pass the descriptions phase with content that has a goal statement but lacks specific actions, acceptance criteria, or contains undefined references — then fail at final validation. The incremental validation promise (OBJ-incremental-validation) is weakened because the most critical quality dimension (self-containment) provides no feedback until the end of the workflow. Authors may write all descriptions before discovering systemic self-containment issues. Source: Logic critic.
- **Category**: resolved
- **Decision**: Add the self-containment checklist as a per-description check in CMP-descriptions — when each description is drafted/approved, run the 4-item checklist (goal statement, specific actions, acceptance criteria, no undefined references). Retain the full audit at CMP-final-validation as a cross-cutting safety net. This gives authors immediate feedback on each description without losing the final cross-cutting check.

### GAP-75: Progressive construction timing contradicts parallel CMP-skill-md/CMP-fsm-json execution
- **Severity**: high
- **Description**: The State Management section defines progressive fsm.json construction as the default workflow where "the skill builds all task stubs first, then iteratively adds fields across all tasks as each phase completes." GAP-46 (resolved) redefined CMP-fsm-json as finalization. However, the task dependency graph still shows CMP-skill-md and CMP-fsm-json as parallel tasks after CMP-descriptions. If fsm.json is progressively built throughout earlier phases, it already exists before CMP-fsm-json starts — making CMP-fsm-json purely a finalization step. But CMP-skill-md (which runs in parallel) may need to reference fsm.json content for consistency. The technical design does not specify whether CMP-skill-md has access to the progressively-built fsm.json or operates independently. Source: Logic critic.
- **Category**: superseded
- **Superseded by**: GAP-88, GAP-120
- **Decision**: Restructure the dependency graph. CMP-skill-md branches off CMP-normalize (not CMP-descriptions) — it only needs the normalized step list to write author-facing documentation about broad workflow concepts. CMP-skill-md self-validates (prohibited terms, frontmatter) and completes independently. The main chain becomes linear: DM → DE → FJ → FV. CMP-final-validation fans in from CMP-fsm-json only. New graph: `(IE|IW|IB) → N → SM | (DM → DE → FJ → FV)`. This eliminates the timing contradiction: SM doesn't need the progressively-built fsm.json, and the progressive chain is purely linear.
- **Current approach**: GAP-88 restructured the dependency graph to (IE|IW) → IB → N → SM | (DM → DE → FJ → FV). GAP-120 removed prohibited terms from CMP-skill-md self-validation, which now covers frontmatter only.

### GAP-76: Intake component descriptions still use singular path language
- **Severity**: medium
- **Description**: GAP-44 (resolved) reframed intake paths as non-exclusive sources, but the three intake component descriptions (CMP-intake-existing, CMP-intake-written, CMP-intake-brainstorm) each still specify "Evaluate the author's input against applicability criteria; propose this intake path applies and get author confirmation before proceeding." The singular "propose this intake path applies" language implies mutual exclusivity — only one path is proposed as applying. This contradicts the non-exclusive framing where multiple sources may contribute simultaneously. The component text was not updated to reflect the GAP-44 resolution. Source: Logic critic.
- **Category**: resolved
- **Decision**: Update each intake component's text to contribution-based language: "Evaluate whether the author's input includes material for this source; if so, contribute applicable material and get author confirmation." This directly aligns with GAP-44's non-exclusive framing — each task evaluates whether it has something to contribute, not whether it's the selected path.

### GAP-73: CMP-dependency-map cycle detection does not explicitly reference Kahn's algorithm
- **Severity**: low
- **Description**: GAP-35 (resolved) prescribes topological sort for cycle detection, and GAP-54 (resolved) specifies Kahn's algorithm with test cases. CMP-dependency-map's cycle detection (added per GAP-36 resolution) references "topological sort (consistent with CMP-final-validation's algorithm)" but does not explicitly name Kahn's algorithm. CMP-final-validation explicitly specifies Kahn's algorithm. The indirect reference creates a risk that an implementer could use a different topological sort variant at the dependency-mapping phase, producing different results than final validation. Source: Logic critic.
- **Category**: resolved
- **Decision**: Explicitly name Kahn's algorithm in CMP-dependency-map's cycle detection text, consistent with CMP-final-validation. Changed "using topological sort (consistent with CMP-final-validation's algorithm)" to "using Kahn's algorithm (BFS-based topological sort)." Both components now explicitly specify the same algorithm.

### GAP-77: Confirmation gate mechanics unclear for multi-input scenarios
- **Severity**: low
- **Description**: Each intake component specifies its own author confirmation gate, and CMP-normalize also has an author confirmation gate. Under the non-exclusive intake model (GAP-44 resolved), multiple intake tasks may contribute material. This creates potentially redundant confirmation points: each contributing intake task confirms its output independently, then CMP-normalize confirms the combined output again. The technical design does not specify whether this redundancy is intentional (multiple review opportunities) or whether confirmations should be consolidated. Source: Logic critic.
- **Category**: superseded
- **Superseded by**: GAP-76, GAP-61
- **Decision**: The contribution-based framing (GAP-76) transforms confirmation gates from path-selection approvals to per-source contribution approvals — each intake task confirms its own contribution. CMP-normalize concatenation (GAP-61) then confirms the merged output. This is an intentional multi-layer approval flow, not unclear mechanics.
- **Current approach**: Intake tasks use contribution-based language (GAP-76): "Evaluate whether the author's input includes material for this source; if so, contribute applicable material and get author confirmation." CMP-normalize concatenates all contributions without deduplication (GAP-61); author resolves duplicates during confirmation.

### GAP-78: No requirement scenario for structural validation field type mismatch
- **Severity**: low
- **Description**: GAP-70 (resolved) added explicit field type expectations to CMP-final-validation's structural integrity check (`id`: integer, `subject`: string, `description`: string, `activeForm`: string, `blockedBy`: array of integers, `metadata`: object with `fsm` key). However, workflow-validation:2.6 (passing) only tests field presence ("all 5 core fields... and metadata with the skill name"), and workflow-validation:2.7 (failing) only tests a missing field ("one task entry is missing a required field"). No requirement scenario covers a wrong-type failure (e.g., `blockedBy` is a string instead of an array). The infra.md coverage table expects "fail when field missing or wrong type with specific report" but the requirement scenarios only cover missing fields. Source: Gap cleanup — implicit gap detection.
- **Category**: resolved
- **Decision**: Add workflow-validation:2.8 scenario covering wrong-type failure: a task entry has a field with an incorrect type, structural validation fails, and the skill reports the specific task entry, field name, expected type, and actual type.

### GAP-43: skill-file-generation capability text references "underlying task file structure"
- **Severity**: low
- **Description**: The `skill-file-generation` capability description contains the phrase "without leaking knowledge of the underlying task file structure," which itself references an implementation detail ("task file structure") at the functional spec level. GAP-29 (resolved) addressed "SKILL.md + task definition pair" in the same capability but did not modify this phrase. The functional spec should describe the user concern (e.g., "without exposing how the workflow is stored") rather than naming the internal structure. Source: Functional critic.
- **Category**: resolved
- **Decision**: Acknowledge gap as acceptable for now, defer to future release. Deferral documented in functional.md Out of Scope: "Precision of internal terminology in capability descriptions (e.g., 'underlying task file structure' phrasing in skill-file-generation)."

### GAP-45: Data Transformation table does not specify normalize input consumption
- **Severity**: low
- **Description**: The Data Transformation table (added per GAP-3 resolution) documents output schemas for each component but does not specify how CMP-normalize consumes the intake output. The table shows what each component produces but not how the next component selects or filters from its input. For CMP-normalize specifically, the path-agnostic "collect whatever workflow material exists" instruction (per GAP-1/14 resolution) does not appear in the Data Transformation table's input specification. Source: Design critic.
- **Category**: resolved
- **Decision**: Acknowledge gap as acceptable for now, defer to future release. Deferral documented in technical.md Decision 6: "we decided to document output schemas only, accepting that input consumption is implicitly defined by component ordering."

### GAP-59: "Small author-created workflows" threshold undefined in cycle detection
- **Severity**: low
- **Description**: CMP-final-validation's cycle detection specification in technical.md states: "Does not report exact cycle paths; for small author-created workflows the involved-node set is sufficient to identify and fix the issue." The qualifier "small" is undefined — no threshold, heuristic, or upper bound is given for what constitutes a "small" workflow. This creates ambiguity about when the involved-node-set reporting approach becomes insufficient and whether the skill should handle larger workflows differently. The same language appears in the infra.md cycle detection test cases section. Source: Documentation gap analysis.
- **Category**: resolved
- **Decision**: Acknowledge gap as acceptable for now, defer to future release. Deferral documented in technical.md Risks section: the undefined "small" threshold is an accepted limitation — exact cycle path reporting can be added in a future release without changing the detection algorithm.

### GAP-60: Out of Scope item is a meta-comment about spec quality
- **Severity**: low
- **Description**: The Out of Scope section in functional.md includes "Precision of internal terminology in the functional specification that is not visible to users" — this is a meta-comment about the specification's own quality rather than a user-facing scoping decision. Out of Scope items should describe capabilities or behaviors that users might expect but are intentionally excluded. A statement about internal terminology precision is a spec-authoring concern, not something a user would expect the skill to deliver. Source: Functional critic.
- **Category**: resolved
- **Decision**: Acknowledge gap as acceptable for now, defer to future release. The Out of Scope item was subsequently refined to "Precision of internal terminology in capability descriptions (e.g., 'underlying task file structure' phrasing in skill-file-generation)" which is more specific than the original meta-comment. The refined wording is acceptable as-is.

### GAP-67: "Author-facing language" vs "internal identifiers" boundary undefined
- **Severity**: low
- **Description**: skill-file-generation:1.1 requires SKILL.md content to use "author-facing body language" and skill-file-generation:2.1 scans for prohibited terms. However, the boundary between acceptable "author-facing language" and prohibited "internal identifiers" is defined only by the explicit SPEC-prohibited-terms list. Terms not on the list but still implementation-leaking (e.g., "task stub," "hydration pipeline," "progressive construction") would pass the prohibited term scan. No criteria exist for evaluating new terms that may emerge during skill generation. Source: Verification critic.
- **Category**: superseded
- **Superseded by**: GAP-120
- **Decision**: Acknowledge gap as acceptable for now, defer to future release. Deferral documented in functional.md Out of Scope: "Formal boundary between 'author-facing language' and 'internal identifiers' beyond the explicit SPEC-prohibited-terms list."
- **Current approach**: GAP-120 removed the SPEC-prohibited-terms mechanism. The boundary between author-facing language and internal identifiers is no longer governed by a prohibited-terms list; SKILL.md content quality relies on author judgment.

### GAP-68: "Targeted questions" vs "generic questions" distinction unverifiable
- **Severity**: low
- **Description**: workflow-intake:4.2 specifies that the skill "asks targeted questions to help the author develop ideas into concrete workflow steps." The qualifier "targeted" implies questions should be specific to the author's input rather than generic brainstorming prompts, but no criteria distinguish targeted from generic questions. Without observable criteria, a verifier cannot determine whether the skill's brainstorming questions are appropriately targeted. Source: Verification critic.
- **Category**: resolved
- **Decision**: Acknowledge gap as acceptable for now, defer to future release. Deferral documented in functional.md Out of Scope: "Verifiable criteria distinguishing 'targeted questions' from 'generic questions' in brainstorming intake guidance."

### GAP-79: No scenario for fsm.json description prohibited term scan at final validation
- **Severity**: medium
- **Description**: CMP-final-validation's responsibilities include checking fsm.json task descriptions for SPEC-prohibited-terms, and the Validation Scope table lists this as a distinct check. However, workflow-validation:2.3 only covers SKILL.md prohibited terms. No requirement scenario verifies the parallel fsm.json description check.
- **Category**: superseded
- **Superseded by**: GAP-85
- **Decision**: Add workflow-validation:2.9 scenario specifically for fsm.json description prohibited term scan at CMP-final-validation. Symmetric with workflow-validation:2.3 (SKILL.md scan). One scenario per distinct validation check.
- **Current approach**: GAP-85 removed workflow-validation:2.3 (SKILL.md scanning belongs at CMP-skill-md). GAP-120 subsequently removed the entire SPEC-prohibited-terms mechanism including workflow-validation:2.9. Neither SKILL.md nor fsm.json description prohibited term scanning exists in current specs.

### GAP-80: No scenario for metadata content validation failure
- **Severity**: medium
- **Description**: Similar to GAP-72 (resolved), which added metadata content validation to CMP-final-validation, but no requirement scenario was added for the content-specific failure mode. Scenarios 2.6 (pass), 2.7 (missing field), 2.8 (wrong type) exist, but none covers semantically invalid metadata content (e.g., `{"fsm": ""}` or `{"wrong-key": "value"}`) — a distinct failure mode from missing field or wrong type.
- **Category**: resolved
- **Decision**: Add workflow-validation:2.10 scenario for metadata content validation failure — specifically the empty `fsm` value case (`{"fsm": ""}`). The wrong-key case (`{"wrong-key": "value"}`) is already covered by 2.7 (missing required field) since the `fsm` key itself is absent. Completes the failure-mode coverage: missing field (2.7), wrong type (2.8), wrong content (2.10).

### GAP-81: No scenario for CMP-skill-md self-validation failure and correction loop
- **Severity**: medium
- **Description**: CMP-skill-md self-validates (prohibited terms scan + frontmatter check) and completes independently per technical.md Decision 3. skill-file-generation:2.1 covers prohibited term correction during generation but with no explicit failure-then-correction scenario. Other capabilities have explicit failure-correction scenarios (workflow-validation:1.4, 1.5, 1.6). CMP-skill-md lacks an equivalent.
- **Category**: superseded
- **Superseded by**: GAP-120
- **Decision**: Add skill-file-generation:2.2 scenario for CMP-skill-md self-validation failure with correction-then-re-validation loop. Aligns with the workflow-validation:1.4-1.6 failure-correction pattern used by other capabilities.
- **Current approach**: GAP-120 removed SPEC-prohibited-terms from CMP-skill-md. Self-validation now covers frontmatter only. The skill-file-generation:2.2 scenario covers frontmatter self-validation failure, not prohibited term correction.

### GAP-82: No scenario for author removing a task during dependency mapping
- **Severity**: medium
- **Source**: coverage-critic
- **Description**: The intake phase produces a normalized step list that the author approves. The dependency mapping phase then encodes relationships between these steps. However, no scenario covers the author realizing during dependency mapping that a task should be removed entirely (not just reordered). The dependency mapping phase covers modifying dependency relationships, but removing a task node from the graph is a different operation — it changes the step list itself, not just the edges. If an author discovers during dependency mapping that a step is redundant, the skill's behavior for removing a step at this phase is unspecified.
- **Category**: resolved
- **Decision**: Add a dedicated Rule 5 to dependency-mapping for step list modifications (add, remove, rename tasks) during the dependency mapping phase, with separate scenarios for each operation. The step list is mutable during dependency mapping — the skill supports adding, removing, and renaming tasks with dependency graph updates and re-validation.
- **Outcome**: Added dependency-mapping Rule 5 with scenarios 5.1 (remove task), 5.2 (add task), 5.3 (rename task). Updated CMP-dependency-map responsibilities in technical.md to support step list modifications with graph updates and re-validation. Updated Validation Scope table with step list modification re-validation. Updated functional.md dependency-mapping capability description. Updated infra.md coverage table for Rule 5.

### GAP-83: No final validation scenario for blockedBy referential integrity
- **Severity**: medium
- **Source**: coverage-critic
- **Description**: The skill file generation phase specifies that dependencies are encoded using task IDs. The final generated task definition file could contain blockedBy values referencing non-existent task IDs. Incremental validation checks that no task references a dependency that does not exist in the step list during the dependency mapping phase, before IDs are assigned. Structural validation at final validation covers field presence and field type (related to resolved gaps GAP-40, GAP-70, GAP-78), but no final validation scenario explicitly verifies referential integrity of blockedBy values against actual task IDs in the generated output.
- **Category**: resolved
- **Decision**: Add workflow-validation:2.11 scenario for dangling blockedBy reference at final validation. A task entry's blockedBy contains an ID that does not correspond to any task in the generated output; final validation catches it and reports the specific task entry and the invalid reference. Symmetric with existing 2.7 (missing field), 2.8 (wrong type), 2.10 (empty metadata) failure-mode pattern.
- **Outcome**: Added workflow-validation:2.11 scenario for dangling blockedBy reference detection at final validation. Completes the structural validation failure-mode coverage: missing field (2.7), wrong type (2.8), wrong content (2.10), dangling reference (2.11). Updated infra.md coverage table for Rule 2 to include 2.11 verification.

### GAP-84: No scenario for existing skill intake when the skill contains conditional branching logic
- **Severity**: low
- **Source**: coverage-critic
- **Description**: The intake phase covers extracting sequential steps and identifying implicit parallelism. No scenario covers existing skills that contain conditional logic (if/else, conditional paths). The skill's behavior when source material contains conditional branching that cannot be directly represented as task dependencies is unspecified.
- **Category**: resolved
- **Decision**: Add a scenario to workflow-intake Rule 2 for conditional logic decomposition. When the existing skill contains conditional paths, the skill guides the author to decompose them — either as separate tasks with the condition stated in each description, or as a single task that handles both branches internally. The author chooses the decomposition strategy.
- **Outcome**: Added workflow-intake:2.5 scenario for conditional logic decomposition during existing skill intake. Updated CMP-intake-existing responsibilities in technical.md to include conditional logic guidance. Updated infra.md coverage table for workflow-intake Rule 2 to include conditional branching verification.

### GAP-85: workflow-validation:2.3 assigns SKILL.md prohibited term scan to CMP-final-validation, contradicting technical design
- **Severity**: medium
- **Source**: implicit-detection
- **Description**: Requirement scenario workflow-validation:2.3 states "Final validation checks SKILL.md for prohibited terms" and places this check at CMP-final-validation ("the skill is performing final validation"). However, the technical design explicitly excludes this check from CMP-final-validation. CMP-final-validation's description states: "SKILL.md validation (prohibited terms scan and frontmatter check) is handled by CMP-skill-md's self-validation and is not repeated here." The CMP-final-validation prohibited term scan responsibility says: "Check fsm.json task descriptions for SPEC-prohibited-terms. Flag any found. (SKILL.md prohibited term scanning is handled by CMP-skill-md's self-validation.)" The infra.md coverage table for Rule 2 also notes "(fsm.json descriptions only -- SKILL.md scanned by CMP-skill-md self-validation)." This creates a direct contradiction: an implementer following workflow-validation:2.3 would add SKILL.md scanning to CMP-final-validation, while an implementer following the technical design would not. The scenario should either be moved to skill-file-generation (where CMP-skill-md self-validation lives) or rewritten to reference CMP-skill-md's self-validation rather than CMP-final-validation.
- **Category**: superseded
- **Superseded by**: GAP-120
- **Decision**: Remove workflow-validation:2.3 entirely. The SKILL.md prohibited term check is already covered by skill-file-generation:2.1 (CMP-skill-md Scenario Outline for each prohibited term) and skill-file-generation:2.2 (correction loop). The fsm.json description prohibited term check is covered by workflow-validation:2.9. Scenario 2.3 is redundant and contradicts the technical design's explicit placement of SKILL.md scanning at CMP-skill-md, not CMP-final-validation.
- **Outcome**: Removed workflow-validation:2.3 scenario. SKILL.md prohibited term coverage remains at skill-file-generation:2.1-2.2 (CMP-skill-md self-validation). fsm.json description prohibited term coverage remains at workflow-validation:2.9 (CMP-final-validation).
- **Current approach**: GAP-120 removed SPEC-prohibited-terms entirely. skill-file-generation:2.1 was changed from prohibited term Scenario Outline to frontmatter self-validation. workflow-validation:2.9 was removed. SKILL.md quality relies on author judgment.

### GAP-86: GAP-1 Decision uses superseded single-path intake selection language
- **Severity**: low
- **Source**: stale-detection
- **Description**: GAP-1 (resolved) Decision describes a single-path-selection model ("Agent evaluates input and proposes which intake path applies; author confirms before work begins") that was explicitly replaced by GAP-44's resolution ("Reframe intake paths as non-exclusive sources... Remove the 'pick one path' framing from intake task applicability"). GAP-1 lacks a Superseded by annotation pointing to GAP-44, so a reader following GAP-1's Decision alone would implement single-path selection rather than the current non-exclusive multi-source model.
- **Category**: resolved
- **Decision**: Re-categorize GAP-1 in resolved.md as superseded by GAP-44. Add Current approach field pointing to the non-exclusive intake source model. Decision text stays immutable per managing-spec-gaps rules.
- **Outcome**: GAP-1 re-categorized from "resolved" to "superseded" with Superseded by: GAP-44 and Current approach field pointing to the non-exclusive intake source model defined in technical.md.

### GAP-87: Capability description exposes internal phase decomposition
- **Severity**: medium
- **Source**: functional-critic
- **Description**: The workflow-validation capability description in functional.md contains implementation leak language: "Skill authors can verify generated workflows at each phase (intake, dependency mapping, description writing — including self-containment feedback on each description as it is written)". The parenthetical exposes the internal phase decomposition to the functional spec level. Similar issue was addressed in GAP-27 (resolved) which rewrote the Scope section to remove this language, but the same language survived in the capability description.
- **Status**: resolved
- **Triage**: delegate
- **Decision**: Rewrite workflow-validation capability to remove internal phase names. Change to "Skill authors can verify generated workflows incrementally and through a comprehensive final check before deployment." Consistent with GAP-27's Scope rewrite pattern.
- **Outcome**: Rewrote workflow-validation capability description in functional.md. Changed "at each phase (intake, dependency mapping, description writing — including self-containment feedback on each description as it is written)" to "incrementally — including self-containment feedback on each description as it is written —". Internal phase names removed.

### GAP-89: Weak normative language in workflow-intake format consistency statement
- **Severity**: low
- **Source**: requirements-critic
- **Description**: The workflow-intake scenario for step list format consistency uses weak normative language ("is consistent") without SHALL. Prior normative fixes addressed "can" (GAP-6), "should" (GAP-16), and "will" (GAP-47, GAP-62) but not this instance.
- **Status**: resolved
- **Triage**: delegate
- **Decision**: Change "is consistent" to "SHALL be consistent" in the workflow-intake step list format scenario. Straightforward normative language fix consistent with GAP-6, GAP-16, GAP-47, GAP-62 pattern.
- **Outcome**: Changed "the step list format is consistent" to "the step list format SHALL be consistent" in workflow-intake:1.2.

### GAP-91: Weak "recommends" language in self-contained-descriptions splitting guidance
- **Severity**: medium
- **Source**: requirements-critic
- **Description**: The self-contained-descriptions scenario for overly large descriptions uses weak normative language ("recommends splitting") instead of SHALL. The skill must provide splitting guidance when descriptions are overly broad, not merely suggest it.
- **Status**: resolved
- **Triage**: delegate
- **Decision**: Change "recommends splitting the description into separate tasks, one per objective" to "SHALL flag the distinct objectives and provide splitting guidance, recommending separate tasks for each objective." Strengthens normative language while preserving the advisory nature of the specific split recommendation.
- **Outcome**: Changed "the skill flags the distinct objectives and recommends splitting" to "the skill SHALL flag the distinct objectives and provide splitting guidance, recommending separate tasks for each objective" in self-contained-descriptions:3.1.

### GAP-94: dependency-mapping scenario tests internal data structure rather than observable behavior
- **Severity**: medium
- **Source**: requirements-critic
- **Description**: The dependency-mapping scenario for blocking direction encoding tests internal data structure (adding to a `blockedBy` array) rather than observable behavior (how the blocking relationship is presented to the author). GAP-8 (resolved) intentionally added this scenario format, but the testability concern (observable behavior vs internal data structure) remains. Similar to GAP-34's pattern (resolved) but distinct scenario.
- **Status**: resolved
- **Triage**: delegate
- **Decision**: Rewrite dependency-mapping:1.3 to test observable behavior rather than internal data structure. Change "the skill adds 'setup' to the `blockedBy` array of task 'build'" to "the skill presents task 'build' as blocked by 'setup'" and "task 'setup' does not have 'build' in its `blockedBy` array" to "the skill does not present 'setup' as blocked by 'build'."
- **Outcome**: Rewrote dependency-mapping:1.3. Title changed to "Blocking direction presented correctly to the author." Then steps changed to use "presents task 'build' as blocked by 'setup'" / "does not present 'setup' as blocked by 'build'" — observable behavior language replacing internal data structure language.

### GAP-95: No verification guidance for relationship prompting with newly added tasks
- **Severity**: low
- **Source**: verification-critic
- **Description**: The dependency-mapping scenario for adding tasks during dependency mapping (added by GAP-82 resolution) lacks verification guidance for what constitutes correct "relationship prompting" for a newly added task.
- **Status**: resolved
- **Triage**: delegate
- **Decision**: Add verification guidance to infra.md coverage table for dependency-mapping Rule 5: "Manual: during dependency mapping, add a task and verify the skill prompts for blocking relationships with all existing tasks (predecessors and successors)."
- **Outcome**: Updated infra.md dependency-mapping Rule 5 verification approach. Changed "add a task and verify relationship prompting" to "add a task and verify the skill prompts for blocking relationships with all existing tasks (predecessors and successors)."

### GAP-90: Parallel-eligible presentation criteria undefined
- **Severity**: medium
- **Source**: requirements-critic
- **Description**: The dependency-mapping requirement states the skill "presents all three tasks as parallel-eligible" but doesn't specify observable criteria for what "parallel-eligible" means in the presentation. How does the skill communicate this property to the author in a verifiable way?
- **Status**: resolved
- **Triage**: check-in
- **Decision**: Replace the undefined term "parallel-eligible" with concrete observable language directly in requirement scenarios. Change "presents all three tasks as parallel-eligible" to "presents all three tasks with no blocking relationship between them" and similar concrete phrasing across all occurrences. Eliminates the undefined term entirely.
- **Outcome**: Replaced all 7 occurrences of "parallel-eligible" in dependency-mapping requirements with concrete observable language. Rule text, scenario titles, and scenario steps now use "no blocking relationship between them" or equivalent phrasing. The undefined term is fully eliminated from requirement scenarios.

### GAP-92: No scenario for resuming a partially completed workflow
- **Severity**: medium
- **Source**: coverage-critic
- **Description**: The entire spec assumes continuous session state. No scenario addresses what happens if the author abandons the session mid-workflow and later resumes. Given FSM tasks execute as independent turns and conversation context is the state-passing mechanism, session interruption could lose intermediate state.
- **Status**: resolved
- **Triage**: defer-release
- **Decision**: Defer to future release. Add to functional.md Known Risks: "Session interruption requires restarting the workflow from the beginning — no resume capability exists." Add to functional.md Out of Scope: "Session resumption or recovery after workflow interruption."
- **Outcome**: Added "Session interruption requires restarting the workflow from the beginning — no resume capability exists" to functional.md Known Risks. Added "Session resumption or recovery after workflow interruption" to functional.md Out of Scope.

### GAP-93: Task navigation strategy unspecified during description writing phase
- **Severity**: medium
- **Source**: coverage-critic
- **Description**: No specification exists for how the author navigates between tasks during the description writing phase. When a workflow has five or more tasks, the skill's behavior for presenting tasks to the author — sequentially in dependency order, all at once for author choice, or other pattern — is unspecified.
- **Status**: resolved
- **Triage**: check-in
- **Decision**: The skill presents tasks one at a time in dependency order (topological sort) during the description writing phase. The author can request to skip to a specific task or return to revise a previously completed one. Consistent with the "skill proposes, author confirms/overrides" pattern used throughout the spec. Add this navigation strategy to CMP-descriptions responsibilities in technical.md and add a scenario to self-contained-descriptions requirements.
- **Outcome**: Added task navigation responsibility to CMP-descriptions in technical.md: "Present tasks one at a time in dependency order (topological sort) during the description writing phase; the author can request to skip to a specific task or return to revise a previously completed one." Added self-contained-descriptions:1.5 scenario for dependency-order navigation with skip/return. Updated infra.md self-contained-descriptions Rule 1 coverage to include navigation verification.

### GAP-96: ID generation strategy for tasks added during dependency mapping unspecified
- **Severity**: medium
- **Source**: coverage-critic
- **Description**: The dependency-mapping scenario for adding tasks during dependency mapping (GAP-82 resolution) specifies adding tasks after IDs have been assigned. GAP-20 (resolved) dismissed duplicate ID concerns because "IDs are auto-generated sequentially," but GAP-20 predates GAP-82 (step list modifications). The ID generation strategy for a newly inserted task is unspecified — does it get the next sequential ID, or does the sequence get re-numbered?
- **Status**: resolved
- **Triage**: check-in
- **Decision**: Use next-sequential IDs during authoring (new task gets max existing ID + 1, existing IDs stay stable). At CMP-fsm-json finalization, renumber all IDs to topological order and update all blockedBy references. Stable IDs during authoring, clean final output. Add this strategy to CMP-dependency-map responsibilities and CMP-fsm-json finalization responsibilities in technical.md.
- **Outcome**: Added ID generation strategy to CMP-dependency-map: "Newly added tasks receive the next sequential ID (max existing ID + 1); existing task IDs remain stable during authoring." Added finalization renumbering to CMP-fsm-json: "Renumber all task IDs to topological order (sequential starting at 1) and update all blockedBy references to match the new IDs."

### GAP-88: CMP-normalize fallback to brainstorming is structurally impossible
- **Severity**: medium
- **Source**: implementation-critic
- **Description**: CMP-normalize fallback to brainstorming when zero steps emerge is structurally impossible. CMP-normalize is blocked by all three intake tasks in the dependency graph — the intake phase has already completed before normalize executes. If zero steps emerge at normalize time, the intake tasks are already marked complete. "Fallback to brainstorming" would require re-executing CMP-intake-brainstorm, but task execution is atomic and cannot rewind to a completed predecessor. This finding raises a feasibility concern distinct from GAP-37 (which defined the fallback behavior) and GAP-65 (which defined the threshold).
- **Status**: resolved
- **Triage**: check-in
- **Decision**: Restructure the dependency graph so input-based intakes (existing-skill, written-steps) run in parallel and fan-in to brainstorming (which fills gaps from whatever material the other intakes produced), then brainstorming feeds normalize. New graph: `(IE|IW) → IB → N`. This makes brainstorming a gap-filling step with context from prior intakes rather than a parallel source. Remove the structurally impossible "fallback to brainstorming" language from intake tasks and CMP-normalize. Update CMP-intake-brainstorm's responsibilities and dependencies. Update the task dependency graph, data flow table, and related requirement scenarios.
- **Outcome**: Restructured the dependency graph from `(IE|IW|IB) → N` to `(IE|IW) → IB → N` across all spec artifacts. Changes applied: (1) technical.md Context section updated intake path handling paragraph to describe sequential brainstorming after input-based intakes. (2) technical.md system overview diagram and task dependency graph updated to show `IE → IB`, `IW → IB`, `IB → N`. (3) technical.md architecture bullet descriptions updated: CMP-intake-existing and CMP-intake-written are now "parallel input-based intake" blocking CMP-intake-brainstorm; CMP-intake-brainstorm is now "sequential gap-filling step" blocked by both input-based intakes; CMP-normalize depends only on CMP-intake-brainstorm. (4) technical.md data flow table updated brainstorming row to "gap-filling material, full step list, or skip." (5) CMP-intake-existing description changed from "One of three parallel intake sources" to "One of two parallel input-based intake sources" and removed "fallback to brainstorming" language. (6) CMP-intake-written description changed from "One of three parallel intake sources" to "One of two parallel input-based intake sources" and removed "fallback to brainstorming" language. (7) CMP-intake-brainstorm fully rewritten from parallel source to sequential gap-filling step with new responsibilities (review prior material, fill gaps or generate from scratch, validate combined output) and dependencies changed to `CMP-intake-existing, CMP-intake-written`. (8) CMP-normalize dependencies changed to `CMP-intake-brainstorm` only and removed "fallback to brainstorming" validation language. (9) OBJ-intake-convergence updated to reflect two input-based sources feeding brainstorming. (10) Decision 1 replaced with approved Y-statement describing the `(IE|IW) → IB → N` graph. (11) Decision 4 updated from "three parallel paths" to "multiple sources." (12) Risks section updated "intake evaluation overhead" to describe the sequential brainstorming step. (13) functional.md workflow-intake capability updated to describe brainstorming as gap-filling step. (14) functional.md Known Risks updated: "three separate intake paths" changed to "intake pipeline (two input-based sources plus brainstorming gap-filling)"; "falls back to brainstorming" changed to sequential brainstorming language. (15) functional.md What Changes and Scope sections updated. (16) workflow-intake requirements: Rule 1 text rewritten to describe input-based sources and brainstorming gap-filling; scenario 1.1 updated to source-specific guidance with brainstorming row reflecting gap-filling role; scenario 1.2 updated from "three intake paths" to "intake phase"; scenario 1.3 rewritten from fallback scenario to "input-based intakes yield no material and brainstorming generates full step list"; scenario 1.4 rewritten to describe input-based intakes producing material and brainstorming filling gaps. (17) workflow-intake Rule 4 rewritten from "guide brainstorming intake" to "guide brainstorming as a gap-filling step" with all scenarios updated to reflect sequential gap-filling role (4.1-4.2 add "input-based intakes have completed" given; 4.3-4.4 reference normalization instead of "next phase"; 4.5 adds "input-based intakes have completed with no material" given). (18) infra.md coverage table: Rule 1 changed from "Three distinct intake paths" to "Input-based sources and brainstorming gap-filling"; Rule 4 changed from "Brainstorming intake" to "Brainstorming gap-filling" with expanded verification. (19) infra.md "No meaningful workflow material" verification examples section rewritten to describe brainstorming behavior instead of fallback behavior.

### GAP-97: `description` field semantic overloading between CMP-normalize and CMP-descriptions
- **Severity**: medium
- **Source**: implicit-detection
- **Triage**: check-in
- **Status**: resolved
- **Description**: The `description` field carries two semantically different meanings across the pipeline. CMP-normalize produces `{label, description}` pairs where `description` is "a description of the work [the step] performs" (technical.md CMP-normalize responsibilities). The Data Transformation table confirms this as the initial field value. CMP-descriptions then "enriches `description`" (Data Transformation table) into a full self-contained instruction with goal, actions, and acceptance criteria. Meanwhile, the State Management section states "description writing adds `description`" — using "adds" rather than "enriches" or "replaces," implying it is a new field rather than a modification. The verb inconsistency ("enriches" vs "adds") combined with the same field name carrying both a brief work summary and a comprehensive self-contained instruction creates ambiguity about whether the CMP-descriptions phase appends to, replaces, or expands the normalize-phase description. An implementer could preserve the brief normalize description alongside the detailed one, append the detailed content to the brief summary, or fully replace it. The distinction matters because the brief normalize description serves the author during dependency mapping (they need to see what each step does), while the detailed CMP-descriptions output serves the executing agent after context compaction.
- **Decision**: CMP-descriptions explicitly replaces the normalize-phase brief `description` with the full self-contained instruction. The brief summary is transient authoring data visible in conversation context during dependency mapping but not preserved in the progressive artifact after CMP-descriptions runs. Update Data Transformation table from "enriches `description`" to "replaces `description`". Update State Management from "description writing adds `description`" to "description writing replaces `description`". No schema change — one `description` field with clear replacement semantics.
- **Outcome**: Updated technical.md Data Transformation table: CMP-descriptions "Fields added" column changed from `activeForm` (enriches `description`) to `activeForm` (replaces `description`). Updated technical.md State Management section: changed "description writing adds `description` and `activeForm`" to "description writing replaces `description` and adds `activeForm`". No schema changes needed — single `description` field retained with clear replacement semantics documented at both the data transformation and state management levels.

### GAP-98: Topological renumbering tie-breaking specification missing
- **Severity**: low
- **Source**: technical-critic
- **Triage**: delegate
- **Category**: resolved
- **Description**: CMP-fsm-json renumbers all task IDs to topological order during finalization, but topological sorts are not unique when multiple nodes share the same precedence level (e.g., parallel tasks). The design does not specify a tie-breaking rule for assigning sequential IDs to same-precedence nodes. This ambiguity affects testability (test expectations cannot predict final IDs for parallel tasks) and could produce non-deterministic output across runs.
- **Decision**: Use stable sort by original authoring order as the tie-breaking rule for same-precedence nodes during topological renumbering. Tasks assigned IDs earlier during CMP-dependency-map retain their relative order when they share the same topological precedence level. This preserves author intent, produces deterministic output, and allows test expectations to predict final IDs for parallel tasks.
- **Outcome**: Updated technical.md CMP-fsm-json first responsibility to specify tie-breaking rule: same-precedence nodes retain their original authoring order (the order IDs were assigned during CMP-dependency-map) via stable sort, producing deterministic output for parallel tasks.

### GAP-99: Validation result presentation format unspecified across components
- **Severity**: low
- **Source**: logic-critic
- **Triage**: delegate
- **Category**: resolved
- **Description**: Multiple components perform validation (CMP-normalize, CMP-dependency-map, CMP-descriptions, CMP-final-validation) but no shared specification defines the structure or presentation format for validation results. CMP-final-validation § Responsibilities references presenting pass/fail results per check, but the output format and presentation mechanism are undefined. Without a consistent format across validation points, incremental and final validation reporting may diverge in structure, making the workflow-validation § Rule 3 requirement for clear presentation difficult to verify.
- **Decision**: Document two distinct validation modes: (1) incremental phase-gate validation within tasks is conversational — the agent identifies issues and works with the author to fix them inline, no formal output structure needed; (2) CMP-final-validation produces structured pass/fail results per check with specific issues listed for each failure. Only CMP-final-validation requires a defined presentation format. This accurately reflects the system's design where incremental validation is interactive dialogue and final validation is a structured report.
- **Outcome**: Updated technical.md Validation Scope section to explicitly document the two validation modes: phase checks use conversational validation (no formal output structure) while CMP-final-validation produces structured pass/fail results (the only validation point with a defined presentation format). Added Y-Statement to Decisions section documenting the validation result presentation choice.

### GAP-100: Brainstorming gap-filling step has undefined behavior when it yields no output
- **Severity**: low
- **Source**: stale-detection
- **Triage**: check-in
- **Category**: resolved
- **Description**: CMP-intake-brainstorm is a sequential gap-filling step that runs after the two input-based intakes (CMP-intake-existing, CMP-intake-written) complete. No behavior is specified for when brainstorming itself yields no usable output — for example, if the author declines to provide any ideas and neither input-based intake contributed material. The skill's behavior at this terminal dead-end is undefined. (Restated from GAP-41 without the pre-GAP-88 "fallback" framing.)
- **Decision**: Graceful exit. If brainstorming yields no usable steps after the author declines to provide ideas and no prior intake produced material, the skill acknowledges the author is not ready to define a workflow and suggests returning later. The workflow terminates cleanly rather than looping indefinitely.
- **Outcome**: No artifact changes needed — graceful exit behavior is already specified in CMP-intake-brainstorm's responsibilities in technical.md.

### GAP-101: No scenario for skill targeting a non-existent plugin directory
- **Severity**: medium
- **Source**: requirements-coverage-critic
- **Category**: resolved
- **Description**: The skill-file-generation capability specifies file placement under plugins/<plugin>/skills/<skill>/ but no scenario covers the case where the author specifies a plugin name that does not correspond to an existing plugin directory.
- **Triage**: check-in
- **Decision**: Create the target directory during file placement. By the time files are being written, the author has already confirmed the skill and plugin names (via auto-normalize + confirmation in CMP-skill-md). Add directory creation to the file placement step. Co-resolves with GAP-102 on directory handling.
- **Outcome**: Added skill-file-generation:4.3 scenario for directory creation when the target directory does not exist. Updated CMP-skill-md and CMP-fsm-json responsibilities in technical.md: CMP-skill-md now creates the target directory during placement and handles collision detection; CMP-fsm-json references CMP-skill-md for directory handling. Co-resolved with GAP-102.

### GAP-102: No scenario for skill name colliding with an existing skill directory
- **Severity**: medium
- **Source**: requirements-coverage-critic
- **Category**: resolved
- **Description**: The skill-file-generation capability specifies directory placement but no scenario covers what happens when the target skill directory already exists and contains files.
- **Triage**: check-in
- **Decision**: Add collision detection. When the target skill directory already exists and contains files, the skill detects the collision and offers the author options (overwrite, rename, abort). Add a scenario to skill-file-generation covering this case. Co-resolves with GAP-101 on directory handling.
- **Outcome**: Added skill-file-generation:4.4 scenario for collision detection when the target directory already exists. Updated CMP-skill-md responsibilities in technical.md to detect existing directories and offer overwrite/rename/abort options. Co-resolved with GAP-101.

### GAP-103: No behavioral verification implementation despite infra.md mandate
- **Severity**: high
- **Source**: test-tasks-critic
- **Category**: resolved
- **Description**: The infra.md file defines detailed manual verification approaches for all capabilities but tasks.yaml contains zero tasks implementing these procedures. The verification group only tests structural aspects.
- **Triage**: check-in
- **Decision**: Add behavioral verification tasks to tasks.yaml for all 5 capabilities. Create a behavioral-verification group with one task per capability, deriving manual verification procedures from infra.md's coverage tables. Co-resolves with GAP-104 (confirmation gates observed during behavioral testing).
- **Outcome**: Added `behavioral-verification` group to tasks.yaml with one task per capability (workflow-intake, dependency-mapping, self-contained-descriptions, skill-file-generation, workflow-validation). Each task derives its verification procedure from infra.md's Coverage by capability tables. Confirmation gate observation is explicitly included in each task's verification steps, co-resolving GAP-104. Added a "Relationship to tasks.yaml" subsection to infra.md clarifying that infra.md defines what/how to verify while tasks.yaml provides actionable implementation tasks. Co-resolved with GAP-104.

### GAP-104: E2E verification for confirmation gates not covered
- **Severity**: medium
- **Source**: test-tasks-critic
- **Category**: resolved
- **Description**: While GAP-55 (resolved) establishes that AskUserQuestion is inherently blocking by construction, no E2E verification task confirms that the skill actually uses confirmation gates at the correct workflow points. A skill could omit all confirmation gates and still pass current verification tasks.
- **Triage**: check-in
- **Decision**: Fold into GAP-103's behavioral verification tasks. Confirmation gates are naturally observed during behavioral testing — e.g., testing workflow-intake:2.3 exercises the confirmation gate. No separate mechanism needed. Co-resolved by GAP-103.
- **Outcome**: Each behavioral verification task in tasks.yaml explicitly includes confirmation gate observation as a verification step (e.g., "Confirm that the author confirmation gate (AskUserQuestion) is observed during intake"). No separate mechanism needed — confirmation gates are exercised as part of the behavioral verification workflow. Co-resolved by GAP-103.

### GAP-105: Verification Examples boundary cases not tested
- **Severity**: low
- **Source**: test-tasks-critic
- **Category**: resolved
- **Description**: The infra.md file defines concrete boundary examples for scenario categories but tasks.yaml has no tasks testing these boundary cases against the delivered artifacts.
- **Triage**: delegate
- **Decision**: Reframe boundary examples as acceptance criteria. The Verification Examples in infra.md are reference material for consistent manual verification — benchmarks for pass/fail decisions during behavioral testing. They are not implementation tasks for tasks.yaml. tasks.yaml is for building the skill; the examples guide testing of the built result.
- **Outcome**: Added a clarifying note to infra.md's Verification Examples section stating these are reference material and acceptance criteria for the `behavioral-verification` tasks in tasks.yaml — benchmarks for consistent pass/fail decisions during manual behavioral testing, not separate implementation tasks.

### GAP-106: Prohibited term detection requires callable mechanism
- **Severity**: medium
- **Source**: test-infra-critic
- **Category**: superseded
- **Superseded by**: GAP-120
- **Description**: The prohibited term verification protocol (from GAP-56 resolution) requires modifying the generated SKILL.md to insert each term and re-running the scan, but no callable scan function is documented for independent invocation.
- **Triage**: check-in
- **Decision**: Clarify that the scan is an agent-executed instruction, not a standalone callable. CMP-skill-md's description says "scan output for SPEC-prohibited-terms using case-insensitive substring matching." The agent follows this instruction directly. "Re-running the scan" in the verification protocol means re-executing this scanning instruction on modified content. No separate callable function is needed.
- **Outcome**: Updated infra.md's prohibited term verification protocol step 2b to explicitly state "re-run the prohibited term scan by having the agent re-execute CMP-skill-md's scanning instruction on the modified content — this is an agent-executed instruction, not a standalone callable function." Added closing clarification that "re-running the scan" means re-executing the scanning instruction from CMP-skill-md's task description.
- **Current approach**: GAP-120 removed SPEC-prohibited-terms and the scanning instruction from CMP-skill-md. No scanning mechanism exists; SKILL.md content quality relies on author judgment.

### GAP-107: Verification instructions for cycle detection report format missing
- **Severity**: medium
- **Source**: test-infra-critic
- **Category**: resolved
- **Description**: While GAP-54 (resolved) specifies Kahn's algorithm as the cycle detection implementation and adds test cases with expected outputs to infra.md, verification instructions for confirming the skill's actual report matches the expected format are missing.
- **Triage**: check-in
- **Decision**: Define the cycle detection report as conversational output. Technical.md's decision on validation modes states incremental validation is conversational with no formal output structure. The specification already says "report the set of unconsumed task IDs and labels" — this is the semantic content to verify. Behavioral verification checks that the report identifies the correct tasks, not that it uses exact phrasing.
- **Outcome**: Added a clarifying note to infra.md's cycle detection test cases section stating that expected output describes semantic content to verify (correct tasks identified), not exact phrasing or format, consistent with the conversational validation mode defined in technical.md.

### GAP-108: Missing feedback loop scenarios for validation-driven corrections
- **Severity**: high
- **Source**: integration-critic
- **Category**: resolved
- **Description**: Validation failures create bidirectional feedback affecting multiple capabilities. No scenario tests whether a correction in one capability (such as task descriptions) can invalidate another capability's output (such as dependency mapping).
- **Triage**: check-in
- **Decision**: Resolve as pipeline non-issue. The pipeline is strictly forward: intake → normalize → dependencies → descriptions → fsm.json → final validation. Corrections happen within each phase before advancing. CMP-final-validation's in-place description corrections can't invalidate the dependency graph (already finalized), can't change the SKILL.md (independent), and structural integrity is a read-only check. The integration.feature.md "No Integration Scenarios Required" stance stands.
- **Outcome**: Added a note to integration.feature.md reinforcing that the forward-only pipeline prevents backward cascading of corrections. CMP-final-validation's in-place description corrections cannot invalidate upstream artifacts. The "No Integration Scenarios Required" stance is supported by this pipeline property.

### GAP-109: No scenario for task restructuring affecting multiple downstream artifacts
- **Severity**: medium
- **Source**: integration-critic
- **Category**: resolved
- **Description**: When dependency-mapping detects a cycle and the author restructures tasks, this affects both the dependency graph and task descriptions simultaneously. No scenario covers this cross-capability update.
- **Triage**: check-in
- **Decision**: Resolve as pipeline ordering non-issue. CMP-dependency-map runs before CMP-descriptions in the pipeline. When the author restructures tasks during dependency mapping, descriptions don't exist yet. The only artifact affected is the dependency graph itself, which dependency-mapping:5.1-5.3 already cover (removal cleans dangling refs, addition prompts for relationships, rename preserves relationships). No cross-capability impact is possible.
- **Outcome**: Added a note to integration.feature.md explaining that step list modifications during CMP-dependency-map precede CMP-descriptions in the pipeline, so restructuring cannot affect descriptions. The existing dependency-mapping scenarios (5.1-5.3) already cover the only affected artifact.

### GAP-110: infra.md coverage table for skill-file-generation Rule 4 missing scenarios 4.3 and 4.4
- **Severity**: medium
- **Source**: implicit-detection
- **Category**: resolved
- **Description**: The infra.md coverage table for skill-file-generation Rule 4 ("Correct directory structure") lists only file placement and colocation scenarios. The newly added scenarios — directory creation when the target does not exist (4.3) and collision detection with overwrite/rename/abort options (4.4) — have no corresponding coverage or verification approach entries in the table. The behavioral-verification task for skill-file-generation already includes these verification steps, but the infra.md table that behavioral-verification tasks derive from is incomplete.
- **Triage**: delegate
- **Decision**: Update infra.md Rule 4 coverage table to include scenarios 4.3 and 4.4 with corresponding verification approaches. Co-resolves with GAP-111 on directory handling completeness.
- **Outcome**: Updated infra.md skill-file-generation Rule 4 "What it covers" to include "target directory created if it does not exist (4.3); existing directory detected with overwrite/rename/abort options (4.4)." Updated verification approach to include "verify the skill creates the target directory when it does not exist; verify the skill detects an existing directory and offers overwrite/rename/abort options before placing files." Co-resolved with GAP-111.

### GAP-111: tasks.yaml fsm-json entry 5 omits directory creation and collision detection
- **Severity**: medium
- **Source**: implicit-detection
- **Category**: resolved
- **Description**: The tasks.yaml fsm-json group entry 5 (Draft skill documentation) scripts the fsm.json content for CMP-skill-md but does not include directory creation or collision detection in its description instructions. The Covers reference ends at skill-file-generation:4.1-4.2, missing 4.3 and 4.4. Without these instructions, the delivered fsm.json entry for the documentation task would lack self-contained guidance for directory creation and collision detection behavior.
- **Triage**: delegate
- **Decision**: Add directory creation and collision detection instructions to entry 5's description and extend Covers line to 4.4. Co-resolves with GAP-110 on directory handling completeness.
- **Outcome**: Added points (h) and (i) to tasks.yaml fsm-json entry 5: (h) create the target directory if it does not exist, (i) detect when the target skill directory already exists and offer overwrite/rename/abort options. Renumbered former (h) to (j). Extended Covers from skill-file-generation:4.1-4.2 to 4.1-4.4. Co-resolved with GAP-110.

### GAP-112: Phase advancement validation unspecified when task descriptions are incomplete due to skipping
- **Severity**: medium
- **Source**: requirements-coverage-critic
- **Category**: resolved
- **Description**: The self-contained-descriptions capability allows the author to skip to a specific task during the description writing phase, but no specification addresses what happens when the author attempts to advance to the next phase without completing descriptions for skipped tasks. An implementer could allow phase advancement with unwritten descriptions, contradicting the self-contained-descriptions requirement that tasks have author-confirmed descriptions. This concern is related to GAP-93 (resolved), which established the navigation strategy (dependency order, skip, return), but GAP-93 did not address the validation gate interaction when descriptions remain incomplete.
- **Triage**: check-in
- **Decision**: Add a completeness gate scenario (workflow-validation:1.3.2) that explicitly ties skip behavior to the phase gate: when the author has skipped tasks without writing descriptions, the skill reports which tasks have incomplete descriptions and blocks advancement until all tasks have descriptions. This is consistent with existing phase gate patterns (1.3.1, 1.4, 1.5) and makes the skip-advance interaction testable.
- **Outcome**: Added workflow-validation:1.3.2 scenario to requirements/workflow-validation/requirements.feature.md after 1.3.1. Updated tasks.yaml fsm-json entry 7 Covers line to include 1.3.2. Updated infra.md workflow-validation Rule 1 coverage table to include skipped-task advancement blocking and corresponding verification approach. Updated tasks.yaml behavioral-verification for workflow-validation to include skip-and-advance verification.

### GAP-113: ActiveForm override validation missing when non-present-continuous text is provided
- **Severity**: medium
- **Source**: requirements-coverage-critic
- **Category**: resolved
- **Description**: The self-contained-descriptions capability specifies that the author can confirm or override the generated activeForm field, but no scenario covers the override path where the author provides text that is not in present-continuous form. The skill-file-generation requirement mandates that activeForm contain present-continuous form for status display. The interaction between the override capability and the format requirement is unspecified, leaving implementers unclear on whether to validate overridden activeForm values or accept any author-provided text.
- **Triage**: check-in
- **Decision**: Accept any author-provided override as-is. The present-continuous form requirement applies to auto-generated values only. When the author chooses to override, the skill respects the author's autonomy. Clarify in the spec that the format requirement governs auto-generation, not author overrides.
- **Outcome**: Added self-contained-descriptions:4.2 scenario to requirements/self-contained-descriptions/requirements.feature.md covering the override-accepted path. Clarified skill-file-generation:3.3 that present-continuous form is the auto-generated default with author overrides accepted as-is. Updated CMP-fsm-json in technical.md to note that activeForm format validation does not apply to author overrides. Updated tasks.yaml entry 7 point (h) and entry 8 point (c) to reflect override acceptance. Extended entry 7 Covers to self-contained-descriptions:4.1-4.2. Updated infra.md self-contained-descriptions Rule 4 coverage and activeForm verification example to reference 4.2 override behavior.

### GAP-114: Redundant dependency graph verification in tasks.yaml
- **Severity**: low
- **Source**: code-tasks-critic
- **Category**: resolved
- **Description**: The verification group in tasks.yaml includes a task to verify that the fsm.json dependency graph matches the authoritative graph from technical.md. However, the fsm.json construction tasks already prescribe exact blockedBy values derived from technical.md. The verification becomes redundant unless construction tasks could produce incorrect dependency values, which would indicate a specification gap in the construction tasks themselves rather than a verification need.
- **Triage**: delegate
- **Decision**: Keep the verification task as a defense-in-depth safety net. The redundancy is intentional — even though construction tasks prescribe exact values, implementation errors could produce incorrect dependency values. The cost is one verification step; redundancy in verification is acceptable for correctness-critical outputs that produce deployable skill artifacts.
- **Outcome**: No artifact changes. The current spec is correct as-is. The verification task in tasks.yaml intentionally duplicates the dependency graph check as a defense-in-depth safety net — construction tasks prescribe exact values but the verification step catches implementation errors in the construction.

### GAP-115: Prohibited terms scanning in SKILL.md lacks exception guidance for meta-level references
- **Severity**: low
- **Source**: code-tasks-critic
- **Category**: superseded
- **Superseded by**: GAP-120
- **Description**: The skill-md task in tasks.yaml instructs scanning SKILL.md for prohibited terms without exception guidance. The fsm.json task acknowledges meta-level exceptions for task entries that list prohibited terms for scanning purposes. The skill-md task has no corresponding guidance on whether SKILL.md might legitimately reference prohibited terms when explaining the workflow's validation steps, creating ambiguity for implementers about when to treat detected terms as violations versus legitimate meta-level documentation.
- **Triage**: delegate
- **Decision**: Add a clarifying note to CMP-skill-md component responsibilities: all prohibited terms detected in SKILL.md are violations with no meta-level exceptions (unlike fsm.json task descriptions, which may embed the term list for self-containment). SKILL.md is pure author-facing documentation and should never reference internal mechanism terms for any purpose.
- **Outcome**: Added no-meta-level-exceptions clarification to CMP-skill-md's prohibited terms scan responsibility in technical.md. Updated tasks.yaml skill-md scanning task and fsm-json entry 5 point (d) to state that all prohibited terms in SKILL.md are violations with no exceptions.
- **Current approach**: GAP-120 removed SPEC-prohibited-terms entirely. CMP-skill-md no longer scans for prohibited terms, so meta-level exception guidance is moot.

### GAP-116: CMP-skill-md self-validation independence not justified in branch point rationale
- **Severity**: medium
- **Source**: design-critic
- **Category**: resolved
- **Description**: The branch point rationale in technical.md Decision 3 focuses on input dependencies (CMP-skill-md only needs the normalized step list) but does not address why self-validation of output can complete independently without feeding into final validation. CMP-skill-md's self-validation includes prohibited term scanning on the final SKILL.md text output, not the input. The rationale should explain why output validation can complete in parallel with the main chain rather than only explaining input dependency timing.
- **Triage**: check-in
- **Decision**: Extend Decision 3's Y-Statement with output-independence reasoning — SKILL.md content is functionally independent of fsm.json, so CMP-skill-md's self-validation (frontmatter check) covers all applicable checks without needing cross-artifact validation
- **Outcome**: Extended Decision 3 Y-Statement in technical.md by integrating output-independence reasoning into the accepting clause: "accepting that CMP-final-validation does not cover SKILL.md checks because SKILL.md content is functionally independent of fsm.json and the frontmatter check covers all applicable output correctness concerns (CMP-skill-md handles its own)." Co-resolved with GAP-120 (prohibited term removal simplified the self-validation scope).

### GAP-117: Brainstorming sequential gap-filling has no verification criteria for identifying gaps
- **Severity**: medium
- **Source**: verification-critic
- **Category**: resolved
- **Description**: The brainstorming intake phase requires reviewing prior intake material and identifying gaps or thin areas to fill. No objective criteria exist for what constitutes a gap or thin area in workflow material. Without verification criteria, testers cannot determine whether the skill correctly identified all gaps or whether identified gaps were genuine.
- **Triage**: check-in
- **Decision**: Define a gap taxonomy in functional.md with four categories — structural gaps (missing workflow phases), depth gaps (phases with insufficient detail to act on), coverage gaps (workflow paths not represented), consistency gaps (contradictions between steps) — giving verifiers a concrete checklist to evaluate brainstorming effectiveness
- **Outcome**: Added "Brainstorming Gap Taxonomy" section to functional.md with four categories (structural gaps, depth gaps, coverage gaps, consistency gaps) and descriptions explaining what each category means and how verifiers evaluate brainstorming effectiveness against them.

### GAP-118: Dependency mapping task adjacency has no scalability criteria for large workflows
- **Severity**: low
- **Source**: verification-critic
- **Category**: resolved
- **Description**: The dependency mapping phase requires presenting dependency relationships for author confirmation when adding tasks. For large workflows with many tasks, the skill must handle scalability of presenting "all existing tasks" for relationship specification. No criteria define thresholds for different interaction patterns (e.g., when to paginate, when to offer search, when to suggest grouping by subsystem).
- **Triage**: defer-release
- **Decision**: Record as Known Risk in functional.md — large workflows may have poor UX during dependency mapping when presenting all existing tasks for relationship specification; no upper workflow size limit defined
- **Outcome**: Added Known Risk entry to functional.md: "Large workflows may have poor UX during dependency mapping when presenting all existing tasks for relationship specification — no upper workflow size limit is defined, and no scalability criteria (pagination, search, grouping) exist for presenting tasks during dependency mapping."

### GAP-119: Multi-source intake scenarios lack test data construction guidance
- **Severity**: high
- **Source**: design-for-test-critic
- **Category**: resolved
- **Description**: The intake phase supports multiple sources (existing skill analysis, written step descriptions, brainstorming gap-filling), and CMP-normalize concatenates all contributions. Test verification requires multi-source intake scenarios with duplicate or conflicting steps from different sources. Infra.md provides no guidance on constructing test data showing how the skill handles material that overlaps across sources or contains subtle conflicts.
- **Triage**: check-in
- **Decision**: Add 4 concrete multi-source test scenarios to infra.md — (a) identical steps from two sources (duplicate detection), (b) same-label different-description steps (conflict resolution), (c) complementary non-overlapping steps (clean merge), (d) one source contributing nothing (skip handling) — each with expected verification behavior
- **Outcome**: Added "Multi-source intake scenarios" section to infra.md with four scenarios: (A) identical steps from two sources — author resolves duplicates during normalization, (B) same label/different description — author resolves conflict during normalization, (C) complementary non-overlapping steps — clean concatenation, (D) one source contributing nothing — normalize processes the sole contributed material.

### GAP-120: Prohibited term detection has no edge case test guidance
- **Severity**: medium
- **Source**: design-for-test-critic
- **Category**: resolved
- **Description**: The prohibited term detection uses case-insensitive substring matching on terms like 'task', 'hook', and '.json'. Edge cases exist where legitimate usage would be flagged (terms embedded in compound words like 'task-directory-structure', punctuation variations like 'task_file' vs 'task file', file references like 'config.json' or 'package.json'). Infra.md provides verification protocol for exact term detection but not for distinguishing legitimate usage from prohibited usage in edge cases.
- **Triage**: check-in
- **Decision**: Remove the prohibited term prohibition entirely — users may legitimately want skills that work with tasks, hooks, or JSON files. Remove SPEC-prohibited-terms, remove prohibited term scanning from CMP-skill-md self-validation and CMP-final-validation, remove the verification protocol from infra.md, and update skill-file-generation requirements accordingly. Rely on author judgment during SKILL.md writing instead of automated prohibition
- **Outcome**: Removed SPEC-prohibited-terms specification from technical.md. Removed prohibited term scanning from CMP-skill-md responsibilities — self-validation now covers frontmatter only. Removed prohibited term scan from CMP-final-validation — now runs 3 checks (cycle detection, self-containment audit, structural integrity) instead of 4. Removed prohibited term rows from Validation Scope table. Removed prohibited term verification protocol section from infra.md. Updated skill-file-generation requirements: removed Rule 2 (prohibited term Scenario Outline and correction scenario), replaced with Rule 2 (self-validation for frontmatter), renumbered subsequent rules. Removed workflow-validation:2.9 (prohibited term scan scenario). Updated integration.feature.md to remove prohibited term cross-capability reference. Updated tasks.yaml: removed SKILL.md prohibited term scanning task, removed prohibited term constraints from fsm-json task, removed prohibited term check from entry 5 and entry 9, removed prohibited term references from behavioral-verification and verification tasks. Updated functional.md: removed Out of Scope entry about formal boundary between author-facing language and SPEC-prohibited-terms list, removed Known Risk about generated skill documentation revealing workflow storage. Updated Decision 3 Y-Statement to reference frontmatter-only self-validation. Updated Data flow table description for CMP-skill-md. Updated Validation Scope paragraph.

### GAP-121: Self-containment checklist verification lacks false-positive boundary test cases
- **Severity**: medium
- **Source**: design-for-test-critic
- **Category**: resolved
- **Description**: Infra.md provides examples of descriptions that fail each self-containment checklist item. Missing are examples of descriptions that appear to fail but should actually pass. For instance, checklist item (d) requires no undefined references - "PostgreSQL" should pass (well-known technology with implicit definition), while "the normalized step list" should fail (assumes context from earlier phase). Boundary cases where the pass/fail distinction is subtle are not provided.
- **Triage**: check-in
- **Decision**: Add borderline-pass examples alongside existing fail examples for all 4 self-containment checklist items (goal statement, specific actions, acceptance criteria, no undefined references) in infra.md — covers boundary confusion across the entire checklist, not just item (d)
- **Outcome**: Added "Borderline pass" column to the self-containment checklist verification table in infra.md. Each of the 4 checklist items now has a borderline-pass example with reasoning explaining why it passes despite appearing borderline: (a) goal framed in terms of enabling downstream — passes because outcome is concrete, (b) high-level actions without file paths — passes because iteration pattern and action are specific enough, (c) weak but objectively checkable criterion — passes because it is verifiable even if not strong, (d) domain-specific term with broad ecosystem definition — passes because it is widely understood.

### GAP-122: Metadata field absent from progressive construction cumulative output tracking
- **Severity**: high
- **Source**: design-critic
- **Category**: resolved
- **Description**: The Data Transformation table in technical.md shows cumulative output ending at the description writing phase with fields (task_id, label, description, activeForm, blockedBy). The JSON generation phase requires metadata field. The metadata field never appears in the cumulative output column, creating a gap in the progressive construction field-addition tracking. The table should show when metadata is added to the cumulative artifact.
- **Triage**: check-in
- **Decision**: Add a CMP-fsm-json row to the Data Transformation table showing metadata addition during finalization — cumulative output becomes {task_id, label/subject, description, activeForm, blockedBy[], metadata}
- **Outcome**: Added a Finalize row to the Data Transformation table in technical.md for CMP-fsm-json, showing `metadata` as the field added and `{task_id, label/subject, description, activeForm, blockedBy[], metadata}` as the cumulative output.

### GAP-123: No scenario for written step descriptions containing inter-task dependency hints
- **Severity**: medium
- **Source**: requirements-coverage-critic
- **Category**: resolved
- **Description**: The workflow intake validation rules cover vague descriptions (Rule 3.2), well-structured descriptions (Rule 3.1), and overly large descriptions (Rule 3.3). Missing is guidance for descriptions that contain explicit dependency information embedded in the text (e.g., "after the config is generated, validate it"). This is distinct from the self-contained-descriptions capability (which applies during description writing, not intake) - the concern is how intake handles dependency hints in authored step descriptions.
- **Triage**: check-in
- **Decision**: Add guidance to CMP-intake-written that dependency hints in descriptions are preserved as-is during intake and inform CMP-dependency-map — include a verification example showing how a dependency hint flows from intake through to dependency mapping
- **Outcome**: Added responsibility to CMP-intake-written in technical.md: "Preserve dependency hints embedded in descriptions as-is — these hints are not acted on during intake but are preserved and inform CMP-dependency-map during the dependency mapping phase." Added "Dependency hint preservation through intake to dependency mapping" verification example to infra.md showing a two-step workflow where a dependency hint in a written step description flows from intake through normalization to dependency mapping.

### GAP-124: No scenario for dependency mapping with single-task workflow
- **Severity**: low
- **Source**: requirements-coverage-critic
- **Category**: resolved
- **Description**: The minimum workflow size was changed from 2 steps to 1 step. The dependency mapping phase with a single-task workflow represents a trivially-empty dependency graph boundary case. No scenario covers the skill's behavior when dependency mapping executes but there are no inter-task relationships to encode.
- **Triage**: delegate
- **Decision**: Add a scenario to dependency-mapping requirements covering single-task workflows — the task produces an empty blockedBy array and the dependency mapping phase confirms the trivially empty graph with the author before completing
- **Outcome**: Added dependency-mapping:6 Rule ("The skill SHALL handle single-task workflows during dependency mapping") and dependency-mapping:6.1 Scenario ("Single-task workflow produces empty dependency graph") to dependency-mapping requirements. The scenario covers: single task produces empty blockedBy, skill confirms trivially empty graph with author, skill proceeds after confirmation.

### GAP-125: Empty directory boundary case not explicitly addressed in skill file generation
- **Severity**: low
- **Source**: requirements-coverage-critic
- **Category**: deprecated
- **Description**: The skill file generation phase handles non-existent directories (creates them) and existing directories with files (overwrites with confirmation). The empty existing directory boundary case is not explicitly covered - a directory exists at the plugin/skill path but contains no files. While implementation likely handles this correctly (treats as existing location), the scenario coverage leaves this boundary implicit.
- **Triage**: defer-release
- **Decision**: Not worth addressing — the existing directory detection behavior is acceptable for empty directories; close without further action
- **Rationale**: Empty directory behavior is subsumed by existing directory detection logic. The user confirmed the concern is not worth addressing — an empty directory at the target path is functionally equivalent to a non-existent directory for the purpose of file placement (no files to overwrite, no conflicts to resolve). The skill-file-generation:4.3 scenario (non-existent directory creation) and 4.4 scenario (existing directory with files) cover the meaningful boundary cases.

### GAP-126: Test environment setup for 9-component pipeline execution not documented
- **Severity**: high
- **Source**: design-for-test-critic
- **Category**: resolved
- **Description**: Infra.md describes manual verification by "invoking the skill" but provides no setup instructions for creating the FSM plugin test environment. The skill executes a 9-component pipeline with progressive construction, confirmation gates, and validation at multiple phases. Verifiers cannot systematically execute behavioral verification tasks without documented environment setup procedures.
- **Triage**: check-in
- **Decision**: Add a "Verification environment" section to infra.md with prerequisites (Claude Code CLI, FSM plugin enabled, fresh session) and setup steps (ensure FSM plugin in plugins directory, start new session, invoke skill by name)
- **Outcome**: Added "Verification Environment" section to infra.md with three subsections: Prerequisites (Claude Code CLI, FSM plugin enabled, fresh session), Setup Steps (5 numbered steps from ensuring plugin presence to verifying hydration), and Session Management (guidance on single-session vs multi-session verification and fresh invocation requirements).

### GAP-127: Progressive construction artifact feasibility mechanics unspecified
- **Severity**: low
- **Source**: technical-critic
- **Status**: resolved
- **Description**: Progressive fsm.json construction is the default workflow (GAP-31 resolution) where the artifact is built incrementally across phases. However, no specification addresses feasibility challenges: how the partial artifact is represented to the agent during intermediate phases, how field additions are verified to affect all task stubs simultaneously, or what recovery mechanism exists if the agent loses the in-progress artifact. The resolved gaps define the construction strategy (GAP-31, GAP-46) and field replacement semantics (GAP-97), but not the mechanics of maintaining and recovering partial state.
- **Triage**: delegate
- **Decision**: Add a Progressive Construction Protocol note to technical.md State Management covering: (a) representation — the artifact is maintained as a JSON structure in conversation context, (b) verification — each phase updates all entries before completing, (c) recovery — reconstruct from the most recent complete phase output visible in conversation history.
- **Outcome**: Added "Progressive Construction Protocol" subsection to technical.md State Management with three protocol items (representation, verification, recovery). Also clarified that progressive construction describes runtime behavior of the delivered skill, not implementation structure (co-resolved with GAP-132).

### GAP-132: tasks.yaml does not implement progressive construction workflow
- **Severity**: high
- **Source**: code-tasks-critic
- **Status**: resolved
- **Description**: The tasks.yaml implementation generates fsm.json in a single complete generation step rather than implementing the progressive construction workflow defined in technical.md State Management. The progressive workflow specifies stub creation followed by iterative field addition across all tasks, but the task group structure does not reflect this pattern. The implementation approach conflicts with the technical design's default construction model (GAP-31 resolution).
- **Triage**: check-in
- **Decision**: Clarify in technical.md State Management that progressive construction describes the runtime behavior of the delivered skill (how it guides the author), not the implementation structure of the skill's own fsm.json. The tasks.yaml fsm-json group correctly writes static file content — the implementor knows all 9 entries upfront. The task descriptions within those entries instruct the agent to use progressive construction at runtime.
- **Outcome**: Added clarification to technical.md State Management opening paragraph distinguishing runtime behavior (progressive construction during author session) from implementation structure (static fsm.json written by implementor). Co-resolved with GAP-127.

### GAP-128: Topological renumbering ID mapping and referential integrity verification unspecified
- **Severity**: medium
- **Source**: technical-critic
- **Status**: resolved
- **Description**: The fsm.json finalization component renumbers all task IDs to topological order and updates all blockedBy references (GAP-96 resolution). No specification addresses how the agent constructs the ID mapping between original authoring IDs and final topological IDs, whether it validates that all blockedBy references point to valid task IDs after renumbering, or how it handles tasks with multiple blockedBy entries. The resolved gaps define the renumbering strategy (GAP-96) and tie-breaking rule (GAP-98), but not the mapping construction or verification mechanics.
- **Triage**: check-in
- **Decision**: Add a post-renumbering validation step to CMP-fsm-json responsibilities: after renumbering task IDs to topological order and updating blockedBy references, verify all blockedBy references resolve to valid IDs in the renumbered array. The mapping construction and traversal mechanics are standard algorithmic work that does not require additional specification.
- **Outcome**: Added post-renumbering validation clause to CMP-fsm-json responsibilities in technical.md: "After renumbering, verify that all blockedBy references resolve to valid IDs in the renumbered array."

### GAP-130: workflow-validation scenarios use non-normative language for validation criteria
- **Severity**: medium
- **Source**: requirements-critic
- **Status**: resolved
- **Description**: The workflow-validation requirement scenarios use non-normative language for validation criteria rather than SHALL/SHALL NOT/MAY. For example, scenario text describes validation checks without normative keywords indicating whether the check is mandatory or optional. Previous normative language fixes (GAP-6, GAP-16, GAP-47) addressed other requirement files but not workflow-validation scenarios.
- **Triage**: delegate
- **Decision**: Apply SHALL consistently to validation Then clauses in workflow-validation requirements, matching the pattern established by GAP-6 and GAP-16 for other requirement files. Change "checks that" / "verifies" to "SHALL check" / "SHALL verify" in scenario Then clauses.
- **Outcome**: Changed all "checks that" to "SHALL check that" and "verifies" to "SHALL verify" in workflow-validation Then/And clauses (scenarios 1.1, 1.2, 1.3, 2.1, 2.2). Matches the normative language pattern established by GAP-6 and GAP-16.

### GAP-129: Behavioral verification tasks lack explicit scenario ID mapping
- **Severity**: high
- **Source**: test-tasks-critic
- **Status**: deprecated
- **Description**: The behavioral verification tasks in tasks.yaml derive from infra.md coverage tables (GAP-103 resolution) but do not systematically enumerate or map to specific requirement scenario IDs. Task descriptions reference requirements generically without establishing which scenarios are verified, how verification results map back to scenario IDs, or whether all scenarios from a capability are covered. This makes it unclear whether partial scenario coverage would be detected.
- **Triage**: check-in
- **Decision**: Dismiss. The infra.md schema template explicitly prohibits per-scenario enumeration in infra.md ("NOT per-scenario enumeration — scenario details are owned by requirements files"). The critic lacked access to the infra.md template and demanded exactly what the schema prohibits. Rule-level coverage tables are the design intent of the schema. No changes needed.
- **Rationale**: The infra.md schema template (Testing Strategy comment, line 30) states "NOT per-scenario enumeration — scenario details are owned by requirements files." The critic's request for explicit scenario ID mapping directly contradicts this schema constraint. The existing Rule-level coverage tables in infra.md are the intended granularity per the schema design. The critic produced this gap without access to the infra.md template, which explains the mismatch between the gap's expectation and the schema's intent.

### GAP-131: workflow-validation final audit scenario combines multiple distinct verification behaviors
- **Severity**: low
- **Source**: requirements-critic
- **Status**: resolved
- **Description**: The workflow-validation final self-containment audit scenario combines multiple distinct verification behaviors in a single Then clause: structural completeness checks, term definition coverage, and external reference detection. Each verification behavior could pass or fail independently. The prior atomicity fix (GAP-7) addressed workflow-intake scenarios but not workflow-validation.
- **Triage**: delegate
- **Decision**: Split the combined final self-containment audit scenario into three atomic scenarios: (a) structural completeness — goal statement, specific actions, acceptance criteria present, (b) term definition coverage — every term defined or pointer included, (c) external reference detection — no references to SKILL.md text, sibling tasks, or assumed context. Follows the precedent from GAP-7.
- **Outcome**: Split workflow-validation:2.1 into three atomic scenarios: 2.1 (structural completeness — goal statement, specific actions, acceptance criteria), 2.1.1 (term definition coverage — every term defined or pointer included), 2.1.2 (external reference detection — references to SKILL.md text, sibling tasks, or assumed context flagged). Each scenario has its own Given-When-Then block with a single verification behavior per the atomicity principle from GAP-7.

### GAP-133: tasks.yaml task groupings do not map to technical.md component structure
- **Severity**: high
- **Source**: code-tasks-critic
- **Status**: deprecated
- **Description**: The task groupings in tasks.yaml do not align with the technical.md component structure (intake convergence, normalization, dependency mapping, description generation, fsm.json finalization, validation). No task groups exist for the intake convergence pattern or the component-based pipeline ordering defined in technical.md.
- **Triage**: check-in
- **Decision**: Dismiss. tasks.yaml is an implementation plan organized by deliverable (files to create, code to change, tests to run), not by runtime component. The fsm-json group entries 1-9 map 1:1 to components via "Covers: CMP-*" annotations. Restructuring by component is inappropriate for an implementation plan — you create one fsm.json file, not a file per component. No changes needed.
- **Rationale**: tasks.yaml is organized by implementation deliverable (validation-enhancement, skill-directory, skill-md, fsm-json, behavioral-verification, verification), not by runtime component. This is the correct organizational principle for an implementation plan — tasks are grouped by the files and artifacts they produce. The "Covers: CMP-*" annotations on each fsm-json entry already provide explicit component traceability (e.g., "Covers: CMP-intake-existing", "Covers: CMP-fsm-json"), mapping each implementation task to the technical component it delivers. Restructuring tasks.yaml by component would produce an incoherent implementation plan where a single file (fsm.json) is split across multiple task groups.

### GAP-134: tasks.yaml task descriptions use undefined "the skill" references
- **Severity**: medium
- **Source**: code-tasks-critic
- **Status**: resolved
- **Description**: Task descriptions in tasks.yaml use "the skill" to reference the skill being created without defining the referent within each description. Per the self-containment principle in technical.md, references should be explicit. The pronoun "the skill" assumes context that may not be available when the description is read in isolation.
- **Triage**: check-in
- **Decision**: Replace all occurrences of "the skill" in tasks.yaml task descriptions with an explicit referent such as "the creating-taskflow-skills skill" or "the delivered skill" to eliminate ambiguity.
- **Outcome**: Replaced ambiguous "the skill" references across tasks.yaml with explicit referents: "the creating-taskflow-skills skill" in skill-md metadata context, "the existing skill" for intake-existing references, "the delivered skill" for runtime behavior references in fsm-json entries and behavioral-verification tasks. Two remaining "the skill" occurrences in quoted anti-pattern examples (line 47 and line 159) are intentionally kept as-is — they show what NOT to write in task descriptions.

### GAP-135: No explicit acknowledgment that integration verification is excluded
- **Severity**: low
- **Source**: test-tasks-critic
- **Status**: resolved
- **Description**: The behavioral verification tasks do not explicitly acknowledge that integration verification is not required per the integration.feature.md rationale. The scope exclusion is implicit rather than documented, making it unclear whether the omission is intentional or an oversight.
- **Triage**: defer-release
- **Decision**: Add a brief statement to infra.md Testing Strategy section acknowledging the integration verification exclusion and pointing to integration.feature.md for rationale. Acceptable to ship without full resolution; the integration.feature.md rationale is already documented.
- **Outcome**: Added "Integration verification exclusion" note to infra.md Testing Strategy section, explicitly stating no integration test scenarios are defined and pointing to integration.feature.md for rationale. Artifact coverage verified: infra.md now acknowledges the exclusion explicitly, and integration.feature.md already documents the full rationale.

### GAP-136: Behavioral verification tasks compress multiple scenarios into single tasks
- **Severity**: medium
- **Source**: test-tasks-critic
- **Status**: resolved
- **Description**: The behavioral verification tasks compress all scenarios from a capability into a single task. This makes it unclear whether all scenarios will be verified, how verification results are recorded per scenario, and whether partial failures (some scenarios pass, others fail) are detectable. The task structure does not provide scenario-level granularity for verification tracking.
- **Triage**: check-in
- **Decision**: Add enumerated verification checklists to each behavioral verification task description in tasks.yaml. Each checklist itemizes the Rules from the corresponding infra.md coverage table, making coverage explicit and partial failures detectable without splitting into separate tasks.
- **Outcome**: Added Rule-level verification checklists to all 5 behavioral-verification tasks in tasks.yaml. Each checklist itemizes the Rules from the corresponding infra.md coverage table: workflow-intake (4 Rules), dependency-mapping (5 Rules), self-contained-descriptions (4 Rules), skill-file-generation (3 Rules), workflow-validation (3 Rules). Checklists use [ ] checkbox format for tracking partial pass/fail at the Rule level.

### GAP-137: Confirmation gate mechanism uses undefined "equivalent" qualifier
- **Severity**: medium
- **Source**: implicit-detection
- **Status**: resolved
- **Description**: The Confirmation Gate Mechanism (technical.md) specifies that confirmation gates use "AskUserQuestion (or equivalent user prompt)" but does not define what qualifies as an "equivalent" prompt mechanism. The same phrasing appears in infra.md's verification-by-design section. An implementor writing task descriptions that instruct the agent to pause for author approval would not know whether alternative mechanisms (e.g., a plain text question without AskUserQuestion, TodoWrite with a question, or other prompting patterns) satisfy the "equivalent" qualifier. This could lead to inconsistent confirmation gate implementations across tasks, where some use AskUserQuestion and others use an undefined alternative.
- **Triage**: check-in
- **Decision**: Replace "AskUserQuestion (or equivalent user prompt)" with a functional definition: "any mechanism that blocks skill execution until the author responds." Define equivalence by behavior (execution blocking), not by tool name. Apply consistently in technical.md Confirmation Gate Mechanism and infra.md verification-by-design.
- **Outcome**: Updated technical.md Confirmation Gate Mechanism to use "any mechanism that blocks skill execution until the author responds" with behavioral equivalence definition. Updated infra.md "Verification by design" section header and body to remove tool-specific phrasing and use the functional definition consistently.

### GAP-138: No recovery fallback for total context compaction
- **Severity**: low
- **Source**: implicit-detection
- **Status**: resolved
- **Description**: The Progressive Construction Protocol's Recovery clause (technical.md, State Management section) states that if the agent loses the in-progress artifact, it should "reconstruct from the most recent complete phase output visible in conversation history." The procedure assumes that at least one complete phase output remains visible after context compaction. No guidance exists for the scenario where aggressive compaction removes all intermediate artifacts from the visible conversation history, leaving no recovery baseline.
- **Triage**: defer-release
- **Decision**: Record in functional.md Out of Scope: "Recovery fallback for total context compaction" — the scenario where aggressive compaction removes all intermediate artifacts is deferred to a future release. The phase-gate architecture makes total context loss unlikely, and session resumption is already out of scope.
- **Outcome**: Added "Recovery fallback for total context compaction" to functional.md Out of Scope section with rationale that phase-gate architecture makes total context loss unlikely.

### GAP-139: No actionable guidance for large workflow UX during dependency mapping
- **Severity**: medium
- **Source**: implicit-detection
- **Status**: resolved
- **Description**: The Known Risks section (functional.md) documents that large workflows may have poor UX during dependency mapping because "no upper workflow size limit is defined, and no scalability criteria (pagination, search, grouping) exist for presenting tasks during dependency mapping." While this is acknowledged as a risk, neither functional.md nor technical.md provides any actionable guidance for the implementor: no recommended maximum task count, no warning threshold at which the skill should advise the author about potential UX issues, and no fallback presentation strategy.
- **Triage**: check-in
- **Decision**: Define a soft threshold of 15-20 tasks where the agent warns the author that the workflow is large and suggests grouping related tasks for review during dependency mapping. No hard limit. Add guidance to CMP-dependency-map and the Known Risks entry with the threshold and recommendation.
- **Outcome**: Added soft threshold guidance (15-20 tasks) to CMP-dependency-map responsibilities in technical.md. Updated Known Risks entry in functional.md to reflect the threshold and grouping suggestion.

### GAP-140: Author not informed of ID renumbering during finalization
- **Severity**: low
- **Source**: implicit-detection
- **Status**: resolved
- **Description**: During authoring, CMP-dependency-map assigns task IDs sequentially. However, CMP-fsm-json renumbers all task IDs to topological order. The documentation does not specify whether the author is informed that the IDs they interacted with during dependency mapping and description writing will change in the final output.
- **Triage**: delegate
- **Decision**: Add to CMP-fsm-json-finalize's responsibilities: after renumbering, present the old-to-new ID mapping to the author so they are aware of the ID changes. Minimal disclosure step, no workflow disruption.
- **Outcome**: Added ID mapping disclosure step to CMP-fsm-json-finalize responsibilities in technical.md: "After renumbering, present the old-to-new ID mapping to the author so they are aware of the ID changes."

### GAP-141: No cross-artifact name consistency check between SKILL.md and fsm.json metadata
- **Severity**: medium
- **Source**: design-critic
- **Status**: resolved
- **Description**: The SKILL.md template specifies a `name` field and CMP-fsm-json writes a `metadata.fsm` block. No cross-artifact consistency requirement exists ensuring that the skill name recorded in SKILL.md matches the corresponding identifier written into the FSM JSON metadata.
- **Triage**: check-in
- **Decision**: Add a name-consistency check to CMP-final-validation's structural integrity: verify that the metadata.fsm value in fsm.json matches the SKILL.md frontmatter `name` field. This creates a new dependency — CMP-final-validation needs access to SKILL.md content.
- **Outcome**: Added "Name consistency" check to CMP-final-validation responsibilities in technical.md. Updated CMP-final-validation dependencies to note access to SKILL.md content from CMP-skill-md. Added name consistency row to Validation Scope table.

### GAP-142: Progressive construction invariant has no observable verification criterion
- **Severity**: high
- **Source**: technical-critic
- **Status**: resolved
- **Description**: The Progressive Construction Protocol specifies that "each phase updates all entries before completing" as an invariant, but no workflow-validation requirement scenario covers this invariant, and no observable criterion exists to verify it holds.
- **Triage**: check-in
- **Decision**: Add a phase-completion summary gate: after each construction phase (dependency mapping adds blockedBy, description writing adds description + activeForm), the agent presents a summary showing which entries were updated and the author confirms completeness.
- **Outcome**: Updated Progressive Construction Protocol Verification clause in technical.md to include phase-completion summary gate with author confirmation. Added workflow-validation:1.7 scenario to requirements/workflow-validation/requirements.feature.md for phase-completion summary confirmation.

### GAP-143: Cycle detection execution model unspecified (agent reasoning vs tool invocation)
- **Severity**: medium
- **Source**: technical-critic
- **Status**: resolved
- **Description**: The dependency-mapping workflow specifies cycle detection using Kahn's algorithm at the graph review step. The technical design does not specify whether cycle detection is performed by the agent reasoning over the graph, by a programmatic tool invocation, or by some other mechanism.
- **Triage**: check-in
- **Decision**: Specify tool invocation as the execution model for cycle detection. The agent invokes a programmatic tool (e.g., a Python script) to perform Kahn's algorithm deterministically, rather than reasoning through the algorithm in natural language.
- **Outcome**: Updated CMP-dependency-map and CMP-final-validation cycle detection in technical.md to specify programmatic tool invocation. Updated tasks.yaml entry 6 (dependency mapping) to include "via programmatic tool invocation" for cycle detection.

### GAP-144: Mixed normative strength in self-contained-descriptions Then clauses
- **Severity**: medium
- **Source**: requirements-critic
- **Status**: resolved
- **Description**: The self-contained-descriptions rule in the requirements file mixes normative strength within a single Then block — some clauses use SHALL and others use plain present tense.
- **Triage**: check-in
- **Decision**: Normalize all Then clauses in the self-contained-descriptions requirements to consistent SHALL phrasing. Every Then clause in a Rule's scenarios imposes a testable obligation.
- **Outcome**: Updated all Then and And clauses in requirements/self-contained-descriptions/requirements.feature.md to use consistent SHALL/SHALL NOT phrasing across all scenarios (1.1-1.5, 2.1-2.3, 3.1-3.3, 4.1-4.2).

### GAP-145: Dependency-mapping Rule 5 preamble uses non-normative present tense
- **Severity**: medium
- **Source**: requirements-critic
- **Status**: resolved
- **Description**: The dependency-mapping Rule 5 preamble uses declarative present tense to express a mutability guarantee about the task list state.
- **Triage**: check-in
- **Decision**: Rewrite the Rule 5 preamble to use SHALL: "The step list SHALL be mutable during the dependency mapping phase."
- **Outcome**: Updated Rule 5 preamble in requirements/dependency-mapping/requirements.feature.md from "The step list is mutable" to "The step list SHALL be mutable."

### GAP-146: Workflow-validation final validation Then clause references internal state
- **Severity**: medium
- **Source**: requirements-critic
- **Status**: resolved
- **Description**: The workflow-validation final validation rule's Then clause describes internal algorithm state — it references what the validation pass has internally determined — rather than specifying an observable output or behavior that a tester can verify from outside the component.
- **Triage**: check-in
- **Decision**: Rewrite the Then clause to reference the validation report presented to the author rather than internal algorithm state.
- **Outcome**: Rewrote workflow-validation:2.2 scenario Then clauses in requirements/workflow-validation/requirements.feature.md to reference observable output: "the skill SHALL present validation results indicating whether the dependency graph is acyclic" and "the skill SHALL report the set of task IDs and labels involved in cycle(s) to the author."

### GAP-147: Compound Then block in dependency-mapping graph review mixes concerns
- **Severity**: medium
- **Source**: requirements-critic
- **Status**: resolved
- **Description**: The dependency-mapping graph review rule contains a compound Then block that mixes a presentation obligation (displaying the graph to the author) with a capability assertion (the graph representation supports cycle detection).
- **Triage**: check-in
- **Decision**: Split into two independently testable scenarios: one for graph presentation to the author, and one for cycle detection readiness.
- **Outcome**: Split dependency-mapping:4.1 into two scenarios in requirements/dependency-mapping/requirements.feature.md: 4.1 (graph presentation to author for review) and 4.1.1 (dependency graph supports cycle detection via topological sort).

### GAP-148: Workflow-intake scenarios use "accepted" as internal state label
- **Severity**: low
- **Source**: requirements-critic
- **Status**: resolved
- **Description**: The workflow-intake scenarios for the no-modification path and the minor-adjustment path define "accepted" as the observable outcome. "Accepted" is an internal state label, not an observable behavior.
- **Triage**: delegate
- **Decision**: Replace "accepted" in scenario outcomes with the observable behavior: "the skill advances to the normalization phase with the contributed material" or "the skill presents the step list for normalization."
- **Outcome**: Updated workflow-intake:2.3 and 3.1 Then clauses in requirements/workflow-intake/requirements.feature.md to use observable behaviors: "the skill SHALL present the step list for normalization without modification" and "the skill SHALL advance to the normalization phase with the contributed material."

### GAP-149: No scenario for cycle introduced by modification during dependency mapping review
- **Severity**: medium
- **Source**: requirements-coverage-critic
- **Status**: resolved
- **Description**: The requirements define scenarios for cycles introduced during the initial graph construction, but no scenario covers the case where a cycle is introduced by a task modification made during the dependency mapping graph review step.
- **Triage**: check-in
- **Decision**: Add a new scenario under dependency-mapping:5 (step list modifications): "Author modifies a dependency during the graph review step, introducing a circular dependency. The skill detects the cycle during re-validation and reports the involved tasks before accepting the modification."
- **Outcome**: Added dependency-mapping:5.4 scenario to requirements/dependency-mapping/requirements.feature.md covering modification-introduced cycles during graph review with re-validation and cycle reporting.

### GAP-150: Brainstorming Gap Taxonomy implies intake-time detection
- **Severity**: medium
- **Source**: validation-critic
- **Status**: resolved
- **Description**: The Brainstorming Gap Taxonomy (functional.md) defines depth and consistency as gap categories alongside coverage and clarity. No workflow-intake rule addresses depth gaps or consistency gaps. The taxonomy describes a classification the system is expected to support, but the intake requirements and verification infrastructure only demonstrably cover a subset of the defined categories.
- **Triage**: check-in
- **Decision**: Clarify that the Brainstorming Gap Taxonomy is a post-hoc evaluation framework, not an intake-time detection mechanism. Add clarifying language to functional.md's taxonomy section.
- **Outcome**: Added clarifying preamble to functional.md Brainstorming Gap Taxonomy section explaining it is a post-hoc evaluation framework used by verifiers, not an intake-time detection mechanism.

### GAP-151: No coverage row for SKILL.md self-validation path
- **Severity**: low
- **Source**: verification-critic
- **Status**: resolved
- **Description**: The infra.md coverage table for skill-file-generation does not include a row for the SKILL.md self-validation and re-validation scenario.
- **Triage**: delegate
- **Decision**: Add a coverage row to infra.md's skill-file-generation table for Rule 2 (self-validation).
- **Outcome**: Added "Rule 2 (self-validation): SKILL.md self-validation" coverage row to infra.md skill-file-generation table with verification approach for triggering and verifying self-validation failure and re-validation.

### GAP-152: No setup procedure for empty-sources precondition in verification
- **Severity**: medium
- **Source**: verification-critic
- **Status**: resolved
- **Description**: The workflow-intake requirements include a scenario where all brainstorming sources are empty. The infra.md verification approach does not specify how to reproducibly establish this precondition.
- **Triage**: check-in
- **Decision**: Add an explicit setup procedure to infra.md for the empty-sources precondition.
- **Outcome**: Added empty-sources setup procedure to infra.md workflow-intake Rule 4 verification approach: start fresh session, invoke skill, provide no input to either intake source, brainstorming receives zero prior material.

### GAP-153: No boundary verification example for single-task dependency prompting
- **Severity**: low
- **Source**: verification-critic
- **Status**: resolved
- **Description**: infra.md provides no boundary verification example for what "relationship prompting with all existing tasks" looks like at the boundary where the workflow contains exactly one existing task before the addition.
- **Triage**: delegate
- **Decision**: Add a boundary verification example to infra.md for single-task prompting.
- **Outcome**: Added single-task boundary example to infra.md dependency-mapping Rule 5 verification approach with pass/fail criteria for referencing the existing task by name.

### GAP-154: No coverage row for single-task workflow boundary case
- **Severity**: medium
- **Source**: design-for-test-critic
- **Status**: resolved
- **Description**: The infra.md coverage table for dependency-mapping does not include a row for the single-task boundary case (Rule 6).
- **Triage**: check-in
- **Decision**: Add a coverage row to infra.md's dependency-mapping table for Rule 6 (single-task workflows).
- **Outcome**: Added "Rule 6: Single-task workflows" coverage row to infra.md dependency-mapping table with verification approach for empty dependency graph and immediate progression.

### GAP-155: File-write mechanism unspecified for CMP-skill-md and CMP-fsm-json
- **Severity**: medium
- **Source**: logic-critic
- **Status**: resolved
- **Description**: The technical design describes CMP-skill-md and CMP-fsm-json as components that produce SKILL.md and the FSM JSON file respectively, but the mechanism by which these components write files to the filesystem is implicit.
- **Triage**: check-in
- **Decision**: Specify the Write tool (Claude Code's native file creation tool) as the file-write mechanism in CMP-skill-md and CMP-fsm-json-finalize component responsibilities.
- **Outcome**: Added "Write the SKILL.md file to disk using the Write tool" to CMP-skill-md responsibilities and "Write the fsm.json file to disk using the Write tool" to CMP-fsm-json-finalize responsibilities in technical.md.

### GAP-156: No CI/CD exclusion acknowledgment for behavioral verification
- **Severity**: low
- **Source**: test-tasks-critic
- **Status**: resolved
- **Description**: The infra.md Testing Strategy section does not acknowledge the absence of automated CI/CD integration for behavioral verification.
- **Triage**: delegate
- **Decision**: Add an explicit acknowledgment to infra.md Testing Strategy: "Behavioral verification is manual by design — no automated CI/CD integration is defined for behavioral tests because the outputs are agent actions guided by prose descriptions, not deterministic function outputs."
- **Outcome**: Added "CI/CD exclusion" paragraph to infra.md Testing Strategy section explicitly stating behavioral verification is manual by design with no automated CI/CD integration.

### GAP-157: Behavioral verification tasks lack setup preamble
- **Severity**: high
- **Source**: test-infra-critic
- **Status**: resolved
- **Description**: The behavioral verification tasks in the implementation plan do not include or reference a setup task that establishes the verification environment prerequisites described in infra.md.
- **Triage**: check-in
- **Decision**: Add a setup preamble task as the first entry in the behavioral-verification group of tasks.yaml.
- **Outcome**: Added setup preamble task as the first entry in the behavioral-verification group of tasks.yaml with concrete steps: verify FSM plugin installation, verify skill deployment, start fresh session, invoke skill, verify hydration succeeds with 9 task files.

### GAP-158: Testing strategy contradicts task plan on pytest test additions
- **Severity**: medium
- **Source**: test-infra-critic
- **Status**: resolved
- **Description**: The infra.md Testing Strategy states that no new pytest tests are added as part of this change. The validation-enhancement tasks in the implementation plan add new pytest tests. The strategy claim and the task plan are contradictory.
- **Triage**: check-in
- **Decision**: Update infra.md Testing Strategy to distinguish behavioral from structural tests.
- **Outcome**: Updated infra.md Testing Strategy from "No new pytest tests are added" to "No new behavioral verification pytest tests are added. Structural validation tests in the validation-enhancement group extend the existing hydration pipeline's field checking — these are code changes to validate_fsm_tasks, not behavioral tests."

### GAP-159: OBJ-requirements-coverage describes process goal, not verifiable state
- **Severity**: low
- **Source**: test-infra-critic
- **Status**: resolved
- **Description**: The OBJ-requirements-coverage objective in infra.md describes a process goal rather than a measurable operational outcome.
- **Triage**: delegate
- **Decision**: Reframe OBJ-requirements-coverage from a process goal to a verifiable state: "Each requirement rule in the requirements files has at least one corresponding scenario."
- **Outcome**: Updated OBJ-requirements-coverage in infra.md from "Each requirement capability has a documented verification approach" to "Each requirement rule in the requirements files has at least one corresponding scenario with a documented verification approach."

### GAP-160: File production capability not reflected in change functional boundary
- **Severity**: low
- **Source**: functional-consistency-critic
- **Status**: resolved
- **Description**: The skill-file-generation capability introduces filesystem write operations that expand the FSM plugin's scope beyond what project-level functional documentation describes for the plugin.
- **Triage**: delegate
- **Decision**: Add a delta note in the change's functional.md documenting that this change expands the FSM plugin's capability boundary to include authoring-time file production.
- **Outcome**: Added "Capability boundary expansion" delta note to functional.md What Changes section documenting that this change adds authoring-time file production (SKILL.md + fsm.json generation), with note that project-level functional description will be updated at merge time.

### GAP-161: Change-local CMP-fsm-json identifier collides with project-level component
- **Severity**: medium
- **Source**: technical-consistency-critic
- **Status**: resolved
- **Description**: This change defines a component using the identifier CMP-fsm-json. The same identifier is used by an existing project-level component in the technical architecture.
- **Triage**: check-in
- **Decision**: Rename the change-local component from CMP-fsm-json to CMP-fsm-json-finalize. This accurately describes the component's role (finalization of the progressively-built artifact, not full generation) and disambiguates it from the project-level CMP-fsm-json. All references in the change's specs must be updated.
- **Outcome**: Renamed CMP-fsm-json to CMP-fsm-json-finalize across all change spec files: technical.md (component definition, architecture section, data flow table, data transformation table, dependencies), tasks.yaml (entry 8 Covers annotation). Description fields in gaps.md and resolved.md entries are immutable history and were not renamed.

### GAP-162: Project-level no-cycle-detection Y-statement reads as blanket constraint
- **Severity**: medium
- **Source**: technical-consistency-critic
- **Status**: resolved
- **Description**: The project-level technical documentation includes a no-cycle-detection Y-statement scoped to runtime behavior, but the statement reads as a blanket constraint. This change adds authoring-time cycle detection as a new capability. The project Y-statement does not acknowledge the scope boundary between runtime and authoring-time.
- **Triage**: check-in
- **Decision**: Update the project-level Y-statement in project technical.md now to add a "runtime only" scope qualifier, clarifying that the no-cycle-detection decision applies to runtime execution, not authoring-time tooling.
- **Outcome**: Updated the no-cycle-detection Y-statement in openspec/finite-skill-machine/technical.md to add "at runtime" scope qualifier and explicit note that authoring-time tooling may perform cycle detection during workflow construction.

### GAP-163: Skill discoverability mechanism undefined after file generation
- **Severity**: medium
- **Source**: implementation-critic
- **Status**: resolved
- **Description**: No component in this change specifies what the FSM plugin requires to discover and register a newly generated skill beyond the file being placed in the expected directory structure.
- **Triage**: check-in
- **Decision**: Document that the FSM plugin discovers skills via filesystem convention: skills placed in `plugins/<plugin>/skills/<skill>/` with both SKILL.md and fsm.json are automatically discovered by Claude Code's plugin loading mechanism. No registration steps, index updates, manifest changes, or reload signals are required.
- **Outcome**: Added "Skill discoverability" technical notes to both CMP-skill-md and CMP-fsm-json-finalize component descriptions in technical.md documenting the filesystem convention for automatic discovery by Claude Code's plugin loading mechanism.

### GAP-164: Tasks added during dependency mapping bypass intake quality criteria
- **Severity**: medium
- **Source**: integration-coverage-critic
- **Status**: resolved
- **Description**: A task added during dependency mapping (per the dependency-mapping task-addition rule) bypasses the intake validation gate entirely. The label and initial description provided at the dependency-mapping step are never evaluated against intake-phase quality criteria for specificity, actionability, and scope.
- **Triage**: check-in
- **Decision**: Add a lightweight quality check during dependency-mapping task addition: when the author provides a new task's label and description, the agent applies intake-quality criteria (specificity, actionability, scope) before adding it to the graph. Update CMP-dependency-map responsibilities and the dependency-mapping:5.2 scenario.
- **Outcome**: Added lightweight quality check against intake-quality criteria to CMP-dependency-map responsibilities in technical.md for task additions during dependency mapping. Updated dependency-mapping:5.2 scenario in requirements/dependency-mapping/requirements.feature.md to include quality check step before task addition.

### GAP-165: Lightweight quality check undefined for dependency-mapping task additions
- **Severity**: Low
- **Source**: implicit-detection
- **Status**: resolved
- **Description**: CMP-dependency-map responsibilities and dependency-mapping:5.2 require a "lightweight quality check against intake-quality criteria (specificity, actionability, scope)" when a task is added during dependency mapping, but do not define what makes the check "lightweight" versus the full intake evaluation performed by CMP-intake-written. An implementor cannot determine which checks to abbreviate or omit relative to the full intake path.
- **Category**: delegate
- **Decision**: Define "lightweight quality check" by enumeration in CMP-dependency-map and dependency-mapping:5.2. The lightweight check verifies: label is present and non-empty, description is non-empty and identifies distinct work (specificity), and the task describes a concrete action (actionability). It omits: splitting guidance for overly broad steps, iterative prompting for clarification, and full scope evaluation.
- **Outcome**: Enumerated the lightweight quality check criteria in CMP-dependency-map responsibilities in technical.md (3 checks performed, 3 checks omitted). Updated dependency-mapping:5.2 scenario to specify the enumerated criteria and explicitly state what the lightweight check omits.

### GAP-166: Cycle detection tool invocation uses "e.g." without commitment
- **Severity**: Medium
- **Source**: implicit-detection
- **Status**: resolved
- **Description**: CMP-dependency-map and CMP-final-validation both specify cycle detection "via programmatic tool invocation (e.g., a Python script)" but use "e.g." both times without committing to a specific invocation method. An implementor must decide the concrete tool mechanism (inline Python via Bash tool, standalone script file, or another approach) with no guidance on which to use or where to place a script if one is created.
- **Category**: check-in
- **Decision**: Remove "e.g." from both occurrences — commit to "a Python script." Python is the natural choice: hydrate-tasks.py is already Python, Python has built-in data structures for graph algorithms, and Kahn's algorithm is straightforward to implement. Whether inline or standalone is left to the implementor.
- **Outcome**: Changed "via programmatic tool invocation (e.g., a Python script)" to "via programmatic tool invocation (a Python script)" in CMP-dependency-map and CMP-final-validation in technical.md. Also updated the matching text in tasks.yaml entry 6.

### GAP-167: Minor formatting adjustments boundary undefined
- **Severity**: Low
- **Source**: implicit-detection
- **Status**: resolved
- **Description**: CMP-intake-written responsibilities and workflow-intake:3.1 specify accepting well-structured descriptions "with at most minor formatting adjustments" but do not define the boundary between minor formatting adjustments and substantive content changes. An implementor cannot distinguish permissible silent adjustments from changes that require author review.
- **Category**: defer-release
- **Decision**: Add to functional.md Out of Scope: precise boundary between minor formatting adjustments and substantive content changes during written step intake is deferred to implementation judgment.
- **Outcome**: Added Out of Scope entry to functional.md deferring the minor formatting vs. substantive content boundary to implementation judgment.

### GAP-168: SKILL.md body content structure undefined
- **Severity**: Low
- **Source**: implicit-detection
- **Status**: resolved
- **Description**: CMP-skill-md responsibilities and skill-file-generation Rule 1 specify SKILL.md frontmatter fields precisely but define body content only as "describing workflow steps in terms the skill's end user understands" in "author-facing language." No template, section structure, or content guidelines exist for the body beyond avoiding internal identifiers. An implementor must invent the body structure without reference material.
- **Category**: defer-release
- **Decision**: Add to functional.md Out of Scope: SKILL.md body content template or section structure guidelines are deferred — implementor determines body structure based on the existing constraint of author-facing language without internal identifiers.
- **Outcome**: Added Out of Scope entry to functional.md deferring SKILL.md body content template to implementor judgment.

### GAP-169: Task dependency diagram missing SKILL.md to final-validation edge
- **Severity**: Medium
- **Source**: design-critic
- **Status**: resolved
- **Description**: The task dependency graph mermaid diagram in technical.md does not include an edge from the SKILL.md component to the final validation component. GAP-141 resolved the name-consistency check by adding CMP-final-validation's dependency on SKILL.md content to the component text, but the authoritative diagram was not updated to reflect this fan-in dependency. The diagram and the component description are now inconsistent.
- **Category**: delegate
- **Decision**: Add a dashed edge `SM -.->|reads output| FV` to the mermaid diagram in technical.md. The dashed edge accurately represents a data-read dependency (name-consistency check reads SKILL.md from disk) without implying a blocking task dependency. CMP-skill-md completes independently; CMP-final-validation reads its output from disk.
- **Outcome**: Added dashed edge `SM -.->|reads output| FV` to the mermaid diagram in technical.md. Updated the CMP-skill-md and CMP-final-validation bullet points below the diagram to describe the data-read dependency relationship.

### GAP-170: Progressive Construction Protocol scale threshold undefined
- **Severity**: Medium
- **Source**: technical-critic
- **Status**: resolved
- **Description**: The Progressive Construction Protocol in technical.md defines no feasibility boundary for the protocol itself. The protocol maintains a JSON artifact in conversation context across all construction phases, and for larger workflows this artifact grows with every phase. No documented scale threshold identifies when the progressively maintained artifact itself creates context pressure that undermines the protocol's purpose.
- **Category**: defer-release
- **Decision**: Add to functional.md Out of Scope: scale threshold for the Progressive Construction Protocol's in-context artifact growth is deferred — real-world usage will reveal actual limits before a formal boundary is needed.
- **Outcome**: Added Out of Scope entry to functional.md deferring the Progressive Construction Protocol scale threshold to real-world usage feedback.

### GAP-171: Automatic graph updates vs prompted interaction conflict
- **Severity**: Medium
- **Source**: implementation-critic
- **Status**: resolved
- **Description**: The dependency-mapping capability description in functional.md states the skill performs automatic graph updates when new tasks are added. The CMP-dependency-map component in technical.md specifies that adding new dependency relationships requires prompted author interaction. The functional claim of automatic updates conflicts with the technical requirement of author-prompted interaction for new relationships.
- **Category**: check-in
- **Decision**: Two-phase clarification in functional.md. Update the dependency-mapping capability to distinguish automatic structural maintenance (node addition, dangling reference cleanup, rename propagation) from prompted author interaction for new dependency relationships. Both documents were partially correct — the functional description should clarify this nuance.
- **Outcome**: Updated the dependency-mapping capability in functional.md to distinguish automatic structural maintenance (node addition, dangling reference cleanup, rename propagation) from prompted author interaction for new dependency relationships.

### GAP-172: Internal component identifiers in requirement scenarios
- **Severity**: Medium
- **Source**: requirements-critic
- **Status**: resolved
- **Description**: Internal technical component identifiers appear in requirement scenario bodies. The skill-file-generation requirements reference a component identifier by name in a Rule body, and the workflow-intake requirements reference another component identifier in a Then clause. Requirement scenarios should describe observable author-facing behavior; exposing internal component names at the requirements layer creates coupling between the requirements and the technical design's naming choices.
- **Category**: delegate
- **Decision**: Rewrite affected scenarios to use purpose-based language. Replace "CMP-skill-md" with "the skill's documentation generation step" in skill-file-generation:2 Rule header and 2.1 scenario. Replace "CMP-normalize" with "the normalization step" in workflow-intake:1.4.
- **Outcome**: Replaced "CMP-skill-md" with "the skill's documentation generation step" in skill-file-generation:2 Rule header and 2.1 scenario. Replaced "CMP-normalize" with "the normalization step" in workflow-intake:1.4 Then clause.

### GAP-173: Inconsistent actor terminology in workflow-validation:1.7
- **Severity**: Low
- **Source**: requirements-critic
- **Status**: resolved
- **Description**: The phase-completion summary scenario in workflow-validation uses "agent" as the subject in one Then clause but "skill" in all other Then clauses within the same scenario. All other requirement scenarios consistently use "the skill" as the subject of Then clauses. This inconsistency creates ambiguity about whether the two subjects refer to different actors.
- **Category**: delegate
- **Decision**: Change "the agent" to "the skill" in workflow-validation:1.7 Then clause for consistency with the established convention across all requirement scenarios.
- **Outcome**: Changed "the agent" to "the skill" in the Given and Then clauses of workflow-validation:1.7 for consistency with all other requirement scenarios.

### GAP-174: Task definition serialization format unspecified
- **Severity**: Medium
- **Source**: requirements-coverage-critic
- **Status**: resolved
- **Description**: No requirement scenario specifies that the task definition output must be in JSON format. The skill-file-generation requirements list required fields but do not pin the serialization format. An implementor could produce the task definition as YAML, TOML, or any other structured format and satisfy all field-presence scenarios without producing valid JSON.
- **Category**: delegate
- **Decision**: Add a new scenario under skill-file-generation Rule 3 requiring the task definition to be serialized as a JSON array. JSON is the format specified by the INT-fsm-json schema and consumed by hydrate-tasks.py.
- **Outcome**: Added scenario @skill-file-generation:3.4 requiring JSON array serialization. Renumbered existing 3.4 (display-friendly names) to 3.5. Updated tasks.yaml coverage annotations to reflect renumbering.

### GAP-175: Verification setup incompatible with directory-state scenarios
- **Severity**: Medium
- **Source**: verification-critic
- **Status**: resolved
- **Description**: The verification environment setup procedure documented in technical.md always creates the target skill directory before verification begins. This makes it impossible to verify the directory-creation scenario (when the target directory does not exist) and the collision-detection scenario (when a pre-existing skill directory is present) in the defined environment. No documented procedure exists for establishing either precondition in a reproducible way for verification purposes.
- **Category**: check-in
- **Decision**: Restructure verification setup into base + scenario-specific preconditions. Base setup verifies FSM plugin presence and skill deployment but does not manipulate the target skill directory. Add documented scenario-specific setup steps: remove target directory for directory-creation testing, pre-populate target directory for collision-detection testing.
- **Outcome**: Restructured infra.md Verification Environment Setup into "Base Setup Steps" (applies to all scenarios) and "Scenario-Specific Setup" subsection documenting directory-state preconditions for skill-file-generation:4.3 and 4.4. Updated the skill-file-generation behavioral verification task in tasks.yaml to reference scenario-specific setup from infra.md.

### GAP-176: Name-consistency check has no requirement coverage
- **Severity**: High
- **Source**: logic-critic
- **Status**: resolved
- **Description**: CMP-final-validation defines four checks in technical.md: cycle detection, self-containment audit, structural integrity, and name consistency. The workflow-validation requirements include scenarios covering the first three checks but contain no scenario for the name-consistency check (verifying that the metadata.fsm value in fsm.json matches the SKILL.md frontmatter name field). The fourth check has no requirement coverage.
- **Category**: check-in
- **Decision**: Add a dedicated fail scenario @workflow-validation:2.12 for the name-consistency check. The scenario covers the case where metadata.fsm in fsm.json does not match the SKILL.md frontmatter name field, resulting in a validation failure with a specific report.
- **Outcome**: Added scenario @workflow-validation:2.12 for the name-consistency check. Updated CMP-final-validation description from "3 cross-cutting checks" to "4 cross-cutting checks" in technical.md (component description and data flow table). Updated tasks.yaml entry 9 to cover 4 checks and reference 2.12. Updated infra.md workflow-validation coverage table Rule 2 to mention name-consistency. Updated integration.feature.md cross-artifact dependency description to reference the name-consistency check.

### GAP-177: No explicit dependency between skill-directory and skill-md groups
- **Severity**: Low
- **Source**: code-tasks-critic
- **Status**: resolved
- **Description**: In tasks.yaml, the skill-directory group and the skill-md group are ordered implicitly by document position only. No explicit dependency declaration exists between these groups in the task schema, so an implementor could execute them in any order without violating any stated constraint. The schema has no ordering mechanism beyond document sequence.
- **Category**: delegate
- **Decision**: Add a YAML comment above skill-md group documenting that it depends on skill-directory completing first (SKILL.md is placed in the directory that skill-directory creates).
- **Outcome**: Added YAML comment `# Depends on skill-directory completing first (SKILL.md placed in created directory)` above the skill-md group in tasks.yaml.

### GAP-178: Cross-group dependency in tasks.yaml not explicitly declared
- **Severity**: Medium
- **Source**: code-tasks-critic
- **Status**: resolved
- **Description**: The behavioral-verification group in tasks.yaml depends on the validation-enhancement, skill-directory, skill-md, and fsm-json groups completing first. No explicit cross-group dependency declaration captures this ordering constraint, leaving the dependency implicit and unenforceable through the task schema.
- **Category**: check-in
- **Decision**: Accept document position as the ordering mechanism. tasks.yaml groups execute in document order by convention. No schema change needed — the implicit ordering is the design.
- **Outcome**: No artifact changes. Document position is the accepted ordering mechanism for tasks.yaml groups.

### GAP-179: SKILL.md body coverage not verified by any task
- **Severity**: Low
- **Source**: code-tasks-critic
- **Status**: resolved
- **Description**: The skill-md group tasks in tasks.yaml cover SKILL.md frontmatter but do not verify that the SKILL.md body addresses the collision detection and name normalization behaviors defined in the CMP-skill-md component responsibilities. The behavioral-verification group checks frontmatter structure only; body coverage of these behaviors is not verified by any task.
- **Category**: defer-release
- **Decision**: Add to functional.md Out of Scope: verification of SKILL.md body content completeness — frontmatter structure is verified; body coverage of all component behaviors deferred to implementation judgment.
- **Outcome**: Added Out of Scope entry to functional.md deferring SKILL.md body content completeness verification to implementation judgment.

### GAP-180: Integration feature missing SKILL.md fan-in for CMP-final-validation
- **Severity**: Low
- **Source**: integration-coverage-critic
- **Status**: resolved
- **Description**: The integration.feature.md states that CMP-final-validation fans in from CMP-fsm-json-finalize only. GAP-141 resolved the name-consistency check by adding CMP-final-validation's dependency on SKILL.md content from CMP-skill-md. The integration.feature.md cross-artifact dependency description was not updated to reflect this new fan-in relationship.
- **Category**: delegate
- **Decision**: Update integration.feature.md to reflect that CMP-final-validation also reads SKILL.md content produced by CMP-skill-md for the name-consistency check. The statement that CMP-final-validation fans in from CMP-fsm-json-finalize "only" is no longer accurate.
- **Outcome**: Updated integration.feature.md cross-artifact dependency description to reflect CMP-final-validation's data-read dependency on SKILL.md content for the name-consistency check, including both the blocking task dependency (CMP-fsm-json-finalize) and the data-read dependency (CMP-skill-md).

### GAP-181: Authoring-time file writes may trigger runtime protection guard
- **Severity**: Low
- **Source**: functional-consistency-critic
- **Status**: resolved
- **Description**: The authoring-time file write path places SKILL.md and fsm.json under the runtime skill discovery directory. The FSM plugin's runtime active-work-protection guard monitors this directory for in-progress tasks. A partially written fsm.json produced during an authoring session could be detected by the guard, potentially triggering unexpected abort or protection behavior before the file is complete.
- **Category**: defer-release
- **Decision**: Add to functional.md Known Risks: authoring-time file writes may trigger runtime active-work-protection guard. Phase-gate architecture makes this unlikely — files are written near end of the workflow after validation passes.
- **Outcome**: Added Known Risks entry to functional.md documenting the potential for authoring-time file writes to trigger the runtime active-work-protection guard, with mitigation note about phase-gate architecture.

### GAP-182: Data Transformation table column header semantically incorrect
- **Severity**: Low
- **Source**: design-critic
- **Status**: resolved
- **Description**: The data transformation table in technical.md uses "Fields added" as the column header for all component rows. The CMP-descriptions row describes replacement semantics (replacing the normalize-phase brief description with the full self-contained instruction), not addition. GAP-97 updated the cell content to say "replaces description" but the column header itself still reads "Fields added," which is semantically incorrect for the replacement case. Similar concern to resolved GAP-97, which updated cell content but not the header.
- **Category**: delegate
- **Decision**: Change the column header from "Fields added" to "Fields added/modified" in the Data Transformation table in technical.md. This accurately covers both addition semantics (most rows) and replacement semantics (CMP-descriptions row).
- **Outcome**: Changed the column header from "Fields added" to "Fields added/modified" in the Data Transformation table in technical.md.

### GAP-183: No intake-phase check for trivially small step descriptions
- **Severity**: Medium
- **Source**: requirements-coverage-critic
- **Status**: resolved
- **Description**: No requirement scenario addresses evaluation of trivially small step descriptions at the intake phase. The self-contained-descriptions requirements cover overly small descriptions during the description writing phase, but a step that is too small to be meaningful could be accepted through the intake and normalization phases without any quality check. Intake-phase evaluation for minimum meaningful size is not covered. Similar concern to resolved GAP-66, which defined the "overly small" threshold at the description writing phase rather than the intake phase.
- **Category**: check-in
- **Decision**: Rely on existing description-phase check — no intake change needed. At intake, steps are labels + brief descriptions, not self-contained instructions. The "overly small" threshold is defined by the self-containment checklist (can you populate all 4 items?), which is a description-writing concern. A step like "Validate config" is appropriately sized for intake but correctly flagged during description writing. Intake already has specificity criteria (workflow-intake:3.2) that catch truly meaningless steps.
- **Outcome**: No artifact changes. The existing description-phase check (self-containment checklist) and intake-phase specificity criteria (workflow-intake:3.2) together cover the concern without requiring a new intake-phase size check.

### GAP-184: ID renumbering transformation has no requirement coverage
- **Severity**: Medium
- **Source**: logic-critic
- **Status**: resolved
- **Description**: No requirement scenario covers the ID renumbering transformation that CMP-fsm-json-finalize performs at the end of the authoring workflow. The renumbering strategy (next-sequential during authoring, topological order at finalization) and the old-to-new ID mapping disclosure are documented as technical decisions, but no requirement scenario specifies the transformation itself, author notification, or post-renumber verification that all blockedBy references are consistent. Similar concern to resolved GAP-96 and GAP-140, which established the technical design and author disclosure decisions without adding requirement coverage.
- **Category**: delegate
- **Decision**: Add a scenario under skill-file-generation Rule 3 covering the ID renumbering transformation and author notification. The scenario specifies that task IDs are renumbered to topological order at finalization with an old-to-new mapping presented to the author. Post-renumber reference consistency is already covered by structural integrity (workflow-validation:2.11 checks blockedBy resolution).
- **Outcome**: Added scenario @skill-file-generation:3.5 for the ID renumbering transformation and author notification. Renumbered existing 3.5 (display-friendly names, previously 3.4) to 3.6. Updated tasks.yaml coverage annotations to reflect renumbering.
