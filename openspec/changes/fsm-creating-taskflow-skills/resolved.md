# Resolved Gaps

<!-- GAP TEMPLATE:
### GAP-XX: Title
- **Source**: <kebab-case with type suffix, e.g., functional-critic, implicit-detection>
- **Severity**: high|medium|low
- **Description**: ... (original concern, immutable)
- **Triage**: check-in|delegate|defer-release|defer-resolution (preserved from gaps.md)
- **Decision**: ... (immutable point-in-time decision)
- **Status**: resolved|superseded|deprecated (set on move to resolved.md)
- **Superseded by**: GAP-XX (only when Status is superseded)
- **Outcome**: ... (optional — records what actually changed in artifacts after Decision was applied)
- **Rationale**: ... (only when Status is deprecated — must cite specific evidence: artifact change, code evidence, or context shift)
- **Current approach**: ... (only when Status is superseded — points to up-to-date information)

See tokamak:managing-spec-gaps for triage and status semantics.
-->

### GAP-28: infra.md workflow-validation coverage table references phantom scenario IDs
- **Source**: implicit-detection
- **Severity**: high
- **Description**: The infra.md workflow-validation Rule 1 and Rule 2 coverage rows reference scenario IDs that do not exist in the requirements. Rule 1 cites 1.3.2 (no sub-scenario format is used), 1.7.1 (does not exist), and 1.8 (does not exist; last scenario is 1.7), and mislabels 1.7 as "phase-completion summary gate" when the actual scenario title is "Corrected validation error unblocks phase progression." Rule 2 cites 2.10, 2.11, and 2.12, none of which exist (last scenario is 2.4). The associated behaviors — phase-completion summary gate, advancement blocked when phase-completion summary reveals skipped items, and artifact recovery — do not appear in requirements, functional.md, or technical.md components. This is the same class of defect as GAP-22, which fixed only the skill-file-generation phantom references; the workflow-validation phantoms were not addressed by that resolution.
- **Triage**: check-in
- **Decision**: Strip all phantom scenario ID references from the workflow-validation coverage rows. Rewrite Rule 1 and Rule 2 coverage entries at Rule level only — no scenario ID citations, following writing-infra-specs guidance to describe coverage patterns rather than per-scenario line items.
- **Status**: resolved
- **Outcome**: Rewrote infra.md workflow-validation Rule 1 and Rule 2 coverage table entries to describe coverage at the Rule level with no scenario ID citations. Removed all phantom references (1.3.2, mislabeled 1.7, 1.7.1, 1.8, 2.10, 2.11, 2.12) and their associated undocumented behaviors (phase-completion summary gate, artifact recovery, metadata fsm validation, name consistency). Both rows now describe the behavioral pattern each Rule covers and the verification approach without referencing specific scenario IDs.

### GAP-29: Auto-normalization of skill names has no component responsibility or requirement scenario
- **Source**: implicit-detection
- **Severity**: medium
- **Description**: A technical.md Y-statement decision states that CMP-skill-md's auto-normalize step produces consistent directory name, metadata.fsm, and SKILL.md name values from the same normalized input. The infra.md skill-file-generation Rule 2 verification plan instructs verifiers to "provide a display-friendly name, verify normalization and confirmation prompt." However, CMP-skill-md's responsibilities do not include name normalization, no requirement scenario specifies when normalization occurs or what triggers a confirmation prompt, and the normalization algorithm is undefined. Implementations could apply different or no normalization and satisfy the requirements as written while failing the infra verification step.
- **Triage**: delegate
- **Decision**: Add "normalizes author-provided display names to directory-safe kebab-case format (lowercase; spaces and special characters replaced with hyphens)" to CMP-skill-md responsibilities in technical.md. The normalization algorithm is now defined at the component level; infra.md verification language remains valid.
- **Status**: resolved
- **Outcome**: Added normalization responsibility to CMP-skill-md in technical.md: "Normalize the author-provided display name to a directory-safe kebab-case format (lowercase; spaces and special characters replaced with hyphens); present the normalized name to the author for confirmation or override; use the confirmed normalized name for the directory path, the frontmatter name field, and the metadata.fsm value." The algorithm is now defined; infra.md verification language ("verify normalization and confirmation prompt") is now backed by a component specification.

