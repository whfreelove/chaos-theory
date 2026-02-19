# Feature: Workflow Intake (workflow-intake)

<!--
MDG format. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

TERMINOLOGY (proposal language → Gherkin keyword):
- "Capability" → "Feature" (one Feature per capability)
- "Requirement" → "Rule" (requirements are grouped as Rules)
-->

## ADDED Requirements

`@workflow-intake:1`
### Rule: The skill SHALL support intake through input-based sources and brainstorming gap-filling

The skill SHALL provide dedicated guidance for transforming workflows from two input-based sources (existing skills, written step descriptions) with brainstorming as a sequential gap-filling step that builds on whatever material the input-based sources produced. All sources SHALL converge into a normalized step list suitable for downstream processing.

`@workflow-intake:1.1`
#### Scenario Outline: Skill presents source-specific guidance for each intake type

- Given the author invokes the skill
- When the author provides material for the `<intake_source>` intake source
- Then the skill presents guidance specific to `<intake_source>` workflows
- And the guidance explains how to transform `<source_material>` into workflow steps

##### Examples
| intake_source | source_material | guidance_behavior |
|---|---|---|
| existing skill | an existing skill's structure and logic | presents extraction guidance for existing skills |
| written steps | authored step-by-step descriptions | presents evaluation criteria for written descriptions |
| brainstorming (gap-filling) | gaps identified from prior intake material, or unstructured ideas if no prior material | presents brainstorming prompts informed by what input-based intakes already contributed |

`@workflow-intake:1.2`
#### Scenario: Each intake path produces a normalized step list

- Given the author has completed the intake phase (input-based sources and brainstorming gap-filling)
- When the intake phase concludes
- Then the skill presents a numbered list of discrete workflow steps
- And each step has a short label and a description of the work it performs
- And the step list format SHALL be consistent regardless of which intake path was used

`@workflow-intake:1.3`
#### Scenario: Input-based intakes yield no material and brainstorming generates full step list

- Given neither input-based intake source (existing skill or written steps) has produced material
- And both input-based intake tasks have completed with no output
- When the brainstorming gap-filling step runs
- Then the skill guides the author through brainstorming a full step list from scratch
- And the skill presents brainstorming prompts to help the author develop ideas into workflow steps

`@workflow-intake:1.4`
#### Scenario: Input-based intakes produce material and brainstorming fills gaps

- Given one or both input-based intake sources have produced workflow material
- When the brainstorming gap-filling step runs after the input-based intakes complete
- Then the skill reviews the material from prior intakes and identifies gaps or thin areas
- And the skill brainstorms additional steps to fill the identified gaps
- And the normalization step combines all contributed material into a single step list
- And the author reviews the merged step list during the normalization confirmation gate
- And the author SHALL be able to remove duplicates, resolve conflicts, or reorder steps in the combined list

`@workflow-intake:2`
### Rule: The skill SHALL guide existing skill transformation

When the author provides an existing skill, the skill SHALL analyze its structure and extract discrete workflow steps that capture the skill's intended execution flow.

`@workflow-intake:2.1`
#### Scenario: Existing skill with sequential steps extracted

- Given the author provides an existing skill with a linear sequence of instructions
- When the skill analyzes the existing skill's structure
- Then the skill presents extracted steps in the order they appear
- And each extracted step corresponds to a distinct phase of the original skill

`@workflow-intake:2.2`
#### Scenario: Existing skill with implicit parallelism identified

- Given the author provides an existing skill containing independent operations with no data dependencies between them
- When the skill analyzes the existing skill's structure
- Then the skill presents operations that could execute in parallel as separate steps with a note about their independence

`@workflow-intake:2.3`
#### Scenario: Author confirms extracted steps without changes

- Given the skill has presented extracted steps from an existing skill
- When the skill asks the author to review the extracted steps
- And the author confirms the steps as presented
- Then the skill SHALL present the step list for normalization without modification

`@workflow-intake:2.4`
#### Scenario: Author modifies extracted steps

