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

## Medium



### GAP-73: CMP-skill-md collision detection fires against current-workflow artifacts
- **Source**: Implicit Gap Detection-detection
- **Severity**: medium
- **Description**: CMP-skill-md and CMP-dependency-map are concurrent sibling tasks (both unblocked after CMP-normalize) that both write to `<output-directory>/<skill-name>/`. CMP-dependency-map's responsibility says 'Create the target directory if it does not exist; write the partial fsm.json artifact to <output-directory>/<skill-name>/fsm.json.' CMP-skill-md's responsibility says 'Detect when the target skill directory already exists and contains files; offer the author options to overwrite, choose a different skill name, or abort.' If CMP-dependency-map executes first (non-deterministic since both are unblocked), it creates the directory and writes the partial fsm.json. When CMP-skill-md then executes, it detects the directory exists and contains files — the partial fsm.json from the current workflow — and triggers collision detection, offering the author overwrite/rename/abort for a directory that the CURRENT workflow just created. After context compaction, the agent executing CMP-skill-md has no memory of CMP-dependency-map creating the directory (self-contained descriptions are the sole instruction source), so the task description provides no basis to distinguish current-workflow artifacts from pre-existing files. The collision detection was designed for pre-existing directories from prior skill creation attempts (infra.md scenario-specific setup says 'Pre-populate the target skill directory with existing files'), but nothing in the component spec or requirement (skill-file-generation:4.2) limits it to pre-existing files. An implementor would build collision detection that incorrectly fires during normal workflow execution. Source: implicit-detection
- **Triage**: check-in
- **Decision**: Move collision detection and directory creation from CMP-skill-md and CMP-dependency-map to CMP-normalize. CMP-normalize already collects the output directory and skill name; collision detection is added as its final responsibility after the author confirms the output path. At normalize time, no current-workflow files exist on disk, eliminating the race condition where CMP-dependency-map's partial fsm.json triggers CMP-skill-md's collision detection. Remove 'Create the target directory if it does not exist' from CMP-dependency-map and CMP-skill-md. Remove collision detection from CMP-skill-md. Update: technical.md § CMP-normalize (add collision detection + directory creation), § CMP-dependency-map (remove directory creation), § CMP-skill-md (remove collision detection + directory creation), § Data flow table. Cascade: requirements/skill-file-generation Rule 4 timing, infra.md scenario-specific setup.
- **Primary-file**: technical.md


### GAP-74: workflow-validation:2.3 self-containment audit scope narrower than component spec
- **Source**: Implicit Gap Detection-detection
- **Severity**: medium
- **Description**: workflow-validation:2.3's Then step says 'validation passes if no description contains cross-task references or external references' — checking only for reference-based violations. CMP-final-validation's self-containment audit specification in technical.md checks four items: '(a) goal statement, (b) specific actions, (c) acceptance criteria, (d) no undefined references.' The requirement covers only item (d). Items (a)-(c) — structural completeness checks that verify each description contains a goal, specific actions, and acceptance criteria — are absent from the requirement. An implementor building final validation from the requirement alone would implement only reference checking, missing the structural completeness portion of the self-containment audit. The infra coverage table for workflow-validation Rule 2 says 'verify self-containment failures can be corrected in-place' without specifying which checks constitute the audit, providing no additional disambiguation. While CMP-descriptions enforces the full checklist per-description during writing, the final validation requirement only tests the reference subset, meaning (a)-(c) failures that slip past CMP-descriptions have no requirement-level catch at final validation. Additionally, the Then step uses the 'passes if' conditional-in-Then pattern — the same normative defect that GAP-57 fixed in workflow-validation:2.1. Source: implicit-detection
- **Triage**: check-in
- **Decision**: Rewrite workflow-validation:2.3's Then step with And-chained assertions covering all 4 self-containment checklist items from CMP-final-validation: (a) every description contains a goal statement, (b) every description contains specific actions, (c) every description contains acceptance criteria, (d) no description contains cross-task references or external references. Removes the 'passes if' conditional-in-Then pattern (same defect GAP-57 fixed in 2.1). Follows GAP-57's precedent for And-chained assertions within a single composite scenario. Update: requirements/workflow-validation/requirements.feature.md § 2.3. Cascade: infra.md Rule 2 coverage (mention structural completeness), integration.feature.md 2.3 reference.
- **Primary-file**: requirements/workflow-validation/requirements.feature.md


### GAP-76: 3.5 Then uses action verb 'consolidates'
- **Source**: Resolution Normative Detection-detection
- **Severity**: medium
- **Description**: Resolution of GAP-31 introduced mechanism language in self-contained-descriptions:3.5: the Then step 'the workflow consolidates the two tasks into one' uses 'consolidates' — an action verb describing an internal merge operation — rather than an author-observable state. Subsequent normative-detection resolutions (GAP-64, GAP-65) fixed 'passes validation' and 'phase continues' in the same scenario but left 'consolidates' unaddressed. Observable phrasing should follow the pattern established by scenario 3.4 from the same resolution: 'the workflow contains the original task split into its component parts' uses a state predicate ('contains'), not an action verb. The fix for 3.5 would be: 'the workflow contains one task in place of the two original tasks'. In requirements/self-contained-descriptions/requirements.feature.md.
- **Triage**: delegate
- **Decision**: Rewrite self-contained-descriptions:3.5 Then step (line 89) from 'Then the workflow consolidates the two tasks into one' to 'Then the workflow contains one task in place of the two original tasks.' Replaces the action verb 'consolidates' with the state predicate 'contains', achieving exact parallelism with scenario 3.4 and following the pattern established by GAP-58, GAP-64, and GAP-65.
- **Primary-file**: requirements/self-contained-descriptions/requirements.feature.md