### GAP-30: workflow-intake:5.1 Then steps describe internal intake source execution order rather than observable outcomes
- **Source**: resolution-normative-detection
- **Severity**: medium
- **Description**: The Then steps in workflow-intake Rule 5 Scenario 1 specify that existing-skill analysis is performed first, written step descriptions are processed second, brainstorming fills gaps after both complete, and all results are merged during normalization. These steps describe internal component sequencing — HOW intake sources are ordered and combined — rather than what the author observes as a result. Per MDG normative guidance, Then steps must state observable outcomes, not mechanism execution order.
- **Triage**: delegate
- **Decision**: Replace the multi-step mechanism Then clause with a single declarative Then step: "the skill produces a unified normalized step list that incorporates content from both the existing-skill analysis and the written step descriptions."
- **Status**: resolved
- **Outcome**: Replaced the four mechanism Then steps in workflow-intake:5.1 with a single declarative Then step: "the skill produces a unified normalized step list that incorporates content from both the existing-skill analysis and the written step descriptions." Updated the scenario title from "Multi-source intake follows a defined interaction sequence" to "Multi-source intake produces a unified step list incorporating both sources" to match the observable outcome being tested.

### GAP-31: self-contained-descriptions:3.4 and 3.5 Then steps name an internal artifact and use a mechanism verb
- **Source**: resolution-normative-detection
- **Severity**: medium
- **Description**: The Then steps in self-contained-descriptions scenarios 3.4 and 3.5 reference "partial fsm.json" by name — an internal intermediate artifact — rather than describing what the author observes. Scenario 3.4 also uses "propagated" as a mechanism verb for dependency inheritance. Per MDG normative guidance, Then steps must describe observable author-facing outcomes (e.g., a new task appears in the workflow, the task is consolidated) rather than naming internal artifacts or describing internal data transfer mechanisms.
- **Triage**: delegate
- **Decision**: Rewrite 3.4 Then as "the workflow contains the original task split into its component parts, each part preserves the predecessor and successor relationships of the original task, and the dependency graph passes validation." Rewrite 3.5 Then as "the workflow consolidates the two tasks into one, preserving their combined predecessor and successor relationships, and the dependency graph passes validation."
- **Status**: resolved
- **Outcome**: Rewrote 3.4 Then steps to: "the workflow contains the original task split into its component parts / And each part preserves the predecessor and successor relationships of the original task / And the dependency graph passes validation / And the description-writing phase continues with the post-split tasks." Rewrote 3.5 Then steps to: "the workflow consolidates the two tasks into one / And the consolidated task preserves the combined predecessor and successor relationships of both original tasks / And the dependency graph passes validation / And the description-writing phase continues with the merged task." Internal artifact naming and mechanism verbs removed.

### GAP-1: "Compaction" is internal mechanism language in functional.md
- **Source**: functional-critic
- **Severity**: medium
- **Description**: Two passages in functional.md use the term "compaction" to explain why tasks must be self-contained. Compaction is a Claude Code internal mechanism, not a concept a skill author would reason about. The author's concern is that tasks remain executable without relying on earlier conversation context — the spec should be reframed in those terms.
- **Triage**: check-in
- **Decision**: Add an audience context note to functional.md (e.g., a Context or Vocabulary section) clarifying that the target audience is Claude Code skill authors who are familiar with compaction; the term is intentional and appropriate for this audience. This prevents future spec review agents from flagging the term as audience-inappropriate.
- **Status**: resolved
- **Outcome**: Added a Context section at the top of functional.md with an Audience note explaining that 'compaction' is intentional terminology for Claude Code skill authors, preventing future reviewers from flagging it as audience-inappropriate. [diff: +4/-0 functional.md]

### GAP-2: What Changes section uses internal workflow terminology
- **Source**: functional-critic
- **Severity**: low
- **Description**: The What Changes section in functional.md describes the user experience using internal workflow terms ("intake paths," "gap-filling step") rather than describing what skill authors receive. The Scope section already covers this concern more clearly; the What Changes entry is redundant and uses leakier language.
- **Triage**: delegate
- **Decision**: Rewrite the What Changes entry to user-facing language: "Skill authors receive guidance tailored to their starting point — existing skill analysis, written step descriptions, or both — with brainstorming to fill remaining gaps."
- **Status**: resolved
- **Outcome**: Replaced the second What Changes bullet from internal workflow terminology ('intake paths', 'gap-filling step') to user-facing language describing what skill authors receive. [diff: +1/-1 functional.md]

### GAP-3: OBJ-incremental-validation describes final validation as a pre-generation gate
- **Source**: design-critic
- **Severity**: high
- **Description**: OBJ-incremental-validation states that the final validation pass runs "before file generation," but the task dependency graph and component descriptions place CMP-final-validation after both CMP-skill-md and CMP-fsm-json-finalize have already written artifacts to disk. Final validation is a post-generation correctness check; an implementer reading the objective would design the wrong write order.
- **Triage**: check-in
- **Decision**: Rewrite OBJ-incremental-validation to accurately describe final validation as a post-generation check: "validates generated artifacts before the skill session completes."
- **Status**: resolved
- **Outcome**: Rewrote OBJ-incremental-validation to say 'comprehensive cross-cutting final validation pass that validates generated artifacts before the skill session completes' instead of 'before file generation', accurately reflecting that final validation runs after CMP-skill-md and CMP-fsm-json-finalize have written artifacts to disk. [diff: +1/-1 technical.md]

