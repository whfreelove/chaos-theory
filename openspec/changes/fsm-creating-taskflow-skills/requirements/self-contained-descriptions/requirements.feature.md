# Feature: Self-Contained Descriptions (self-contained-descriptions)

<!--
MDG format. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

TERMINOLOGY (proposal language → Gherkin keyword):
- "Capability" → "Feature" (one Feature per capability)
- "Requirement" → "Rule" (requirements are grouped as Rules)
-->

## ADDED Requirements

`@self-contained-descriptions:1`
### Rule: The skill SHALL guide authors to write descriptions that serve as the sole instruction source

Each task description MUST contain all context an agent needs to execute the task independently. After context compaction removes the original skill text, the task description becomes the only instruction the agent receives. The skill SHALL detect descriptions that depend on external context and guide the author to make them self-contained.

`@self-contained-descriptions:1.1`
#### Scenario: Description includes all necessary context for independent execution

- Given the author has written a task description
- And the description contains the goal, relevant constraints, and expected outcome
- When the skill evaluates the description for self-containment
- Then the skill SHALL accept the description without modification
- And the skill SHALL NOT prompt the author to add additional context

`@self-contained-descriptions:1.2`
#### Scenario: Description omitting critical context triggers skill guidance to add it

- Given the author has written a task description
- And the description states an action but omits the constraints governing that action
- When the skill evaluates the description for self-containment
- Then the skill SHALL flag the missing context and prompt the author to incorporate the missing constraints into the description
- And the skill SHALL explain that the description must stand alone after the original skill text is compacted away

`@self-contained-descriptions:1.3`
#### Scenario: Description that assumes access to original skill text triggers correction

- Given the author has written a task description
- And the description contains phrases such as "as described in the skill" or "per the instructions above"
- When the skill evaluates the description for self-containment
- Then the skill SHALL flag the external reference
- And the skill SHALL instruct the author to replace the reference with the actual content it points to
- And the skill SHALL explain that context compaction removes the original skill text

`@self-contained-descriptions:1.4`
#### Scenario: Author revises a previously approved description during the description writing phase

- Given the author has already approved a task description during the description writing phase
- And the author returns to revise that previously approved description
- When the author submits the modified description
- Then the skill SHALL re-evaluate the modified description for self-containment using the same rules (goal, constraints, expected outcome present; no external references; no inter-task references)
- And the skill SHALL NOT accept the modification until the revised description passes all self-containment checks

`@self-contained-descriptions:1.5`
#### Scenario: Skill presents tasks in dependency order during description writing

- Given the author has completed the dependency mapping phase with multiple tasks
- When the skill begins the description writing phase
- Then the skill SHALL present tasks one at a time in dependency order
- And the author SHALL be able to skip to a specific task
- And the author SHALL be able to return to revise a previously completed description

`@self-contained-descriptions:2`
### Rule: The skill SHALL ensure descriptions contain no forward or backward references to other tasks

Task descriptions MUST NOT reference other task IDs, task names, or assume knowledge of sibling task content. Each description is consumed in isolation; the agent executing a task has no guaranteed visibility into other tasks in the workflow.

`@self-contained-descriptions:2.1`
#### Scenario: Description referencing another task by name triggers correction

- Given the author has written a task description
- And the description contains a phrase such as "use the output format defined in the Validation task"
- When the skill evaluates the description for inter-task references
- Then the skill SHALL flag the reference to the named task
- And the skill SHALL instruct the author to inline the referenced information directly into the description

`@self-contained-descriptions:2.2`
#### Scenario: Description referencing "the previous task" triggers correction

- Given the author has written a task description
- And the description contains a phrase such as "continue from the previous task" or "after the prior step completes"
- When the skill evaluates the description for inter-task references
- Then the skill SHALL flag the sequential reference
- And the skill SHALL instruct the author to state the required preconditions explicitly within the description
- And the skill SHALL explain that task execution order is managed by dependencies, not by description text

`@self-contained-descriptions:2.3`
#### Scenario: Description with implicit ordering assumption triggers correction

- Given the author has written a task description
- And the description contains a phrase such as "at this point the configuration will already exist"
- And no explicit precondition in the description establishes that the configuration exists
- When the skill evaluates the description for inter-task references
- Then the skill SHALL flag the implicit assumption about prior task output
- And the skill SHALL instruct the author to either state the precondition explicitly or remove the assumption

`@self-contained-descriptions:3`
### Rule: The skill SHALL guide appropriate task sizing

The skill SHALL guide authors toward task descriptions that are small enough to survive context compaction but large enough to be meaningful units of work. Descriptions that are too large risk partial context loss within a single task; descriptions that are too small create unnecessary execution overhead.

`@self-contained-descriptions:3.1`
#### Scenario: Overly large description prompts splitting guidance

- Given the author has written a task description
- And the description covers multiple distinct objectives or deliverables
- When the skill evaluates the description for appropriate sizing
- Then the skill SHALL flag the distinct objectives and provide splitting guidance, recommending separate tasks for each objective
- And the skill SHALL explain that smaller descriptions are more resilient to context compaction

`@self-contained-descriptions:3.2`
#### Scenario: Overly small description prompts merging guidance

- Given the author has written a task description
- And the description cannot meaningfully populate all 4 self-containment checklist items (goal statement, specific actions, acceptance criteria, no undefined references) because the checklist items become trivially redundant
- When the skill evaluates the description for appropriate sizing
- Then the skill SHALL flag the description as too granular to justify a separate task
- And the skill SHALL recommend merging the action into a related task where it contributes to a meaningful outcome

`@self-contained-descriptions:3.3`
#### Scenario: Appropriately sized description accepted without modification

- Given the author has written a task description
- And the description addresses a single coherent objective with a clear deliverable
- And the description is neither trivially small nor spanning multiple distinct objectives
- When the skill evaluates the description for appropriate sizing
- Then the skill SHALL accept the description without sizing-related modification

`@self-contained-descriptions:4`
### Rule: The skill SHALL auto-generate activeForm from task labels

The skill SHALL derive a present-continuous form (activeForm) from each task's label to be used as a spinner display during task execution. The generated activeForm is presented to the author for confirmation or override.

`@self-contained-descriptions:4.1`
#### Scenario: Skill generates activeForm from task label for author confirmation

- Given the author has defined a task with label "Validate dependencies"
- When the skill generates the activeForm for the task
- Then the skill SHALL present "Validating dependencies" as the proposed activeForm
- And the author SHALL be able to confirm or override the generated activeForm

`@self-contained-descriptions:4.2`
#### Scenario: Author-provided activeForm override accepted without format validation

- Given the skill has generated an activeForm value in present-continuous form for a task
- And the author chooses to override the generated activeForm with custom text
- When the skill receives the author's override
- Then the skill SHALL accept the author-provided activeForm as-is
- And the skill SHALL NOT validate the override for present-continuous form

## MODIFIED Requirements

None.

## REMOVED Requirements

None.

## RENAMED Requirements

None.
