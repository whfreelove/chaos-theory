# Feature: Workflow validation (workflow-validation)

## ADDED Requirements

`@workflow-validation:1`
### Rule: Incremental validation gates progression at each phase

`@workflow-validation:1.1`
#### Scenario: Intake phase validation passes when step list is complete

- Given the author has completed workflow intake
- And the step list contains at least one labeled step
- When intake validation runs
- Then validation passes

`@workflow-validation:1.2`
#### Scenario: Dependency phase validation passes when graph is acyclic

- Given dependency mapping has produced a dependency graph
- And the graph contains no cycles
- When dependency validation runs
- Then validation passes

`@workflow-validation:1.3`
#### Scenario: Dependency phase validation passes when all task references resolve

- Given dependency mapping has produced a dependency graph
- And all blockedBy references point to existing tasks
- When dependency validation runs
- Then validation passes

`@workflow-validation:1.4`
#### Scenario: Description phase validation passes when all tasks have descriptions

- Given description writing has produced task descriptions
- And every task has a non-empty description
- When description validation runs
- Then validation passes

`@workflow-validation:1.5`
#### Scenario: Description phase validation passes when no descriptions contain placeholder text

- Given description writing has produced task descriptions
- And no description contains placeholder text
- When description validation runs
- Then validation passes

`@workflow-validation:1.6`
#### Scenario: Validation failure blocks phase progression

- Given validation has run at the end of a phase
- When validation detects an issue
- Then the skill reports the issue and does not advance to the next phase

`@workflow-validation:1.7`
#### Scenario: Corrected validation error unblocks phase progression

- Given a validation failure has blocked phase progression
- When the author corrects the reported issue
- Then the workflow advances to the next phase

---

`@workflow-validation:2`
### Rule: A comprehensive final validation runs before deployment

`@workflow-validation:2.1`
#### Scenario: Structural integrity check passes

- Given the fsm.json artifact has been finalized
- When final validation runs the structural integrity check
- Then each entry contains `id`, `subject`, `description`, `activeForm`, and `blockedBy` fields
- And each field has the correct type
- And all IDs are unique
- And all `blockedBy` references resolve to existing IDs

`@workflow-validation:2.2`
#### Scenario: Final cycle detection catches dependency issues

- Given the workflow's dependency graph has been finalized
- When final validation runs cycle detection
- Then validation reports any cycles found and blocks deployment until they are resolved

`@workflow-validation:2.3`
#### Scenario: Self-containment audit passes

- Given all task descriptions have been written
- When final validation runs the self-containment audit
- Then validation passes if no description contains cross-task references or external references

`@workflow-validation:2.4`
#### Scenario: Final validation failure identifies specific issues with correction guidance

- Given final validation has run
- When one or more checks fail
- Then the skill lists each failed check with the specific task or field involved and guidance for correction

---

`@workflow-validation:3`
### Rule: Validation results are presented clearly to the author

`@workflow-validation:3.1`
#### Scenario: Passing validation confirms workflow completion

- Given all validation checks have passed
- When the final validation result is presented
- Then the workflow is complete
- And the generated skill is ready for use

`@workflow-validation:3.2`
#### Scenario: Failing validation lists specific issues with guidance

- Given one or more validation checks have failed
- When the validation result is presented
- Then the skill lists each issue specifically, identifying the affected task and providing actionable correction guidance

## MODIFIED Requirements

## REMOVED Requirements

## RENAMED Requirements
