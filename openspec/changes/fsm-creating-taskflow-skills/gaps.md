# Gaps

<!-- GAP TEMPLATE - Fields by workflow stage:
CRITIQUE adds: ID, Severity, Source, Description
RESOLVE adds: Category, Decision

New gaps from critique should NOT have Category or Decision fields.

See tokamak:managing-spec-gaps for gap creation quality and category semantics.
-->

### GAP-185: CMP-fsm-json-finalize assumes CMP-skill-md has created the target directory without a blocking dependency
- **Severity**: low
- **Source**: implicit-detection
- **Description**: CMP-fsm-json-finalize's responsibilities state "directory creation and collision detection are handled by CMP-skill-md" (technical.md, CMP-fsm-json-finalize component). However, no blocking task dependency exists from CMP-fsm-json-finalize on CMP-skill-md — the dependency graph shows CMP-skill-md branching off CMP-normalize independently while CMP-fsm-json-finalize is at the end of the DM->DE->FJ linear chain. CMP-fsm-json-finalize's task description (tasks.yaml entry 8) says "guide the author on file placement alongside the delivered skill's documentation file" without any fallback for directory creation if the target directory does not yet exist. While the typical execution path makes this unlikely (CMP-skill-md becomes available much earlier than CMP-fsm-json-finalize), the specification's self-containment principle requires each task to stand alone — CMP-fsm-json-finalize's description relies on CMP-skill-md having already run, which is a cross-task assumption without enforcement.

### GAP-186: Recovery path for progressive construction loss has no testability specification
- **Severity**: medium
- **Source**: feasibility-critic
- **Description**: The Progressive Construction Protocol (technical.md, State Management) specifies a recovery procedure for when the in-context artifact is lost: reconstruct from the most recent complete phase output visible in conversation history. GAP-127 and GAP-138 established this recovery path, but neither the requirements nor infra.md specifies how to verify that recovery produces a correct reconstructed artifact. There is no scenario defining what observable behavior the skill must produce when recovery is triggered, no infra.md coverage entry for the recovery path, and no boundary example for what constitutes a successful versus failed reconstruction.

### GAP-187: dependency-mapping:4.1.1 Then clause references internal graph property rather than observable outcome
- **Severity**: medium
- **Source**: testability-critic
- **Description**: The scenario at dependency-mapping:4.1.1 specifies that "the dependency graph SHALL support cycle detection via topological sort" and "the skill SHALL be able to determine whether the graph is acyclic before proceeding." These Then clauses describe an internal property of the graph representation, not an observable outcome the author or verifier can confirm. The scenario cannot be verified independently of executing cycle detection — there is no author-visible output or artifact that demonstrates the graph supports this operation. GAP-147 split the compound scenario from dependency-mapping:4.1 but the resulting 4.1.1 retained implementation-describing language rather than outcome-describing language.

### GAP-188: workflow-validation:1.7 places SHALL obligation on the author rather than the skill
- **Severity**: medium
- **Source**: requirements-critic
- **Description**: The phase-completion summary scenario in workflow-validation:1.7 contains the Then clause "the author SHALL confirm completeness before the next phase begins." In MDG requirement format, SHALL is a normative obligation placed on the subject — "author SHALL confirm" makes the obligation an author requirement rather than a skill requirement. All other requirement Then clauses in the spec use "the skill SHALL" as the subject of normative obligation. GAP-173 corrected actor terminology inconsistency in this scenario but did not address the normative direction of the obligation. The scenario should specify what the skill SHALL do to enforce the confirmation gate, not what the author is obligated to do.

### GAP-189: No scenario for multi-task workflow where all tasks are fully independent
- **Severity**: medium
- **Source**: requirements-coverage-critic
- **Description**: GAP-124 added dependency-mapping Rule 6 covering the single-task boundary case (empty dependency graph, trivially no relationships). A multi-task workflow where no inter-task dependencies exist at all is a distinct boundary case: multiple tasks, all with empty blockedBy arrays, forming a fully disconnected graph. No scenario covers the skill's behavior when presenting a multi-task dependency summary where every task is independent — the confirmation flow, graph presentation, and the author's ability to verify a fully parallel workflow are unspecified. The existing parallel encoding scenarios (Rules 1-2) cover subsets of tasks being parallel within a larger workflow, not the all-parallel boundary.

### GAP-190: No requirement scenario for the large-workflow UX threshold
- **Severity**: medium
- **Source**: requirements-coverage-critic
- **Description**: GAP-139 added a soft threshold of 15-20 tasks to CMP-dependency-map's responsibilities in technical.md, specifying that the agent warns the author and suggests grouping related tasks for review. This design decision has no corresponding requirement scenario in the dependency-mapping requirements. No scenario specifies the observable behavior when a workflow crosses the threshold — what the warning says, when it appears, or how the author responds. The technical decision is documented but lacks requirements-level coverage.

