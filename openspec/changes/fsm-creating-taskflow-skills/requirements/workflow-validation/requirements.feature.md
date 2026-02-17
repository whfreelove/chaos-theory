# Feature: Workflow Validation (workflow-validation)

<!--
MDG format. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

TERMINOLOGY (proposal language → Gherkin keyword):
- "Capability" → "Feature" (one Feature per capability)
- "Requirement" → "Rule" (requirements are grouped as Rules)
-->

## ADDED Requirements

`@workflow-validation:1`
### Rule: The skill SHALL perform incremental validation at each workflow phase

The skill SHALL validate outputs at the end of each phase (intake, dependency mapping, description writing) before proceeding to the next phase. Validation failure at any phase SHALL prevent progression until the author resolves the identified issues.

`@workflow-validation:1.1`
#### Scenario: Intake phase output validated before proceeding to dependency mapping

- Given the author has completed the intake phase and the skill has produced a step list
- When the skill validates the intake phase output
- Then the skill SHALL check that every step has a label and a description of the work it performs
- And the skill SHALL check that the step list contains at least one step
- And the skill confirms the intake output is valid before presenting the dependency mapping phase

`@workflow-validation:1.2`
#### Scenario: Dependency mapping output validated before proceeding to description writing

- Given the author has completed the dependency mapping phase
- When the skill validates the dependency mapping output
- Then the skill SHALL check that every task appears in the dependency graph
- And the skill SHALL check that no task references a dependency that does not exist in the step list
- And the skill SHALL check that no circular dependencies exist in the graph
- And the skill confirms the dependency output is valid before presenting the description writing phase

`@workflow-validation:1.3`
#### Scenario: Description writing output validated before proceeding to file generation

- Given the author has completed the description writing phase for all tasks
- When the skill validates the description writing output
- Then the skill SHALL check that every task has a written description
- And the skill SHALL check that no description is empty or contains only placeholder text
- And the skill confirms the description output is valid before presenting the file generation phase

`@workflow-validation:1.3.1`
#### Scenario: Validation failure at description writing phase catches placeholder text

- Given the author has written a task description
- And the description contains only placeholder text (e.g., "TODO: write this later")
- When the skill validates the description writing output
- Then the skill reports the specific task whose description contains placeholder text
- And the skill does not present the file generation phase
- And the skill asks the author to write a substantive description before proceeding

`@workflow-validation:1.3.2`
#### Scenario: Advancement blocked when skipped tasks have incomplete descriptions

- Given the author has skipped one or more tasks during the description writing phase
- And those skipped tasks do not have written descriptions
- When the author attempts to advance to the file generation phase
- Then the skill reports which tasks have incomplete descriptions
- And the skill does not present the file generation phase
- And the skill blocks advancement until all tasks have descriptions

`@workflow-validation:1.4`
#### Scenario: Validation failure at intake phase prevents progression

- Given the author has completed the intake phase
- And the step list contains a step with no description of the work it performs
- When the skill validates the intake phase output
- Then the skill reports the specific step that lacks a description
- And the skill does not present the dependency mapping phase
- And the skill asks the author to correct the issue before proceeding

`@workflow-validation:1.5`
#### Scenario: Validation failure at dependency mapping phase prevents progression

- Given the author has completed the dependency mapping phase
- And a task references a dependency that does not exist in the step list
- When the skill validates the dependency mapping output
- Then the skill reports the task and the nonexistent dependency it references
- And the skill does not present the description writing phase
- And the skill asks the author to correct the dependency before proceeding

`@workflow-validation:1.6`
#### Scenario: Author corrects validation error and re-validates successfully

- Given the skill has reported a validation error within a task
- And the skill has presented the issue and asked the author to correct it
- And the author has corrected the issue the skill identified
- When the skill re-validates the phase output within the same task
- Then the skill confirms the output is now valid
- And the task completes and the skill proceeds to the next phase

`@workflow-validation:2`
### Rule: The skill SHALL perform comprehensive final validation before deployment

The skill SHALL run a complete validation pass across all workflow outputs before the skill files are finalized. This final check covers cross-cutting concerns that incremental phase checks cannot catch, including self-containment of descriptions, dependency graph integrity, and structural correctness of the task definition.

`@workflow-validation:2.1`
#### Scenario: Final validation checks structural completeness of each task description

- Given the author has completed all phases and the skill is performing final validation
- When the skill evaluates each task description against the self-containment checklist
- Then the skill SHALL verify each description contains a goal statement (what the task accomplishes), specific actions (what the agent should do), and acceptance criteria (how to know when done)

`@workflow-validation:2.1.1`
#### Scenario: Final validation checks term definition coverage in each task description

- Given the author has completed all phases and the skill is performing final validation
- When the skill evaluates each task description against the self-containment checklist
- Then the skill SHALL verify every term in each description is either defined within the description or includes a pointer to its definition in code or project documentation

