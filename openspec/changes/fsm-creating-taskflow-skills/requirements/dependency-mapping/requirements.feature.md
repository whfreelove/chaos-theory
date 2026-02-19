# Feature: Dependency Mapping (dependency-mapping)

<!--
MDG format. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

TERMINOLOGY (proposal language → Gherkin keyword):
- "Capability" → "Feature" (one Feature per capability)
- "Requirement" → "Rule" (requirements are grouped as Rules)
-->

## ADDED Requirements

`@dependency-mapping:1`
### Rule: The skill SHALL guide encoding of serial execution patterns

The skill SHALL help authors express sequential task dependencies where each task must complete before the next begins. Serial chains are presented as ordered sequences where each task blocks the next.

`@dependency-mapping:1.1`
#### Scenario: Linear chain of three tasks produces correct dependency ordering

- Given the author has defined three tasks: "scaffold," "implement," and "verify"
- And the author indicates they must execute in that exact order
- When the skill encodes the serial dependency chain
- Then the skill presents "scaffold" as blocking "implement"
- And the skill presents "implement" as blocking "verify"
- And no task is shown as executable before its predecessor completes

`@dependency-mapping:1.2`
#### Scenario: Author specifies explicit ordering for steps with no natural sequence

- Given the author has defined two tasks with no inherent ordering relationship
- When the author specifies that the first task must complete before the second
- Then the skill encodes the first task as blocking the second
- And the skill confirms the serial dependency back to the author

`@dependency-mapping:1.3`
#### Scenario: Blocking direction presented correctly to the author

- Given the author declares that task "setup" blocks task "build"
- When the skill encodes the dependency
- Then the skill presents task "build" as blocked by "setup"
- And the skill does not present "setup" as blocked by "build"

`@dependency-mapping:2`
### Rule: The skill SHALL guide encoding of parallel execution patterns

The skill SHALL help authors identify tasks that can execute concurrently with no dependencies between them. Tasks with no blocking relationship between them are presented as independent.

`@dependency-mapping:2.1`
#### Scenario: Independent tasks presented with no blocking relationship between them

- Given the author has defined three tasks: "lint," "unit-test," and "type-check"
- And no task depends on the output of another
- When the skill analyzes the dependency relationships
- Then the skill presents all three tasks with no blocking relationship between them
- And no task is shown as blocked by another

`@dependency-mapping:2.2`
#### Scenario: Author confirms parallel grouping

- Given the skill has identified two tasks with no blocking relationship between them
- When the skill presents the parallel grouping to the author
- And the author confirms that neither task depends on the other
- Then the skill encodes both tasks with no dependency between them

`@dependency-mapping:3`
### Rule: The skill SHALL guide encoding of fan-in and fan-out patterns

The skill SHALL help authors express convergence (fan-in) and divergence (fan-out) in task dependencies. Fan-out produces multiple independent tasks from a single predecessor; fan-in requires multiple tasks to complete before a single successor begins.

`@dependency-mapping:3.1`
#### Scenario: Fan-out from single task to multiple independent tasks

- Given the author has defined a task "generate-config" that must complete first
- And the author has defined three tasks that each depend only on "generate-config"
- When the skill encodes the fan-out pattern
- Then the skill presents "generate-config" as blocking all three downstream tasks
- And no blocking relationship is shown between the three downstream tasks

`@dependency-mapping:3.2`
#### Scenario: Fan-in where multiple tasks converge to a single successor

- Given the author has defined three tasks: "build-api," "build-ui," and "build-docs"
- And the author has defined a task "deploy" that depends on all three
- When the skill encodes the fan-in pattern
- Then the skill presents each of the three tasks as blocking "deploy"
- And "deploy" is shown as not executable until all three predecessors complete

`@dependency-mapping:3.3`
#### Scenario: Multi-stage fan-out followed by fan-in (diamond pattern)

- Given the author has defined a task "setup" that fans out to "path-a" and "path-b"
- And the author has defined a task "merge" that depends on both "path-a" and "path-b"
- When the skill encodes the diamond dependency pattern
- Then "setup" is presented as blocking both "path-a" and "path-b"
- And no blocking relationship is shown between "path-a" and "path-b"
- And both "path-a" and "path-b" are presented as blocking "merge"

`@dependency-mapping:3.4`
#### Scenario: Circular dependency detected during dependency mapping

- Given the author has encoded dependencies where task A blocks task B, task B blocks task C, and task C blocks task A
- When the skill validates the dependency graph during the dependency mapping phase
- Then the skill detects the circular dependency before proceeding to description writing
- And the skill reports the tasks involved in the cycle
- And the skill asks the author to resolve the cycle before continuing

`@dependency-mapping:4`
### Rule: The skill SHALL present the dependency graph for author confirmation

