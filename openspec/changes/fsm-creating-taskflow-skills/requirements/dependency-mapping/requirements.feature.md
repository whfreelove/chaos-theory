# Feature: Dependency mapping (dependency-mapping)

## ADDED Requirements

`@dependency-mapping:1`
### Rule: Serial execution patterns are encoded as sequential blockedBy relationships

`@dependency-mapping:1.1`
#### Scenario: Linear chain encoded as sequential dependencies

- Given the author identifies three tasks that must execute in order
- When dependency mapping runs
- Then each task is configured to block the next task in the chain

`@dependency-mapping:1.2`
#### Scenario: Author confirms explicit ordering

- Given the author specifies that two tasks must run in a particular sequence
- When the dependency is presented for confirmation
- Then the author confirms and the ordering is recorded

---

`@dependency-mapping:2`
### Rule: Parallel execution patterns are encoded as tasks with no blocking relationship

`@dependency-mapping:2.1`
#### Scenario: Independent tasks encoded with no blockedBy

- Given the author identifies tasks that can execute concurrently
- When dependency mapping runs
- Then those tasks have no blockedBy entries and can run simultaneously

`@dependency-mapping:2.2`
#### Scenario: Author confirms parallel grouping

- Given the skill identifies tasks that appear to be independent
- When the parallel grouping is presented for author confirmation
- Then the author confirms and the tasks remain ungrouped with no blocking relationships

---

`@dependency-mapping:3`
### Rule: Fan-in and fan-out patterns are encoded using blockedBy relationships

`@dependency-mapping:3.1`
#### Scenario: Fan-out pattern encoded from one task to multiple independent tasks

- Given the author identifies a task that must complete before several independent tasks can begin
- When dependency mapping runs
- Then each downstream task lists the upstream task in its blockedBy field

`@dependency-mapping:3.2`
#### Scenario: Fan-in pattern encoded from multiple tasks to one successor

- Given the author identifies several tasks that must all complete before a successor can begin
- When dependency mapping runs
- Then the successor task lists all predecessor tasks in its blockedBy field

`@dependency-mapping:3.3`
#### Scenario: Diamond pattern encoded as fan-out followed by fan-in

- Given the author identifies a source task, two parallel tasks, and a convergence task
- When dependency mapping runs
- Then the two parallel tasks block on the source and the convergence task blocks on both parallel tasks

`@dependency-mapping:3.4`
#### Scenario: Circular dependency detected and rejected

- Given the author specifies dependencies that form a cycle
- When dependency mapping validates the graph
- Then the skill rejects the cycle, identifies the tasks involved, and prompts the author to resolve it

---

`@dependency-mapping:4`
### Rule: The dependency graph is presented for author confirmation before proceeding

`@dependency-mapping:4.1`
#### Scenario: Dependency graph presented for review

- Given dependency mapping has produced a complete graph
- When the graph is ready
- Then the skill presents the full dependency graph to the author before proceeding

`@dependency-mapping:4.2`
#### Scenario: Author approves dependency graph

- Given the dependency graph has been presented
- When the author confirms the graph is correct
- Then dependency mapping is finalized and the workflow advances

`@dependency-mapping:4.3`
#### Scenario: Author modifies dependency graph

- Given the dependency graph has been presented
- When the author requests changes to dependencies
- Then the skill incorporates the changes and presents the updated graph for re-confirmation

---

`@dependency-mapping:5`
### Rule: Task list modifications during dependency mapping update the dependency graph

`@dependency-mapping:5.1`
#### Scenario: Author removes a task — dependencies garbage-collected

- Given the dependency graph has been presented
- When the author removes a task from the step list
- Then all blockedBy references to the removed task are removed from remaining tasks

`@dependency-mapping:5.2`
#### Scenario: Author adds a task during dependency mapping

- Given the dependency graph has been presented
- When the author adds a new task
- Then the skill prompts the author to specify the new task's dependencies before re-presenting the graph

`@dependency-mapping:5.3`
#### Scenario: Author renames a task — dependencies preserved

- Given the dependency graph has been presented
- When the author renames a task
- Then all blockedBy references to the renamed task are updated to the new name

---

`@dependency-mapping:6`
### Rule: Single-task workflows produce a valid but empty dependency graph

`@dependency-mapping:6.1`
#### Scenario: Single task produces empty dependency graph

- Given the workflow contains exactly one task
- When dependency mapping runs
- Then the task has no blockedBy entries and the graph is presented with a note that no dependencies exist

## MODIFIED Requirements

## REMOVED Requirements

## RENAMED Requirements