### GAP-4: blockedBy data flow from dependency mapping through to fsm.json finalization is unspecified
- **Source**: design-critic
- **Severity**: medium
- **Description**: CMP-fsm-json-finalize describes finalizing a "progressively-built fsm.json" assembled incrementally across prior phases, but neither CMP-dependency-map nor CMP-descriptions specifies building or appending to an intermediate fsm.json artifact. CMP-fsm-json-finalize's formal dependencies list only the enriched task list from CMP-descriptions, and that output format does not include a blockedBy field. The mechanism by which finalization acquires blockedBy values — and how those values flow through the pipeline — is undocumented across all three components.
- **Triage**: check-in
- **Decision**: Document the progressive construction pattern formally: CMP-dependency-map writes a partial fsm.json with blockedBy entries; CMP-descriptions reads and updates it with description and activeForm; CMP-fsm-json-finalize reads and finalizes it. Update the data flow table and component dependency documentation to reflect this shared intermediate artifact.
- **Status**: resolved
- **Outcome**: Updated the data flow table to show CMP-dependency-map outputting 'Partial fsm.json' with '{id, subject, blockedBy}' entries and CMP-descriptions outputting 'Partial fsm.json (updated)' with description and activeForm. Added responsibility to CMP-dependency-map to write the partial fsm.json artifact. Added responsibility to CMP-descriptions to read and update the partial fsm.json in-place. Updated dependencies for CMP-descriptions (partial fsm.json with IDs, subjects, and blockedBy) and CMP-fsm-json-finalize (progressively built by CMP-dependency-map and updated by CMP-descriptions). [diff: +7/-5 technical.md]

### GAP-5: System overview diagram omits SKILL.md to Final Validation data dependency
- **Source**: design-critic
- **Severity**: low
- **Description**: The system overview diagram in technical.md shows the SKILL.md branch terminating without a connection to Final Validation, while the authoritative task dependency graph and surrounding prose both document that Final Validation reads the SKILL.md output for name consistency. Readers must manually reconcile the two diagrams.
- **Triage**: delegate
- **Decision**: Add a dashed read-arrow from the SKILL.md node to the Final Validation node in the system overview diagram to match the authoritative task dependency graph.
- **Status**: resolved
- **Outcome**: Added 'E1 -.->|reads output| F' edge in the system overview Mermaid diagram, matching the dashed edge already present in the authoritative task dependency graph (SM -.->|reads output| FV). [diff: +1/-0 technical.md]

### GAP-6: Python script for cycle detection lacks contract, location, and feasibility documentation
- **Source**: technical-critic
- **Severity**: high
- **Description**: CMP-dependency-map and CMP-final-validation both delegate cycle detection to "topological sort via programmatic tool invocation (Python script)" with no documentation of whether this script exists, where it is located, what its invocation interface is, how it should be tested, or why Python was selected over alternatives. Cycle detection is a core correctness guarantee; without the script's contract and justification, neither component can be implemented as specified.
- **Triage**: check-in
- **Decision**: Specify the Python script contract: document the script's location within the plugin, its invocation interface (input format, exit codes, stdout), and how to test it. Add a Y-statement justifying deterministic programmatic cycle detection over agent-native reasoning — LLM reasoning is unreliable for correctness-critical checks and may silently skip detection; a script provides deterministic, auditable results. Script is to be created as part of implementation.
- **Status**: resolved
- **Outcome**: Added CMP-cycle-detect-script component documenting: location (plugins/finite-skill-machine/scripts/detect_cycles.py), invocation interface (JSON on stdin, exit 0/1/2 with specific stdout/stderr contracts), testing approach (pytest with acyclic/cyclic/malformed input), and Python 3 stdlib-only dependency. Added Y-statement decision justifying deterministic Python script over LLM reasoning for correctness-critical cycle detection. Updated cycle detection references in CMP-dependency-map, CMP-final-validation, and CMP-descriptions to name CMP-cycle-detect-script explicitly. [diff: +15/-2 technical.md]

