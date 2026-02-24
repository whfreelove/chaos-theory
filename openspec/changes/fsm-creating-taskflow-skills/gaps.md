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


### GAP-67: Split child-reference update mechanism unspecified
- **Source**: Implicit Gap Detection-detection
- **Severity**: medium
- **Description**: CMP-descriptions specifies the split mechanism as: 'replace the pre-split entry with new entries using IDs assigned by the max+1 rule; all parents and children of the pre-split task are inherited by all post-split tasks.' The parent-side inheritance is clear (new entries get the old task's blockedBy entries). The child-side inheritance — how blockedBy references to the pre-split task ID in OTHER entries are updated — uses the vague word 'inherited' without specifying the concrete mutation. Compare with the merge mechanism which explicitly states 'all blockedBy references to the removed task in other entries are updated to point to the surviving task,' and the remove mechanism which explicitly states 'garbage-collect any remaining blockedBy references to it.' Both merge and remove define the exact mutation to other entries' blockedBy arrays; split does not. An implementor could: (a) replace old ID with all new IDs in each child's blockedBy (fan-out pattern), (b) replace old ID with just one new ID, or (c) not update children's blockedBy at all, leaving dangling references. Option (c) would not be caught by the post-split re-validation, which only invokes cycle detection — not reference resolution. The dangling reference would persist until CMP-final-validation's structural integrity check at the end of the pipeline, meaning the description-writing phase continues with an inconsistent graph.
- **Triage**: delegate
- **Decision**: Specify the fan-out mutation explicitly in CMP-descriptions split mechanism: 'all blockedBy references to the pre-split task ID in other entries are replaced with references to all post-split task IDs.' This mirrors merge's explicit 'all blockedBy references to the removed task in other entries are updated to point to the surviving task' and directly implements the decision's intent ('all children become children of all post-split tasks'). The mutation prevents dangling references by construction; post-split re-validation (cycle detection) remains unchanged. Update: technical.md § CMP-descriptions split responsibility.
- **Primary-file**: technical.md


### GAP-68: Infra skill-file-generation Rule numbers mismatch requirements
- **Source**: Implicit Gap Detection-detection
- **Severity**: medium
- **Description**: The infra.md skill-file-generation coverage table uses Rule numbers that do not match the requirements file. Requirements define: Rule 1 (SKILL.md structure), Rule 2 (SKILL.md self-validation), Rule 3 (fsm.json generation), Rule 4 (output directory placement). Infra labels: 'Rule 1: SKILL.md generation' (maps to Req Rule 1 but also includes self-validation content from Req Rule 2 and directory placement from Req Rule 4), 'Rule 2: Task definition file generation' (maps to Req Rule 3 — wrong number), 'Rule 2 (self-validation): SKILL.md self-validation' (maps to Req Rule 2 — correct content but creates a numbering collision with the other Rule 2 row), 'Rule 3: Correct directory structure' (maps to Req Rule 4 — wrong number). A verifier tracing infra 'Rule 2' back to requirements would find Req Rule 2 is SKILL.md self-validation, not task definition file generation. The numbering collision (two rows labeled Rule 2) and the off-by-one shift for Rules 3/4 break the traceability chain from infra verification to requirements. Same class of defect as GAP-28 (phantom references breaking traceability), but affecting Rule numbers rather than scenario IDs.
- **Triage**: delegate
- **Decision**: Renumber the skill-file-generation coverage table to exact 1:1 correspondence with requirements Rules 1–4. Redistribute bleed-through content: move self-validation content from Rule 1 to a dedicated Rule 2 row; move directory placement content from Rule 1 to Rule 4. Renumber 'Rule 2: Task definition file generation' to Rule 3. Renumber 'Rule 3: Correct directory structure' to Rule 4. Eliminate the 'Rule 2 (self-validation)' collision row by absorbing its content into the properly numbered Rule 2 row. Same resolution class as GAP-28.
- **Primary-file**: infra.md


### GAP-70: 3.7 Then step uses mechanism trigger 'runs again'
- **Source**: Resolution Normative Detection-detection
- **Severity**: medium
- **Description**: Resolution of GAP-60 introduced mechanism language in self-contained-descriptions:3.7: the Then step 'And re-validation runs again after the author's correction' describes an internal trigger ('runs again') rather than an observable outcome. GAP-56 already fixed the equivalent 're-runs validation' in workflow-validation:1.7 by removing it. In requirements/self-contained-descriptions/requirements.feature.md.
- **Triage**: delegate
- **Decision**: Remove the Then step 'And re-validation runs again after the author's correction' from self-contained-descriptions:3.7 (line 116). Following GAP-56's precedent, which removed equivalent 're-runs validation' mechanism language from workflow-validation:1.7. The scenario's Given/When establish the re-validation context; remaining Then steps describe only observable outcomes (cycle presentation, correction prompting). The internal re-validation trigger is not author-observable.
- **Primary-file**: requirements/self-contained-descriptions/requirements.feature.md


### GAP-71: 3.7 Then step embeds 'until re-validation passes' conditional
- **Source**: Resolution Normative Detection-detection
- **Severity**: medium
- **Description**: Resolution of GAP-60 introduced a conditional embedded in a Then step in self-contained-descriptions:3.7: 'And the skill does not present the next task for description until re-validation passes' places 'until re-validation passes' inside a Then clause. GAP-56 already fixed the equivalent 'if validation passes' in workflow-validation:1.7 by removing the conditional entirely. Conditions belong in Given/When, not Then. In requirements/self-contained-descriptions/requirements.feature.md.
- **Triage**: delegate
- **Decision**: Rewrite the Then step in self-contained-descriptions:3.7 (line 117) from 'And the skill does not present the next task for description until re-validation passes' to 'And the skill does not present the next task for description.' Removes the embedded temporal conditional ('until re-validation passes') while preserving the observable gating behavior. Following GAP-56's precedent: conditions belong in Given/When, not Then. The scenario's When clause ('re-validation detects a cycle') scopes the Then to the cycle-detected state; the resolution path is covered by existing scenarios 3.4 and 3.5.
- **Primary-file**: requirements/self-contained-descriptions/requirements.feature.md


### GAP-72: dependency-mapping:1.2 and 2.2 use 'recorded' state-mutation verb
- **Source**: Resolution Normative Detection-detection
- **Severity**: medium
- **Description**: Resolution of GAP-11 introduced state-mutation mechanism language in dependency-mapping:1.2 ('the ordering is recorded in the dependency table') and 2.2 ('the tasks are recorded with no blocking relationships'). 'Recorded' describes internal artifact mutation rather than an observable outcome — the same defect class that GAP-31 fixed ('propagated' → 'preserves') and GAP-58 fixed ('adds ... to its own blockedBy list' → 'contains'). Observable phrasing would state visible state ('the dependency table reflects the specified order') not the internal write operation. In requirements/dependency-mapping/requirements.feature.md.
- **Triage**: delegate
- **Decision**: Rewrite Then steps in dependency-mapping:1.2 (line 21) and 2.2 (line 41) to replace the state-mutation verb 'recorded' with observable-state language. 1.2: from 'Then the ordering is recorded in the dependency table' to 'Then the dependency table reflects the specified order.' 2.2: from 'Then the tasks are recorded with no blocking relationships' to 'Then the tasks have no blockedBy entries.' Follows GAP-58's precedent ('adds' → 'contains') and GAP-31's precedent ('propagated' → 'preserves'). 2.2 additionally aligns with dependency-mapping:2.1, which already uses 'those tasks have no blockedBy entries' for the system-identified parallel case.
- **Primary-file**: requirements/dependency-mapping/requirements.feature.md

