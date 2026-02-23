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

### GAP-55: Untitled finding
- **Source**: Implicit Gap Detection-detection
- **Severity**: medium
- **Description**: Infra.md dependency-mapping Rule 5 coverage specifies a 'lightweight quality check' for tasks added during dependency mapping — including pass/fail criteria (label present/non-empty, description specificity, actionability) and a detailed verification procedure ('verify the lightweight quality check runs before the task enters the graph — verify pass when label and description meet specificity and actionability criteria, verify fail when label is empty, description is vague, or task is not actionable'). This behavior has no backing in requirements or technical: dependency-mapping:5.2 specifies only that 'the skill prompts the author to specify the new task's dependencies before re-presenting the graph,' and CMP-dependency-map's add operation says only 'prompt the author for the new task's dependencies before updating the graph; assign the next sequential ID.' An implementor reading requirements and technical would not implement a quality check; a verifier following infra would expect one and fail verification.
- **Triage**: check-in
- **Decision**: Remove the lightweight quality check from infra.md dependency-mapping Rule 5 coverage. The quality check has no backing in requirements (dependency-mapping:5.2) or technical (CMP-dependency-map Add). Infra verification should verify specified behavior: dependency prompting, graph update, and ID assignment. Content quality for added tasks is handled by CMP-descriptions, which is the specified home for content quality enforcement. Update: infra.md § dependency-mapping Rule 5 coverage.
- **Primary-file**: infra.md



## Medium

### GAP-59: skill-file-generation Rule 4 uses stale plugin directory path
- **Source**: Implicit Gap Detection-detection
- **Severity**: medium
- **Description**: skill-file-generation:4.1 specifies files are written to `<plugin>/skills/<skill-name>/`, the Rule 4 title says 'correct plugin directory', and the Given clause references 'plugin directory'. GAP-48 resolved the path generalization in technical.md and infra.md to `<output-directory>/<skill-name>/` (with CMP-normalize collecting the output directory), but its outcome explicitly notes 'cascading updates needed in requirements/skill-file-generation Rule 4 and infra.md coverage table (out of scope for this file).' The cascading update to requirements was never applied. An implementor reading requirements/skill-file-generation would build plugin-specific directory logic (collecting a plugin name from a known plugin list), while technical.md expects a generic author-specified output directory. The two artifacts specify incompatible file placement interfaces.
- **Triage**: check-in
- **Decision**: Apply the cascading update deferred by GAP-48: update requirements/skill-file-generation Rule 4 to use the generalized output-directory path. Replace 'correct plugin directory' with 'correct output directory' in the Rule 4 title, 'plugin directory' with 'output directory' in the 4.1 Given clause, and `<plugin>/skills/<skill-name>/` with `<output-directory>/<skill-name>/` in the 4.1 Then step. Scenario 4.2 needs no change. This aligns requirements with technical.md and infra.md which both already use the generalized path.
- **Primary-file**: requirements/skill-file-generation/requirements.feature.md

### GAP-60: Pipeline gate scenario for cycle after split/merge missing from requirements
- **Source**: Implicit Gap Detection-detection
- **Severity**: medium
- **Description**: GAP-27's resolved outcome states: 'added Scenario Outline @self-contained-descriptions:3.6 covering the pipeline gate behavior — when re-validation detects a cycle after a confirmed split or merge, the description-writing phase does not continue and the author is prompted to resolve the cycle.' However, the current requirements/self-contained-descriptions/requirements.feature.md shows @self-contained-descriptions:3.6 as 'Scenario Outline: Author declines a <suggestion_type> suggestion' — an unrelated scenario. The pipeline gate scenario is absent from the file. Technical.md (CMP-descriptions) specifies the behavior in detail: 'if re-validation detects a cycle, present the cycle-participating tasks and edges to the author and allow removal or redirection of specific blockedBy entries to break the cycle, then re-run re-validation.' An implementor following requirements alone would not implement cycle correction after restructuring because no requirement backs it; CMP-final-validation's cycle detection is the only specified cycle handling, but it runs too late — after description writing completes.
- **Triage**: check-in
- **Decision**: Add @self-contained-descriptions:3.7 Scenario Outline covering the pipeline gate when re-validation detects a cycle after a confirmed split or merge. The scenario specifies that cycle-participating tasks and edges are presented to the author, the author is prompted to resolve the cycle by removing or redirecting blockedBy entries, and the description-writing phase does not continue until re-validation passes. Uses a Scenario Outline with split/merge in the Examples table. Placed after the existing 3.6 (decline path) to avoid renumbering. Update integration.feature.md to reference the new scenario. Update infra.md Rule 3 coverage to include cycle-correction verification.
- **Primary-file**: requirements/self-contained-descriptions/requirements.feature.md


