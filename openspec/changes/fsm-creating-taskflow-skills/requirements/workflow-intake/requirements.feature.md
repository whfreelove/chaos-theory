# Feature: Workflow intake (workflow-intake)

## ADDED Requirements

`@workflow-intake:1`
### Rule: Intake produces a normalized step list

`@workflow-intake:1.1`
#### Scenario: Single source produces step list

- Given the author provides a single intake source
- When intake is complete
- Then the skill presents a normalized step list for author confirmation

`@workflow-intake:1.2`
#### Scenario: Multi-source material merged at normalization

- Given the author uses both an existing skill and written step descriptions as intake sources
- When normalization runs
- Then the skill merges material from both sources and presents a unified step list for author confirmation

---

`@workflow-intake:2`
### Rule: Existing skill intake transforms an existing skill into a step list

#### Background

- Given the author provides an existing skill as the intake source

`@workflow-intake:2.1`
#### Scenario: Sequential steps extracted from existing skill

- When the skill analyzes the existing skill
- Then the extracted steps reflect the sequential execution order from the skill

`@workflow-intake:2.2`
#### Scenario: Implicit parallelism identified in existing skill

- When the skill analyzes the existing skill and detects steps that could execute concurrently
- Then the extracted steps reflect the parallel grouping with author confirmation requested

`@workflow-intake:2.3`
#### Scenario: Author confirms extracted steps without changes

- When the extracted step list is presented to the author
- And the author confirms the list as-is
- Then the step list is finalized and intake proceeds to the next phase

`@workflow-intake:2.4`
#### Scenario: Author modifies extracted steps

- When the extracted step list is presented to the author
- And the author requests changes
- Then the skill incorporates the changes and presents the revised list for re-confirmation

---

`@workflow-intake:3`
### Rule: Written step description intake accepts or refines author-provided steps

`@workflow-intake:3.1`
#### Scenario: Well-structured step descriptions accepted

- Given the author provides a written list of clearly described steps
- When the skill evaluates the descriptions
- Then the steps are accepted and presented as a normalized step list for author confirmation

`@workflow-intake:3.2`
#### Scenario: Vague step description prompts clarifying questions

- Given the author provides a written step whose intent is unclear
- When the skill evaluates the description
- Then the skill asks targeted clarifying questions before accepting the step

`@workflow-intake:3.3`
#### Scenario: Overly large step prompts splitting guidance

- Given the author provides a written step that spans multiple distinct actions
- When the skill evaluates the description
- Then the skill suggests splitting the step and prompts the author to confirm the decomposition

---

`@workflow-intake:4`
### Rule: Brainstorming fills gaps in prior intake material

`@workflow-intake:4.1`
#### Scenario: Brainstorming adds missing phases after input-based intake

- Given prior intake sources produced a step list with identifiable gaps
- When brainstorming runs
- Then the skill identifies the missing phases and proposes additional steps to fill them

`@workflow-intake:4.2`
#### Scenario: Brainstorming generates a full step list when prior sources yield nothing

- Given prior intake sources produced no usable material
- When brainstorming runs
- Then the skill generates a complete step list from scratch and presents it for author confirmation

`@workflow-intake:4.3`
#### Scenario: Author modifies brainstorm output

- Given brainstorming produced a proposed step list
- When the author requests changes
- Then the skill incorporates the changes and presents the revised list for re-confirmation

`@workflow-intake:4.4`
#### Scenario: Brainstorming yields no output — workflow terminates gracefully

- Given prior intake sources produced no usable material
- When brainstorming also produces nothing
- Then the skill informs the author that no workflow material is available and terminates the session

---

`@workflow-intake:5`
### Rule: Both intake sources can be used together

`@workflow-intake:5.1`
#### Scenario: Multi-source intake produces a unified step list incorporating both sources

- Given the author provides both an existing skill and written step descriptions as intake sources
- When the skill processes the combined intake
- Then the skill produces a unified normalized step list that incorporates content from both the existing-skill analysis and the written step descriptions

## MODIFIED Requirements

## REMOVED Requirements

## RENAMED Requirements