### GAP-191: infra.md workflow-validation Rule 1 coverage does not include phase-completion summary verification
- **Severity**: medium
- **Source**: verification-critic, design-for-test-critic
- **Description**: The workflow-validation:1.7 scenario specifies a phase-completion summary gate that the skill must present after each construction phase before advancing. The infra.md coverage table for workflow-validation Rule 1 describes incremental phase validation but does not include verification of the phase-completion summary — no entry specifies what constitutes a passing or failing summary, what content the summary must contain, or how a verifier confirms the blocking behavior. GAP-184 added requirement coverage for the related ID renumbering transformation but did not address summary gate verification in infra.md.

### GAP-192: infra.md has no pass/fail boundary definition for the dependency-mapping lightweight quality check
- **Severity**: low
- **Source**: verification-critic, design-for-test-critic
- **Description**: The dependency-mapping:5.2 scenario and CMP-dependency-map responsibilities specify a lightweight quality check applied to tasks added during dependency mapping, verifying label presence, description specificity, and actionability. The infra.md dependency-mapping coverage table for Rule 5 describes task addition verification but provides no boundary examples for the lightweight check — no concrete pass/fail cases illustrate what counts as "sufficient specificity" or "concrete action" for a newly-added task during dependency mapping, distinct from the full intake quality criteria.

### GAP-193: tasks.yaml entry 8 does not include presenting the old-to-new ID mapping to the author
- **Severity**: low
- **Source**: test-tasks-critic
- **Description**: CMP-fsm-json-finalize's responsibilities (technical.md) include presenting the old-to-new ID mapping to the author after renumbering task IDs to topological order. Tasks.yaml entry 8 covers renumbering and blockedBy reference updates but its description does not instruct the implementor to present the ID mapping to the author. GAP-140 added this disclosure step to the component responsibilities but the corresponding tasks.yaml entry was not updated to reflect it.

### GAP-194: tasks.yaml entry 9 does not specify how to retrieve SKILL.md content from disk for name-consistency check
- **Severity**: medium
- **Source**: test-tasks-critic
- **Description**: CMP-final-validation's name-consistency check (technical.md) requires reading the SKILL.md frontmatter name field from the file written to disk by CMP-skill-md. Tasks.yaml entry 9 covers the name-consistency check as check 4 but does not specify the on-disk retrieval instruction — how the agent performing the final validation task obtains the SKILL.md content (file path, read mechanism) to compare against the metadata.fsm value. GAP-141 and GAP-176 added the check to the component description and the requirement scenario, but the tasks.yaml task description omits the retrieval instruction that makes the check executable.

### GAP-195: Name-consistency check scope is asymmetric — directory name not included in 3-way consistency
- **Severity**: low
- **Source**: logic-critic
- **Description**: GAP-141 established a 2-field consistency check: metadata.fsm in fsm.json must match the SKILL.md frontmatter name field. However, both values are derived from the same author-provided skill name that also determines the on-disk directory path (`plugins/<plugin>/skills/<skill>/`). A mismatch between the directory name and the metadata.fsm value is equally detectable at final validation time — the file's location on disk reveals the directory name — yet only the 2-field check is specified. An author who provides a display-friendly name that gets auto-normalized differently across the two artifacts could have a consistent SKILL.md-to-metadata.fsm check but still have an inconsistent directory name.

### GAP-196: Split recommendation during description writing creates guidance conflict when dependency graph is already finalized
- **Severity**: medium
- **Source**: architecture-accuracy-critic
- **Description**: The self-contained-descriptions capability includes guidance for splitting overly broad task descriptions (self-contained-descriptions:3.1). When the skill recommends splitting a task, the author would need to create additional tasks — but dependency mapping has already been finalized for the original task list. The specification does not address how the author resolves the resulting dependency graph inconsistency: the new tasks produced by splitting have no dependency entries, and the original task's relationships no longer apply cleanly. GAP-108 and GAP-109 established that the pipeline is strictly forward and corrections happen within each phase, but the split-recommendation scenario creates cross-phase artifact inconsistency that cannot be resolved within the description writing phase alone.

### GAP-197: Capability descriptions reference internal component mechanism names
- **Severity**: medium
- **Source**: functional-critic
- **Description**: The dependency-mapping capability description in functional.md references internal component mechanism names: "node addition, dangling reference cleanup, rename propagation" are implementation-level terms describing how the dependency graph maintains referential integrity, not user-observable behaviors. Similarly, the workflow-validation capability description references "self-containment feedback" — a mechanism name. A functional spec should describe what the author experiences, not how the implementation achieves it.