### GAP-61: Infra workflow-intake Rule 2 verification references unspecified conditional logic decomposition
- **Source**: Implicit Gap Detection-detection
- **Severity**: medium
- **Description**: The infra.md workflow-intake Rule 2 coverage table instructs verifiers to 'provide a skill with conditional branching, verify the skill presents decomposition options and incorporates the author's choice.' Neither the workflow-intake Rule 2 requirements (scenarios 2.1–2.4: sequential extraction, parallelism identification, author confirmation, author modification) nor CMP-intake-existing's responsibilities mention conditional logic, branching, or decomposition options. An implementor following requirements would not build conditional-branching decomposition; a verifier following infra would test for it and fail verification against a correct implementation. This is the same class of infra-requirements mismatch as GAP-55 (infra references behavior absent from requirements and technical).
- **Triage**: check-in
- **Decision**: Remove 'conditional logic decomposition (author chooses strategy)' from infra.md workflow-intake Rule 2 'What it covers' column and the corresponding verification step about conditional branching. The behavior has no backing in requirements (workflow-intake:2.1–2.4 specify only sequential extraction, parallelism identification, author confirmation, and author modification) or technical (CMP-intake-existing lists no conditional logic responsibilities), and is architecturally infeasible (fsm.json defines a static task list that cannot conditionally activate tasks). Same resolution class as GAP-55. Update: infra.md § workflow-intake Rule 2 coverage row.
- **Primary-file**: infra.md


### GAP-64: "dependency graph passes validation" is mechanism language in Then steps
- **Source**: Resolution Normative Detection-detection
- **Severity**: medium
- **Description**: Resolution of GAP-31 introduced mechanism language in self-contained-descriptions:3.4 and 3.5: the Then step 'And the dependency graph passes validation' describes an internal validation operation running and passing rather than an author-observable state. Per MDG normative guidance, Then steps must state observable outcomes. The observable outcome is 'the dependency graph contains no cycles' or 'the dependency graph is valid', not the mechanism by which validity is established. In requirements/self-contained-descriptions/requirements.feature.md.
- **Triage**: delegate
- **Decision**: Rewrite the Then step in self-contained-descriptions:3.4 (line 81) and 3.5 (line 91) from 'And the dependency graph passes validation' to 'And the dependency graph contains no cycles.' Replaces mechanism language (validation operation running and passing) with the observable state outcome (graph is acyclic), matching the pattern established in workflow-validation:1.2. Reference preservation is already covered by the preceding Then steps in both scenarios.
- **Primary-file**: requirements/self-contained-descriptions/requirements.feature.md


### GAP-65: "description-writing phase continues" is pipeline-state mechanism language
- **Source**: Resolution Normative Detection-detection
- **Severity**: medium
- **Description**: Resolution of GAP-31 introduced mechanism language in self-contained-descriptions:3.4 ('the description-writing phase continues with the post-split tasks') and 3.5 ('the description-writing phase continues with the merged task'); scenario 3.6 also contains 'the description-writing phase continues to the next task'. These Then steps describe internal pipeline state transitions rather than author-observable outcomes. The author observes being presented with the next task for description, not that an internal phase progresses. This is the same class of mechanism-verb defect that GAP-30 fixed in workflow-intake:5.1. In requirements/self-contained-descriptions/requirements.feature.md.
- **Triage**: delegate
- **Decision**: Rewrite the Then steps in self-contained-descriptions:3.4 (line 82), 3.5 (line 92), and 3.6 (line 100) from 'the description-writing phase continues with [X]' to 'the skill presents [X] to the author for description.' Specifically: 3.4 becomes 'And the skill presents the post-split tasks to the author for description'; 3.5 becomes 'And the skill presents the merged task to the author for description'; 3.6 becomes 'And the skill presents the next task to the author for description.' Replaces internal pipeline-state mechanism language ('phase continues') with the observable author interaction ('skill presents ... to the author'), following the pattern established in self-contained-descriptions:5.1 and the precedent set by GAP-30.
- **Primary-file**: requirements/self-contained-descriptions/requirements.feature.md