### GAP-7: Deterministic node expansion during description writing lacks an implementable specification
- **Source**: technical-critic
- **Severity**: medium
- **Description**: The task-splitting behavior during description writing (deterministic node expansion) does not document what artifact the agent mutates, how newly allocated IDs are determined at that phase, or what "re-validate the dependency graph after splitting" invokes. The split mechanism is specified at the requirement level but lacks the implementation-level specification needed for mid-pipeline execution.
- **Triage**: check-in
- **Decision**: Document the split mechanism implementation details in technical.md: the artifact being mutated is the partial fsm.json under construction; new task IDs follow the max+1 rule already established for CMP-dependency-map; re-validation after splitting invokes the same cycle detection Python script.
- **Status**: resolved
- **Outcome**: Updated the split responsibility in CMP-descriptions to specify: deterministic node expansion operates on the partial fsm.json; new entries use IDs from the max+1 rule (max existing ID + 1, incrementing per new entry); re-validation invokes CMP-cycle-detect-script. [diff: +1/-1 technical.md]

### GAP-8: CMP-dependency-map add-task behavior missing the prompt-for-dependencies step
- **Source**: implementation-critic
- **Severity**: medium
- **Description**: CMP-dependency-map describes uniform handling of add, remove, and rename task operations, but the add operation has a required behavioral distinction: the skill must prompt the author for the new task's dependencies before re-presenting the dependency graph. The current uniform phrasing implies the task is appended with empty dependencies, which differs meaningfully from the required prompt-first behavior.
- **Triage**: check-in
- **Decision**: Replace the uniform modification description with explicit per-operation behavior: for add — prompt for new task's dependencies before updating the graph; for remove — garbage-collect all blockedBy references to the removed task; for rename — update all references throughout the dependency table.
- **Status**: resolved
- **Outcome**: Replaced the single uniform 'Support step list modifications' bullet in CMP-dependency-map with explicit per-operation sub-bullets: Add (prompt for dependencies, assign max+1 ID), Remove (garbage-collect blockedBy references), Rename (update subject and all references). Kept the re-validation trigger as a separate bullet applying to all operations. [diff: +5/-1 technical.md]

### GAP-9: CMP-skill-md validation failure path is undocumented
- **Source**: implementation-critic
- **Severity**: medium
- **Description**: CMP-skill-md specifies self-validation of YAML frontmatter but does not document the failure path. Every other validating component in technical.md explicitly states that validation failures must be presented to the author for correction before the component completes. The absence of this failure path from CMP-skill-md leaves the correction behavior unspecified.
- **Triage**: check-in
- **Decision**: Integrate the failure path into the validation statement: "Validate YAML frontmatter contains name and description fields; if missing, prompt the author to provide them before completing."
- **Status**: resolved
- **Outcome**: Updated CMP-skill-md's frontmatter validation responsibility to include the failure path: 'if missing, prompt the author to provide them before completing', making the correction behavior explicit and consistent with other validating components. [diff: +1/-1 technical.md]

### GAP-10: Weak normative language in a dependency-mapping Then step
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: A Then step in the dependency-mapping requirements uses "can run simultaneously" to describe concurrent task execution. Then steps describing mandatory system behavior must use definitive language. The clause should be rewritten with definitive language or removed if it states an implication rather than an observable outcome.
- **Triage**: check-in
- **Decision**: Remove the "can run simultaneously" clause entirely. The observable outcome is "those tasks have no blockedBy entries." Parallel execution is an FSM runtime implication, not an observable skill output.
- **Status**: resolved
- **Outcome**: Removed 'and can run simultaneously' from the Then step in scenario dependency-mapping:2.1, leaving only the observable outcome 'those tasks have no blockedBy entries'. [diff: +1/-1 requirements/dependency-mapping/requirements.feature.md]

### GAP-11: Author confirmation action placed inside a Then step
- **Source**: requirements-critic
- **Severity**: high
- **Description**: Two scenarios in the dependency-mapping requirements place an actor action ("the author confirms") inside a Then step. Then steps must describe the system's observable response only; actor actions belong in When steps. The affected scenarios require structural correction to separate the confirming action from the system response.
- **Triage**: check-in
- **Decision**: Restructure both scenarios: move "the author confirms" to a When step, leaving only the system response in Then. For 1.2: "When the author confirms the order" → "Then the ordering is recorded in the dependency table." For 2.2: "When the author confirms the tasks are independent" → "Then the tasks are recorded with no blocking relationships."
- **Status**: resolved
- **Outcome**: Restructured scenarios dependency-mapping:1.2 and dependency-mapping:2.2. In both, the prior When became an And under Given, the author confirmation action moved to When, and Then now contains only the system's observable response. [diff: +8/-6 requirements/dependency-mapping/requirements.feature.md]