- Given the skill has presented extracted steps from an existing skill
- When the skill asks the author to review the extracted steps
- And the author adds, removes, reorders, or renames steps
- Then the skill incorporates the author's modifications into the step list

`@workflow-intake:2.5`
#### Scenario: Existing skill with conditional branching decomposed with author guidance

- Given the author provides an existing skill containing conditional logic (e.g., if/else paths, conditional branches)
- When the skill analyzes the existing skill's structure
- Then the skill presents the conditional paths to the author
- And the skill offers decomposition options: separate tasks with the condition stated in each task's description, or a single task that handles both branches internally
- And the author chooses the decomposition strategy
- And the skill incorporates the chosen decomposition into the step list

`@workflow-intake:3`
### Rule: The skill SHALL guide written step description intake

When the author provides written step descriptions, the skill SHALL normalize them into a consistent format, prompting for clarification or restructuring when the descriptions are vague or overly broad.

`@workflow-intake:3.1`
#### Scenario: Well-structured descriptions accepted with minimal changes

- Given the author provides step descriptions that are specific, actionable, and appropriately scoped
- When the skill evaluates the descriptions
- Then the skill SHALL advance to the normalization phase with the contributed material, applying at most minor formatting adjustments
- And the skill SHALL present the normalized step list for confirmation

`@workflow-intake:3.2`
#### Scenario: Descriptions that do not specify what work is performed prompt clarifying questions

- Given the author provides a step description that does not specify what work is performed
- When the skill evaluates the description
- Then the skill asks the author targeted questions to clarify what work the step performs
- And the skill does not proceed until the description specifies the work to be performed

`@workflow-intake:3.3`
#### Scenario: Overly large steps prompt splitting guidance

- Given the author provides a step description that encompasses multiple distinct operations
- When the skill evaluates the description
- Then the skill explains why the step should be split
- And the skill suggests specific boundaries for dividing the step into smaller units

`@workflow-intake:4`
### Rule: The skill SHALL guide brainstorming as a gap-filling step

After the input-based intakes (existing skill, written steps) complete, the brainstorming step SHALL review prior intake material and fill gaps. When no prior material exists, the brainstorming step SHALL help organize unstructured thoughts into an ordered sequence of discrete workflow steps, consolidating overlapping ideas and establishing logical order.

`@workflow-intake:4.1`
#### Scenario: Unordered ideas organized into logical sequence

- Given the input-based intakes have completed
- And the author provides a set of ideas without any particular ordering
- When the skill processes the brainstormed ideas
- Then the skill arranges the ideas into a logical execution sequence
- And the skill explains the reasoning behind the proposed order

`@workflow-intake:4.2`
#### Scenario: Overlapping ideas consolidated into distinct steps

- Given the input-based intakes have completed
- And the author provides multiple ideas that describe the same or substantially similar work
- When the skill processes the brainstormed ideas
- Then the skill identifies the overlap and proposes a single consolidated step
- And the skill explains which ideas were merged and why

`@workflow-intake:4.3`
#### Scenario: Author confirms brainstorming output without changes

- Given the skill has organized brainstormed additions (or a full brainstormed list) into a proposed step list
- When the skill presents the proposed step list to the author
- And the author confirms the list as presented
- Then the skill accepts the step list and advances to normalization

`@workflow-intake:4.4`
#### Scenario: Author requests changes to brainstorming output

- Given the skill has organized brainstormed additions (or a full brainstormed list) into a proposed step list
- When the skill presents the proposed step list to the author
- And the author requests changes
- Then the skill incorporates the author's changes
- And the skill does not advance to normalization until the author approves the revised list

`@workflow-intake:4.5`
#### Scenario: Brainstorming yields no output and workflow terminates gracefully

- Given the input-based intakes have completed with no material
- And the author declines to provide ideas or the brainstorming yields no usable workflow steps
- When the skill determines brainstorming cannot produce a step list
- Then the skill acknowledges the author is not ready to define a workflow
- And the skill suggests the author return when they have ideas to work with
- And the workflow terminates cleanly without error

## MODIFIED Requirements

None.

## REMOVED Requirements

None.

## RENAMED Requirements

None.