### GAP-198: Out of Scope items reference internal specification concepts and implementor-facing language
- **Severity**: medium
- **Source**: functional-critic
- **Description**: The Out of Scope section in functional.md contains entries that reference internal specification concepts rather than user-facing scope boundaries. Entries such as "Precision of internal terminology in capability descriptions" and "Progressive Construction Protocol" expose internal mechanism names to the functional spec level. Some entries use implementor-facing language ("deferred to implementation judgment") that belongs in the technical spec or rationale documentation, not a functional scope statement. GAP-28 resolved similar internal-component language in the original Out of Scope section, but subsequent additions re-introduced the pattern.

### GAP-199: Known Risks in functional.md reference internal architecture and runtime mechanism details
- **Severity**: medium
- **Source**: functional-critic
- **Description**: The Known Risks section in functional.md references internal architecture concepts: the "15-20 tasks" threshold is a technical implementation detail of CMP-dependency-map's responsibilities; "phase-gate architecture" is an internal structural term; references to the FSM plugin's "runtime guard" and "skill discovery directory" expose internal mechanism names. GAP-30 resolved similar implementation leakage in the original Known Risks section, but subsequent additions re-introduced the pattern. A functional spec's Known Risks should describe risks in terms the skill's author user would recognize, not internal system behavior.

### GAP-200: functional.md length exceeds functional spec target
- **Severity**: low
- **Source**: functional-critic
- **Description**: The functional.md document has grown substantially beyond a typical functional spec target length through successive gap resolutions. Sections such as the Brainstorming Gap Taxonomy (a post-hoc evaluation framework with a four-category breakdown and multi-column table) and the extended Out of Scope list add content that may belong in the technical spec or infra.md. The Brainstorming Gap Taxonomy in particular describes an evaluation methodology that is closer to a verification approach than a functional capability description.

### GAP-201: No technical specification for how author discussion facilitates multi-source combination
- **Severity**: medium
- **Source**: implementation-critic
- **Description**: The workflow-intake capability description states that authors "combine inputs through discussion when material spans multiple sources." The technical.md CMP-normalize responsibilities describe concatenation of contributions, but no component is specified as responsible for facilitating the author discussion that determines which contributions to combine and how. When two input-based sources partially overlap or conflict before brainstorming runs, no component specification defines the discussion mechanism — who initiates it, what prompts are used, or how the outcome feeds into CMP-normalize's concatenation step.

### GAP-202: Weak normative language in dependency-mapping Rule 5 preamble
- **Severity**: medium
- **Source**: requirements-critic
- **Description**: The Rule 5 preamble in dependency-mapping requirements states "the author MAY add, remove, or rename tasks." The word MAY denotes optional capability — the author is permitted but not required to perform these actions, which is the correct framing for an author capability. However, the skill's obligation to support these modifications is not stated with corresponding SHALL language. The rule preamble does not include a complementary "the skill SHALL support author-initiated modifications" obligation, leaving the skill's implementation requirement implied rather than normative.

### GAP-203: Non-normative "Each modification SHALL trigger" overspecifies implementation detail
- **Severity**: low
- **Source**: requirements-critic
- **Description**: The dependency-mapping Rule 5 preamble contains the clause "Each modification SHALL trigger a dependency graph update and re-validation to maintain referential integrity." The phrase "Each modification SHALL trigger" specifies implementation mechanism — a reactive trigger on modification events — rather than observable outcome. A normative requirement should state that after any modification the dependency graph reflects the change and referential integrity is maintained, not that a trigger fires. This is similar to the class of issues GAP-16 and GAP-47 addressed for "should" and "will" normative language.

