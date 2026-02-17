# Feature: Skill File Generation (skill-file-generation)

<!--
MDG format. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

TERMINOLOGY (proposal language -> Gherkin keyword):
- "Capability" → "Feature" (one Feature per capability)
- "Requirement" → "Rule" (requirements are grouped as Rules)
-->

## ADDED Requirements

`@skill-file-generation:1`
### Rule: The skill SHALL generate a SKILL.md file

The skill SHALL produce a SKILL.md with frontmatter containing name and description fields and body content that describes the workflow in author-facing language without exposing internal task file structure.

`@skill-file-generation:1.1`
#### Scenario: Generated SKILL.md contains valid frontmatter with name and description

- Given the author has completed the workflow intake and task definition steps
- When the skill generates the SKILL.md file
- Then the file begins with YAML frontmatter delimited by `---`
- And the frontmatter contains a `name` field with the skill's display name
- And the frontmatter contains a `description` field summarizing the skill's purpose

`@skill-file-generation:1.2`
#### Scenario: Generated SKILL.md describes workflow steps in author-facing language

- Given the author has defined a workflow with multiple steps
- When the skill generates the SKILL.md file
- Then the body content describes each workflow step in terms the end user of the skill understands
- And the language references tasks by their purpose, not by file names or internal identifiers

`@skill-file-generation:1.3`
#### Scenario: Generated SKILL.md placed in correct skill directory

- Given the author has specified a plugin name and skill name
- When the skill generates the SKILL.md file
- Then the skill guides the author to place SKILL.md at `plugins/<plugin>/skills/<skill>/SKILL.md`

`@skill-file-generation:2`
### Rule: The skill SHALL self-validate SKILL.md before finalizing

CMP-skill-md self-validates the generated SKILL.md (frontmatter correctness) and does not finalize until self-validation passes.

`@skill-file-generation:2.1`
#### Scenario: SKILL.md self-validation failure triggers correction and re-validation

- Given the skill has generated SKILL.md content
- And CMP-skill-md's self-validation detects a missing frontmatter field
- When the skill reports the self-validation failure to the author
- Then the author corrects the identified issue
- And the skill re-validates the corrected SKILL.md before completing
- And the skill does not finalize SKILL.md until self-validation passes

`@skill-file-generation:3`
### Rule: The skill SHALL generate a task definition file

The skill SHALL produce a task definition file that encodes the workflow steps with their dependencies, descriptions, and metadata so tasks are created in the correct execution order.

`@skill-file-generation:3.1`
#### Scenario: Generated task definition contains all workflow steps

- Given the author has defined a workflow with five steps
- When the skill generates the task definition file
- Then the task definition contains exactly five task entries
- And each task entry corresponds to one workflow step

`@skill-file-generation:3.2`
#### Scenario: Generated task definition encodes dependencies correctly

- Given the author has defined step B as dependent on step A
- And step C as dependent on both step A and step B
- When the skill generates the task definition file
- Then step B's entry lists step A's ID in its dependency field
- And step C's entry lists both step A's and step B's IDs in its dependency field

`@skill-file-generation:3.3`
#### Scenario: Each task entry has required fields

- Given the author has completed the workflow definition
- When the skill generates the task definition file
- Then each task entry contains an `id` field with a unique numeric identifier
- And each task entry contains a `subject` field with a short task title
- And each task entry contains a `description` field with self-contained instructions
- And each task entry contains an `activeForm` field with present-continuous form for status display (auto-generated default; author overrides are accepted as-is per self-contained-descriptions:4.2)
- And each task entry contains a `blockedBy` field encoding dependency references
- And each task entry contains `metadata` with the skill name for scoped identification

`@skill-file-generation:3.4`
#### Scenario: Display-friendly names auto-normalized to directory-safe format

- Given the author has specified a plugin name or skill name containing spaces, uppercase letters, or special characters (e.g., "My Cool Skill")
- When the skill processes the name for directory placement
- Then the skill converts the name to a directory-safe format (lowercase, hyphens replacing spaces, no special characters) (e.g., "my-cool-skill")
- And the skill presents the normalized name to the author for confirmation
- And the author SHALL be able to confirm or override the normalized name

`@skill-file-generation:4`
### Rule: The skill SHALL place generated files in the correct directory structure

The skill SHALL guide the author on where to place the SKILL.md and task definition file within the plugin's skill directory so the files conform to the expected plugin convention.

`@skill-file-generation:4.1`
#### Scenario: Skill files placed under plugin skills directory

- Given the author has specified plugin name "my-plugin" and skill name "my-skill"
- When the skill presents the generated files to the author
- Then the skill instructs the author to place files under `plugins/my-plugin/skills/my-skill/`

`@skill-file-generation:4.2`
#### Scenario: Directory structure matches plugin convention

- Given the skill has generated both a SKILL.md and a task definition file
- When the skill presents the directory layout to the author
- Then the layout shows SKILL.md at the skill directory root
- And the layout shows the task definition file alongside SKILL.md in the same directory

`@skill-file-generation:4.3`
#### Scenario: Non-existent target directory created during file placement

- Given the author has specified a plugin name and skill name
- And the target directory `plugins/<plugin>/skills/<skill>/` does not yet exist
- When the skill places the generated files
- Then the skill creates the target directory structure
- And the skill places the generated files in the newly created directory

`@skill-file-generation:4.4`
#### Scenario: Existing skill directory detected and author chooses resolution

- Given the author has specified a plugin name and skill name
- And the target directory `plugins/<plugin>/skills/<skill>/` already exists and contains files
- When the skill detects the existing directory
- Then the skill informs the author that the target directory already exists
- And the skill offers the author options to overwrite the existing files, choose a different skill name, or abort file placement
- And the skill does not place files until the author selects an option

## MODIFIED Requirements

None.

## REMOVED Requirements

None.

## RENAMED Requirements

None.