Before finalizing, the skill SHALL present the complete dependency structure for author review and approval. The presentation MUST show all blocking relationships, parallel groups, and execution order clearly enough for the author to verify correctness.

`@dependency-mapping:4.1`
#### Scenario: Dependency graph presented to author for review

- Given the skill has encoded all task dependencies
- When the skill reaches the confirmation step
- Then the skill SHALL present a summary showing every task and its blocking relationships
- And the summary SHALL distinguish serial chains from parallel groups
- And the summary SHALL identify fan-in and fan-out points

`@dependency-mapping:4.1.1`
#### Scenario: Dependency graph supports cycle detection via topological sort

- Given the skill has encoded all task dependencies
- When the skill constructs the dependency graph
- Then the dependency graph SHALL support cycle detection via topological sort
- And the skill SHALL be able to determine whether the graph is acyclic before proceeding

`@dependency-mapping:4.2`
#### Scenario: Author modifies dependencies after review

- Given the skill has presented the dependency summary to the author
- And the author identifies a dependency that SHALL be changed
- When the author requests a modification to the blocking relationship
- Then the skill updates the dependency encoding to reflect the change
- And the skill presents the revised summary for further review

`@dependency-mapping:4.3`
#### Scenario: Author approves dependencies as presented

- Given the skill has presented the dependency summary to the author
- When the author confirms the dependencies are correct
- Then the skill finalizes the dependency encoding
- And no further dependency modifications are made for this workflow

`@dependency-mapping:4.4`
#### Scenario: Author reviews complex graph with fan-out and fan-in combined

- Given the skill has encoded a dependency graph containing both fan-out and fan-in patterns
- When the skill presents the dependency summary to the author
- Then the summary shows every task and its blocking relationships including the fan-out and fan-in points
- And the summary distinguishes which tasks have no blocking relationship between them within the complex graph
- And the author SHALL be able to confirm the graph matches the intended workflow

`@dependency-mapping:5`
### Rule: The skill SHALL support step list modifications during dependency mapping

The step list SHALL be mutable during the dependency mapping phase. The author MAY add, remove, or rename tasks while encoding dependencies. Each modification SHALL trigger a dependency graph update and re-validation to maintain referential integrity.

`@dependency-mapping:5.1`
#### Scenario: Author removes a task during dependency mapping

- Given the author is in the dependency mapping phase with an approved step list
- And the author determines that a task is redundant
- When the author requests removal of the task from the step list
- Then the skill removes the task and all dependency references to that task from the graph
- And the skill re-validates the dependency graph for integrity
- And the skill presents the updated graph to the author for confirmation

`@dependency-mapping:5.2`
#### Scenario: Author adds a task during dependency mapping

- Given the author is in the dependency mapping phase with an approved step list
- And the author identifies a missing task that needs to be added
- When the author provides the new task's label and description
- Then the skill SHALL apply a lightweight quality check to the provided label and description verifying: the label is present and non-empty, the description is non-empty and identifies distinct work (specificity), and the task describes a concrete action (actionability)
- And the lightweight check SHALL omit splitting guidance, iterative prompting for clarification, and full scope evaluation
- And the skill SHALL add the task to the step list and the dependency graph only after the quality check passes
- And the skill SHALL ask the author to specify the new task's dependency relationships
- And the skill SHALL re-validate the dependency graph for integrity

`@dependency-mapping:5.3`
#### Scenario: Author renames a task during dependency mapping

- Given the author is in the dependency mapping phase with an approved step list
- And the author wants to change a task's label to better reflect its purpose
- When the author provides the new label for the task
- Then the skill updates the task label in the step list and the dependency graph
- And all existing dependency relationships for the renamed task are preserved
- And the skill presents the updated graph to the author for confirmation

`@dependency-mapping:5.4`
#### Scenario: Author modifies a dependency during graph review introducing a circular dependency

- Given the author is in the dependency mapping phase and is reviewing the dependency graph
- And the current dependency graph is acyclic
- When the author modifies a dependency relationship that introduces a circular dependency
- Then the skill SHALL detect the cycle during re-validation
- And the skill SHALL report the tasks involved in the cycle to the author
- And the skill SHALL NOT accept the modification until the cycle is resolved

`@dependency-mapping:6`
### Rule: The skill SHALL handle single-task workflows during dependency mapping

When the workflow contains only one task, the dependency mapping phase SHALL confirm the trivially empty dependency graph with the author and produce an empty blockedBy array for the single task.

`@dependency-mapping:6.1`
#### Scenario: Single-task workflow produces empty dependency graph

- Given the author has defined a workflow with exactly one task
- When the skill performs dependency mapping for the single task
- Then the task's blockedBy array is empty (no dependencies to encode)
- And the skill confirms the trivially empty dependency graph with the author
- And the skill proceeds to the next phase after author confirmation

## MODIFIED Requirements

None.

## REMOVED Requirements

None.

## RENAMED Requirements

None.