### GAP-204: skill-file-generation self-validation failure scenario Then clause references internal correction loop
- **Severity**: medium
- **Source**: requirements-critic
- **Description**: The self-validation failure scenario in skill-file-generation (covering CMP-skill-md's frontmatter check) contains a Then clause that references the internal correction loop: "the skill does not finalize SKILL.md until self-validation passes." Referencing when finalization occurs couples the observable outcome to an internal state transition. The testable outcome should describe what the author observes — the skill reports the issue and requests correction — not the internal finalization gate. This is consistent with the class of internal-state language that GAP-146 resolved in workflow-validation.

### GAP-205: No scenario for dual input-based intake sources contributing simultaneously
- **Severity**: medium
- **Source**: requirements-coverage-critic
- **Description**: The intake architecture supports two input-based sources (existing skill, written steps) as non-exclusive parallel tasks, each contributing material independently. No requirement scenario covers the case where both input-based sources contribute material simultaneously — the author provides both an existing skill and written step descriptions. This scenario exercises CMP-intake-existing and CMP-intake-written both producing output that CMP-intake-brainstorm must then review, and CMP-normalize must concatenate. The existing multi-source test data in infra.md (Scenario D) covers one source contributing nothing, not both sources contributing simultaneously. GAP-63 added a multi-source scenario but it covers the normalize step's behavior, not the dual-active-source intake path that precedes it.

### GAP-206: No scenario for author explicitly canceling the workflow mid-phase
- **Severity**: medium
- **Source**: requirements-coverage-critic
- **Description**: The Out of Scope section defers session interruption (unexpected disconnection or loss of session state) to a future release. However, within an active session an author may explicitly decide to abort the workflow — declining to proceed after reviewing a phase output, or explicitly stating they wish to cancel. This is distinct from session interruption: the author is present and makes an intentional choice. No requirement scenario specifies the skill's behavior when the author explicitly chooses not to continue during an author confirmation gate.

### GAP-207: workflow-validation phase-completion summary scenario absent from infra.md workflow-validation coverage table
- **Severity**: medium
- **Source**: verification-critic, design-for-test-critic
- **Description**: The workflow-validation:1.7 scenario specifies a phase-completion summary that the skill presents after each construction phase before the author confirms completeness and the next phase begins. The infra.md coverage table for workflow-validation Rule 1 does not include verification of the phase-completion summary — no pass/fail criteria define what summary content is required, what constitutes an incomplete or incorrect summary, or how the blocking behavior is verified. This is a distinct concern from GAP-191, which addresses the absence of summary verification from the Rule 1 coverage description; GAP-207 addresses the absence of boundary examples or verification criteria for the summary content itself.

### GAP-208: dependency-mapping lightweight quality check has no boundary examples in infra.md
- **Severity**: low
- **Source**: verification-critic, design-for-test-critic
- **Description**: The infra.md dependency-mapping coverage table for Rule 5 references task addition with lightweight quality check verification, but no boundary examples define what passes and fails the lightweight check. The lightweight check criteria (label present and non-empty, description non-empty and identifies distinct work, task describes a concrete action) are specified in dependency-mapping:5.2 and CMP-dependency-map responsibilities, but no concrete pass/fail examples illustrate where the specificity and actionability boundaries lie for tasks added during dependency mapping. This is distinct from GAP-192, which addresses the missing boundary definition itself; GAP-208 addresses the absence of verification examples in infra.md specifically.

### GAP-209: No requirement scenario for lightweight quality check failure during dependency mapping task addition
- **Severity**: medium
- **Source**: logic-critic
- **Description**: The dependency-mapping:5.2 scenario specifies that the lightweight quality check must pass before a newly added task is accepted into the step list and dependency graph. No scenario specifies what happens when the quality check fails — whether the skill reports the specific criterion that failed (empty label, non-specific description, non-actionable task), how the author is prompted to correct the submission, and whether the task is withheld from the graph until correction. The positive path (check passes, task is added) is covered; the failure path is not.

### GAP-210: No requirement scenario for failure when phase-completion summary reveals incomplete updates
- **Severity**: low
- **Source**: logic-critic
- **Description**: The workflow-validation:1.7 scenario specifies a phase-completion summary that the author confirms before advancing. No scenario covers what happens when the author reviews the summary and identifies that not all entries were updated — for example, a task was skipped during the description writing phase and the summary reveals the gap. The confirmation gate's failure path (author does not confirm, identifies incompleteness) is unspecified; only the success path (author confirms completeness) is covered.

### GAP-211: dependency-mapping Rule 6 single-task workflow absent from behavioral-verification checklist
- **Severity**: medium
- **Source**: test-tasks-critic
- **Description**: The behavioral-verification tasks.yaml entry for dependency-mapping verification lists a Rule-level checklist covering Rules 1-5. Rule 6 (single-task workflows — empty dependency graph, author confirmation, immediate progression) was added via GAP-124 but was not added to the behavioral-verification checklist for dependency-mapping. The verification task does not include a step to exercise the single-task boundary case.

### GAP-212: workflow-validation phase-completion summary gate absent from behavioral-verification checklist
- **Severity**: medium
- **Source**: test-tasks-critic
- **Description**: The behavioral-verification tasks.yaml entry for workflow-validation verification includes a Rule-level checklist for Rules 1-3. The Rule 1 checklist covers incremental phase validation but does not include verification of the phase-completion summary gate specified in workflow-validation:1.7 — there is no checklist item confirming that the skill presents a phase-completion summary and blocks advancement until the author confirms. The scenario exists in the requirements but is absent from the behavioral-verification task's checklist.

### GAP-213: Name-consistency check absent from workflow-validation behavioral-verification checklist
- **Severity**: low
- **Source**: test-tasks-critic
- **Description**: The behavioral-verification tasks.yaml entry for workflow-validation verification includes a Rule 2 checklist item for comprehensive final validation. The checklist entry covers structural integrity checks but does not explicitly include name-consistency verification (confirming that the metadata.fsm value in fsm.json matches the SKILL.md frontmatter name field). GAP-176 added the name-consistency check to the requirements and the infra.md Rule 2 coverage description, but the behavioral-verification checklist was not updated to include it as a verifiable item.
