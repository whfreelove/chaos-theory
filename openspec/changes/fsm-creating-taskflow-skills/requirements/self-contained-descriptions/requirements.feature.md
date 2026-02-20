# Feature: Self-contained descriptions (self-contained-descriptions)

## ADDED Requirements

`@self-contained-descriptions:1`
### Rule: Task descriptions must be self-contained

`@self-contained-descriptions:1.1`
#### Scenario: Description with all necessary context accepted

- Given the author writes a task description that includes all context needed to execute the task
- When the skill evaluates the description
- Then the description is accepted and no correction is requested

`@self-contained-descriptions:1.2`
#### Scenario: Description missing execution context triggers correction

- Given the author writes a task description that omits context required to execute the task
- When the skill evaluates the description
- Then the skill identifies the missing context and requests that the author add it

`@self-contained-descriptions:1.3`
#### Scenario: External reference to skill text triggers correction

- Given the author writes a task description that references the skill document (e.g., "as described in the skill")
- When the skill evaluates the description
- Then the skill flags the external reference and requires the author to inline the referenced content

`@self-contained-descriptions:1.4`
#### Scenario: Tasks presented to author in dependency order

- Given the workflow has been mapped with dependencies
- When the description writing phase begins
- Then the skill presents tasks to the author in dependency order, with prerequisites before dependents

---

`@self-contained-descriptions:2`
### Rule: Task descriptions must not reference other tasks

`@self-contained-descriptions:2.1`
#### Scenario: Reference to another task by name triggers inlining

- Given the author writes a task description that references another task by name
- When the skill evaluates the description
- Then the skill requires the author to inline the relevant content from the referenced task

`@self-contained-descriptions:2.2`
#### Scenario: Continuation language triggers precondition clarification

- Given the author writes a task description that assumes prior conversation state (e.g., "continue from the previous task")
- When the skill evaluates the description
- Then the skill requires the author to state the preconditions explicitly in the description

---

`@self-contained-descriptions:3`
### Rule: Task descriptions must be appropriately sized

`@self-contained-descriptions:3.1`
#### Scenario: Overly large description triggers split guidance

- Given the author writes a task description that spans multiple distinct actions
- When the skill evaluates the description
- Then the skill suggests splitting the task and prompts the author to define the boundary

`@self-contained-descriptions:3.2`
#### Scenario: Overly small description triggers merge guidance

- Given the author writes a task description for a trivial action that could be part of a larger task
- When the skill evaluates the description
- Then the skill suggests merging it with an adjacent task and prompts the author to confirm

`@self-contained-descriptions:3.3`
#### Scenario: Appropriately sized description accepted

- Given the author writes a task description that is focused on a single meaningful action
- When the skill evaluates the description
- Then the description is accepted without guidance

---

`@self-contained-descriptions:4`
### Rule: Each task has an activeForm field

`@self-contained-descriptions:4.1`
#### Scenario: Skill generates activeForm for author confirmation

- Given the author has written a task description and subject
- When the description is accepted
- Then the skill generates a present-continuous activeForm and presents it for author confirmation

`@self-contained-descriptions:4.2`
#### Scenario: Author-provided activeForm override accepted

- Given the skill has generated an activeForm
- When the author provides their own activeForm text instead
- Then the author's override is recorded without format validation

## MODIFIED Requirements

## REMOVED Requirements

## RENAMED Requirements