### GAP-12: Cycle detection scenario bundles three independently falsifiable outcomes in one Then step
- **Source**: requirements-critic
- **Severity**: high
- **Description**: The cycle detection scenario in the dependency-mapping requirements bundles three independently verifiable outcomes in a single Then step: rejection of the graph, identification of the tasks involved, and the resolution prompt. Each outcome can fail independently in an implementation. These must be separated into distinct scenarios or elevated to distinct Rules.
- **Triage**: check-in
- **Decision**: Use multi-step Then with And clauses: "Then the cycle is rejected / And the involved tasks are identified / And the author is prompted to resolve the cycle." Standard Gherkin pattern for related outcomes within a single scenario.
- **Status**: resolved
- **Outcome**: Split the single bundled Then step in scenario dependency-mapping:3.4 into three steps: 'Then the cycle is rejected', 'And the involved tasks are identified', 'And the author is prompted to resolve the cycle'. [diff: +3/-1 requirements/dependency-mapping/requirements.feature.md]

### GAP-13: Presentation-order scenario misclassified under self-containment rule
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: A scenario in the self-contained-descriptions requirements verifies that tasks are presented to the author in dependency order. This scenario is placed under the "Task descriptions must be self-contained" rule, which it cannot test. Presentation ordering is a separate concern; the misclassification means the self-containment rule's test suite can pass even when self-containment is broken.
- **Triage**: check-in
- **Decision**: Create Rule 5 "Task descriptions are presented in dependency order" and move the presentation-order scenario there. Remove it from Rule 1.
- **Status**: resolved
- **Outcome**: Removed scenario 1.4 from Rule 1 (self-containment). Created new Rule 5 "Task descriptions are presented in dependency order" with the scenario renumbered as @self-contained-descriptions:5.1. Presentation ordering is now tested under its own dedicated rule. [diff: +10/-7 requirements/self-contained-descriptions/requirements.feature.md] Propagated to infra.md: removed dependency-order presentation content from self-contained-descriptions Rule 1 coverage row (now belongs to Rule 5); added Rule 5 row with verification approach.

### GAP-14: Then step describes internal non-execution rather than an observable outcome
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: A Then step in the self-contained-descriptions requirements describes an internal process that is not performed ("without format validation") rather than an externally observable outcome. There is no artifact or interaction to assert against. The Then step should state the observable result of the author's override being accepted.
- **Triage**: check-in
- **Decision**: Rewrite Then step to "the author's override is accepted regardless of format." States the semantic outcome (format is not enforced) as a positive observable claim.
- **Status**: resolved
- **Outcome**: Rewrote the Then step in scenario 4.2 from "the author's override is recorded without format validation" to "the author's override is accepted regardless of format", making the outcome a positive observable assertion rather than describing an internal non-action. [diff: +1/-1 requirements/self-contained-descriptions/requirements.feature.md]