`@workflow-validation:2.1.2`
#### Scenario: Final validation detects external references in task descriptions

- Given the author has completed all phases and the skill is performing final validation
- When the skill evaluates each task description against the self-containment checklist
- Then the skill SHALL flag any description that references the SKILL.md text, sibling tasks, or assumes context not present in the description

`@workflow-validation:2.2`
#### Scenario: Final validation checks dependency graph for cycles using topological sort

- Given the author has completed all phases and the skill is performing final validation
- When the skill performs a topological sort on the dependency graph
- Then the skill SHALL verify that the sort consumes all nodes
- And if any nodes remain unconsumed, the skill reports the set of unconsumed task IDs and labels as involved in cycle(s)

`@workflow-validation:2.4`
#### Scenario: Final validation failure identifies specific issues to fix

- Given the skill is performing final validation
- And the final validation detects one or more issues across different validation checks
- When the skill reports the final validation results
- Then the skill lists each issue with the affected task or artifact
- And each listed issue includes a description of what is wrong
- And the skill does not finalize the skill files until all issues are resolved

`@workflow-validation:2.5`
#### Scenario: Self-containment failure corrected in-place during final validation

- Given the skill is performing final validation
- And the self-containment audit flags a description that references context not present in the description itself
- When the skill reports the self-containment issue to the author
- Then the author edits the description directly within the final validation task
- And the skill re-evaluates the corrected description for self-containment
- And no phase regression to the description writing phase is required

`@workflow-validation:2.6`
#### Scenario: Structural validation passes when all required fields and metadata are present

- Given the skill is performing final validation on the generated task definition
- And every task entry contains all 5 core fields (`id`, `subject`, `description`, `activeForm`, `blockedBy`) and `metadata` with the skill name
- When the skill checks the structural integrity of the task definition
- Then the structural validation check passes
- And the skill confirms the task definition structure is valid

`@workflow-validation:2.7`
#### Scenario: Structural validation fails when a required field is missing

- Given the skill is performing final validation on the generated task definition
- And one task entry is missing a required field (e.g., `activeForm` is absent)
- When the skill checks the structural integrity of the task definition
- Then the structural validation check fails
- And the skill reports the specific task entry and the specific missing field
- And the skill does not finalize until the missing field is added

`@workflow-validation:2.8`
#### Scenario: Structural validation fails when a field has the wrong type

- Given the skill is performing final validation on the generated task definition
- And one task entry has a field with an incorrect type (e.g., `blockedBy` is a string instead of an array of integers)
- When the skill checks the structural integrity of the task definition
- Then the structural validation check fails
- And the skill reports the specific task entry, the field name, the expected type, and the actual type
- And the skill does not finalize until the field type is corrected

`@workflow-validation:2.10`
#### Scenario: Structural validation fails when metadata has empty fsm value

- Given the skill is performing final validation on the generated task definition
- And one task entry has metadata with an `fsm` key but the value is an empty string
- When the skill checks the structural integrity of the task definition
- Then the structural validation check fails
- And the skill reports the specific task entry and that the `fsm` metadata value must be a non-empty string matching the skill name
- And the skill does not finalize until the metadata content is corrected

`@workflow-validation:2.11`
#### Scenario: Structural validation fails when blockedBy references a non-existent task ID

- Given the skill is performing final validation on the generated task definition
- And one task entry's `blockedBy` array contains an ID that does not correspond to any task in the generated output
- When the skill checks the structural integrity of the task definition
- Then the structural validation check fails
- And the skill reports the specific task entry and the invalid `blockedBy` reference
- And the skill does not finalize until the dangling reference is corrected

`@workflow-validation:3`
### Rule: The skill SHALL present validation results clearly to the author

The skill SHALL communicate validation outcomes so the author can identify what passed, what failed, and how to fix any issues. Passing validations confirm readiness to proceed; failing validations provide actionable guidance.

`@workflow-validation:3.1`
#### Scenario: Passing validation confirms readiness to proceed

- Given the skill has completed a validation check at any phase or during final validation
- And all checks in that validation pass
- When the skill presents the validation results to the author
- Then the skill confirms that validation passed
- And the skill states that the workflow is ready to proceed to the next step

`@workflow-validation:3.2`
#### Scenario: Failing validation lists specific issues with actionable guidance

- Given the skill has completed a validation check at any phase or during final validation
- And one or more checks in that validation have failed
- When the skill presents the validation results to the author
- Then the skill lists each failing check with the specific issue detected
- And each listed issue includes guidance on how the author can resolve it
- And the skill does not proceed until the author addresses the reported issues

## MODIFIED Requirements

None.

## REMOVED Requirements

None.

## RENAMED Requirements

None.