### GAP-15: Multi-condition Then steps across workflow-validation scenarios
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: Several workflow-validation scenarios bundle multiple independently falsifiable conditions into single Then steps. Each condition can pass or fail independently of the others, making it impossible to identify which check failed. Each condition must become its own scenario or the rule must explicitly define the conditions as a named composite gate.
- **Triage**: check-in
- **Decision**: Split each bundled condition into its own scenario. Follow the markdown-gherkin numbering scheme (do NOT use #.#x suffixes); insert new scenarios using the next sequential number within the Rule. Affected scenarios: 1.2 (acyclic check and ref-resolution check), 1.3 (has-descriptions check and no-placeholders check), 2.1 (goal/action/criteria — resolved separately by GAP-17).
- **Status**: resolved
- **Outcome**: Split 1.2 into two scenarios: 1.2 (acyclic graph check) and 1.3 (task references resolve). Split 1.3 into two scenarios: 1.4 (all tasks have descriptions) and 1.5 (no placeholder text). Renumbered old 1.4 to 1.6 and old 1.5 to 1.7. Each Then step now tests exactly one condition. [diff: +41/-27 requirements/workflow-validation/requirements.feature.md] Propagated to integration.feature.md: updated workflow-validation scenario range from 1.1–1.5 to 1.1–1.7 to include the two scenarios added by splitting; extended description to note failure blocking (1.6) and correction-triggered re-validation (1.7).

### GAP-16: Scenario titles in requirements join two behaviors with an em-dash
- **Source**: requirements-critic
- **Severity**: low
- **Description**: Two scenario titles in the requirements use an em-dash to concatenate what are effectively two behaviors. Scenario titles must name only the single behavior being verified; titles that suggest multiple behaviors are prohibited by the writing-markdown-gherkin guidance.
- **Triage**: delegate
- **Decision**: Rename both em-dash scenario titles to single-behavior names. dependency-mapping:5.1 "Author removes a task — dependencies garbage-collected" → "Removed task dependencies garbage-collected". workflow-validation:1.5 "Author corrects validation error — re-validation unblocks progression" → "Corrected validation error unblocks pipeline progression".
- **Status**: resolved
- **Outcome**: Renamed scenario dependency-mapping:5.1 title from 'Author removes a task — dependencies garbage-collected' to 'Removed task dependencies garbage-collected'. [diff: +1/-1 requirements/dependency-mapping/requirements.feature.md] Propagated to requirements/workflow-validation/requirements.feature.md: renamed scenario 1.7 title (renumbered from 1.5 by GAP-15) from 'Author corrects validation error — re-validation unblocks progression' to 'Corrected validation error unblocks phase progression'.

### GAP-17: Structural sub-components required by final validation are never defined upstream
- **Source**: requirements-coverage-critic
- **Severity**: high
- **Description**: The structural completeness check in workflow-validation requires that each task description contain specific structural sub-components (goal statement, specific actions, acceptance criteria), but the description-writing capability never defines or requires these sub-components. The task schema in skill-file-generation lists the actual required fields — none of which decompose into those sub-components. The workflow-validation scenario is inconsistent with the schema definition and conflates self-containment content with structural integrity, meaning a developer implementing the description phase would produce output that the final validator would incorrectly reject.
- **Triage**: check-in
- **Decision**: Rewrite workflow-validation:2.1 to check actual structural integrity: field presence (id, subject, description, activeForm, blockedBy), correct types, unique IDs, and valid blockedBy references. The self-containment audit (goal/action/criteria) is already covered by workflow-validation:2.3 and should not be duplicated in 2.1.
- **Status**: resolved
- **Outcome**: Rewrote 2.1 from 'Structural completeness check' (goal/action/criteria) to 'Structural integrity check' verifying fsm.json field presence (id, subject, description, activeForm, blockedBy), correct types, unique IDs, and valid blockedBy references. Aligns with CMP-final-validation structural integrity definition in technical.md. [diff: +6/-6 requirements/workflow-validation/requirements.feature.md] Propagated to integration.feature.md: corrected 'structural completeness' to 'structural integrity' in the workflow-validation:2.1–2.4 coverage bullet to match the renamed scenario 2.1 title.

### GAP-18: Task removal leaves orphaned dependents without a reconnection specification
- **Source**: requirements-coverage-critic
- **Severity**: medium
- **Description**: The task removal scenario in the dependency-mapping requirements specifies that all blockedBy references to the removed task are cleared from remaining tasks, but does not address what happens to the ordering relationship between the removed task's predecessors and its dependents. Removing a middle node from a sequential chain silently converts sequential execution to parallel. The requirements are missing a scenario covering either automatic reconnection or an author prompt to resolve the disconnection.
- **Triage**: check-in
- **Decision**: Add a scenario: when a removed task has both predecessors and dependents, its dependents automatically inherit the removed task's blockedBy entries (preserving the ordering chain).
- **Status**: resolved
- **Outcome**: Added scenario dependency-mapping:5.4 'Removed task's dependents inherit its predecessors' specifying that dependents of a removed middle-node task inherit its blockedBy entries, preventing silent conversion of sequential execution to parallel. [diff: +6/-0 requirements/dependency-mapping/requirements.feature.md] Propagated to technical.md: updated CMP-dependency-map Remove operation to include predecessor inheritance — each dependent of the removed task inherits the removed task's blockedBy entries before the entry is removed and references are garbage-collected. Propagated to infra.md: updated dependency-mapping Rule 5 coverage row to include predecessor inheritance with verification step for middle-node removal.

### GAP-19: Confirmed-acceptance path for split and merge suggestions is undefined
- **Source**: requirements-coverage-critic
- **Severity**: medium
- **Description**: The split and merge suggestion scenarios in the self-contained-descriptions requirements end at the suggestion or author prompt without specifying the confirmed-acceptance outcome. Whether the task list is modified, whether the dependency graph is updated, and whether the pipeline continues or loops back after the author confirms is not defined in any requirement.
- **Triage**: check-in
- **Decision**: Add confirmed-acceptance scenarios for both split and merge. When the author confirms a split: the partial fsm.json is updated (new task added with max+1 ID, parent/child relationships propagated), and the dependency graph is re-validated. When the author confirms a merge: the partial fsm.json is updated (one task consolidated into the other), and the dependency graph is re-validated. Both operations continue the description-writing phase after re-validation.
- **Status**: resolved
- **Outcome**: Added scenario 3.4 (Author confirms a split suggestion) and scenario 3.5 (Author confirms a merge suggestion) under Rule 3. Split scenario covers: fsm.json update with next sequential ID, parent/child propagation, graph re-validation, and continuation. Merge scenario covers: fsm.json consolidation, graph re-validation, and continuation. [diff: +18/-0 requirements/self-contained-descriptions/requirements.feature.md] Propagated to infra.md: updated self-contained-descriptions Rule 3 coverage row to include confirmed split and merge behavior with fsm.json update and re-validation verification steps.

### GAP-20: integration.feature.md justification cites requirement scenario tags that do not exist
- **Source**: validation-critic
- **Severity**: medium
- **Description**: The integration.feature.md file justifies omitting integration scenarios by citing specific requirement scenario tags, but those tags do not exist in the change's requirements files. The cited scenario ranges extend beyond what was actually specified, making the argument that cross-capability coverage is already captured by single-capability requirements unverifiable against the actual requirement set.
- **Triage**: check-in
- **Decision**: Read the actual requirements files, verify cross-capability coverage is sufficient given all scenario changes from other gaps, then update integration.feature.md with only real scenario IDs.
- **Status**: resolved
- **Outcome**: Corrected four incorrect scenario references: self-contained-descriptions:2.3 (nonexistent) changed to 2.1-2.2; workflow-validation:2.1 in that bullet changed to 2.3 (the actual self-containment audit scenario); workflow-validation:1.1-1.6 corrected to 1.1-1.5 (no 1.6 exists); workflow-validation:2.1-2.12 corrected to 2.1-2.4 (only 4 scenarios exist). Updated descriptive text to match what the actual scenarios cover. [diff: +4/-4 integration.feature.md]

### GAP-21: Multi-source intake interaction sequence is unspecified and untested
- **Source**: validation-critic
- **Severity**: medium
- **Description**: When both intake sources are provided simultaneously, the requirements cover only the normalization outcome, not the user interaction sequence. Which source is processed first and how the results are combined is unspecified. The scope of each intake capability's scenarios is bounded to single-source use, leaving the combined intake path without coverage.
- **Triage**: check-in
- **Decision**: Add Rule 4 to workflow-intake requirements: "Both intake sources can be used together." Include a scenario specifying the interaction sequence: existing-skill analysis runs first, written descriptions second, brainstorming fills remaining gaps, then both are merged in normalization.
- **Status**: resolved
- **Outcome**: Added Rule 5 (@workflow-intake:5) "Both intake sources can be used together" with scenario 5.1 specifying the multi-source interaction sequence: existing-skill analysis first, written descriptions second, brainstorming fills remaining gaps, all merged during normalization. Numbered as Rule 5 (not 4) because Rule 4 already exists for brainstorming. [diff: +14/-0 requirements/workflow-intake/requirements.feature.md] Propagated to infra.md: added workflow-intake Rule 5 row 'Both intake sources can be used together' covering multi-source interaction sequence.

### GAP-22: infra.md coverage table references requirement scenario IDs that do not exist
- **Source**: design-for-test-critic
- **Severity**: high
- **Description**: The infra.md coverage table references requirement scenario IDs that do not exist in the requirements files. The scenario-specific setup section also references scenario IDs in skill-file-generation that are beyond the last defined scenario. The infra documents verification approaches for behaviors that have no traceable requirement, breaking the traceability chain from infra to requirements.
- **Triage**: check-in
- **Decision**: Investigate each phantom reference: determine whether each referenced behavior is real (missing scenario that should be added to requirements) or stale (typo that should be corrected). Fix accordingly — add missing requirement scenarios where behavior is real, correct IDs where stale.
- **Status**: resolved
- **Outcome**: Both phantom references were stale IDs (off-by-two). skill-file-generation:4.3 (directory creation) corrected to skill-file-generation:4.1 (correct placement includes directory creation). skill-file-generation:4.4 (collision detection) corrected to skill-file-generation:4.2 (collision prompts resolution). Both corrected IDs now reference scenarios that exist in the requirements files. [diff: +2/-2 infra.md]

### GAP-23: Cycle detection scenario absent from infra.md coverage table
- **Source**: design-for-test-critic
- **Severity**: medium
- **Description**: The dependency-mapping coverage row in infra.md covers fan-out, fan-in, and diamond pattern scenarios but omits the cycle detection scenario. Cycle detection requires a distinct setup and is a correctness-critical behavior. No verification approach is documented for it.
- **Triage**: check-in
- **Decision**: Extend the Rule 3 coverage row in infra.md to include @dependency-mapping:3.4 with setup (author specifies a circular dependency) and verification approach (manual: confirm the skill rejects and prompts for resolution).
- **Status**: resolved
- **Outcome**: Extended the dependency-mapping Rule 3 coverage row to include cycle detection and rejection in the 'What it covers' column, and added verification approach: specify dependencies that form a cycle, verify the skill rejects the cycle and prompts the author to resolve it. [diff: +1/-1 infra.md]

### GAP-24: No verification command for validate_fsm_tasks structural code change
- **Source**: design-for-test-critic
- **Severity**: low
- **Description**: The infra classifies the validate_fsm_tasks code change as automated structural verification but provides no runnable verification command. The testing strategy completeness checklist requires verification commands for all automated verification paths.
- **Triage**: delegate
- **Decision**: Read infra.md to find the validate_fsm_tasks entry. Add the pytest verification command for the description field validation test. If the test file path is not yet determined, add a placeholder indicating the command will be confirmed once the test file is written.
- **Status**: resolved
- **Outcome**: Added a pytest verification command (`pytest plugins/finite-skill-machine/tests/ -v -k "description"`) to the structural validation section, with a note that the test file path will be confirmed once the description field validation test is written. [diff: +4/-1 infra.md]

### GAP-25: Correction paths for non-self-containment failures at final validation are undefined
- **Source**: logic-critic
- **Severity**: medium
- **Description**: CMP-final-validation documents a correction mechanism only for self-containment failures. The correction paths for cycle detection failures and structural integrity failures are undefined. The requirements specify that actionable correction guidance must be provided for all failure types, but the design does not document what guidance applies or whether a failure type requires re-entering an earlier phase.
- **Triage**: check-in
- **Decision**: Read @workflow-validation:2.4 and @3.2 to assess what correction guidance those scenarios already specify. If sufficient, align CMP-final-validation in technical.md with that language. If truly absent, add minimal per-failure-type guidance consistent with the pipeline: cycle failures direct the author to re-enter dependency mapping; structural integrity failures provide in-place guidance with identification of the specific invalid field or reference.
- **Status**: resolved
- **Outcome**: Reviewed workflow-validation:2.4 and 3.2 — both specify 'actionable correction guidance' per failure but don't prescribe per-type paths. Replaced the single self-containment correction bullet with a structured 'Correction paths per failure type' block covering all four check types: self-containment (in-place correction), cycle detection (re-enter dependency mapping), structural integrity (in-place field/reference fix with specific identification), and name consistency (choose surviving name, update in-place). [diff: +6/-1 technical.md]

### GAP-26: Task merge mechanism is unspecified in the component design
- **Source**: logic-critic
- **Severity**: medium
- **Description**: CMP-descriptions specifies the split mechanism in detail (deterministic node expansion with dependency inheritance and re-validation) but provides no equivalent specification for merges. The design leaves undefined which task ID survives a merge, how blockedBy relationships from both tasks are reconciled, whether the dependency graph is re-validated, and what "adjacent" means in the context of a dependency graph.
- **Triage**: check-in
- **Decision**: Specify the merge mechanism in technical.md: the lower task ID survives; blockedBy entries are unioned (merged task inherits dependencies from both); the partial fsm.json is updated and the dependency graph is re-validated using the cycle detection script; "adjacent" means sharing a direct blockedBy edge.
- **Status**: resolved
- **Outcome**: Added a merge mechanism responsibility bullet to CMP-descriptions specifying: lower task ID survives, blockedBy entries unioned, all blockedBy references to removed task updated to surviving task, 'adjacent' defined as sharing a direct blockedBy edge, re-validation via CMP-cycle-detect-script. [diff: +1/-0 technical.md]

### GAP-27: Description-phase task restructuring invalidates the finalized dependency graph
- **Source**: integration-coverage-critic
- **Severity**: high
- **Description**: The description phase can trigger task splits and merges after dependency mapping has been finalized. The integration.feature.md argument that the pipeline is forward-only covers only modifications made during the dependency-mapping phase, not structural changes triggered by the description phase. When a split or merge occurs during description writing, the finalized dependency graph becomes stale. No scenario covers the dependency graph update and re-validation that must occur before the pipeline can continue.
- **Triage**: check-in
- **Decision**: CMP-descriptions is responsible for re-validating the dependency graph immediately after any confirmed split or merge using the cycle detection script. Pipeline continues to the next description only after re-validation passes. Document this responsibility in technical.md (CMP-descriptions) and update integration.feature.md to acknowledge this cross-capability dependency.
- **Status**: resolved
- **Outcome**: Added explicit pipeline gate responsibility to CMP-descriptions: after any confirmed split or merge, the pipeline does not continue to the next description until dependency graph re-validation passes. Updated the validation scope table to cover both splits and merges with the pipeline gate noted. [diff: +2/-1 technical.md] Propagated to requirements/self-contained-descriptions/requirements.feature.md: added Scenario Outline @self-contained-descriptions:3.6 covering the pipeline gate behavior — when re-validation detects a cycle after a confirmed split or merge, the description-writing phase does not continue and the author is prompted to resolve the cycle. Propagated to integration.feature.md: reframed forward-only pipeline justification paragraph as 'with one designed exception', added description of the split/merge callback and reference to self-contained-descriptions:3.4–3.5.
