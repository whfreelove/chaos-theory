# Feature: Skill file generation (skill-file-generation)

## ADDED Requirements

`@skill-file-generation:1`
### Rule: A SKILL.md file is generated with valid structure

`@skill-file-generation:1.1`
#### Scenario: SKILL.md contains valid YAML frontmatter

- Given the skill workflow is complete
- When SKILL.md is generated
- Then SKILL.md contains YAML frontmatter with at minimum a `name` and `description` field

`@skill-file-generation:1.2`
#### Scenario: SKILL.md body content uses author-facing language

- Given SKILL.md is being generated
- When the body content is written
- Then the body describes the workflow in author-facing terms without referencing internal task identifiers or fsm.json fields

---

`@skill-file-generation:2`
### Rule: SKILL.md is self-validated before finalization

`@skill-file-generation:2.1`
#### Scenario: SKILL.md validation failure triggers correction

- Given SKILL.md has been generated
- When SKILL.md validation detects a structural problem
- Then the skill identifies the issue and prompts the author to correct it before proceeding

---

`@skill-file-generation:3`
### Rule: A task definition file (fsm.json) is generated with all workflow tasks

`@skill-file-generation:3.1`
#### Scenario: Task definition file contains all workflow steps

- Given the workflow contains N tasks
- When fsm.json is generated
- Then fsm.json contains exactly N task entries

`@skill-file-generation:3.2`
#### Scenario: Task dependencies encoded correctly

- Given the workflow has tasks with blockedBy relationships
- When fsm.json is generated
- Then each task's blockedBy field references the correct predecessor task IDs

`@skill-file-generation:3.3`
#### Scenario: Each task entry contains required fields

- Given a task in the workflow has a subject, description, activeForm, and dependency information
- When fsm.json is generated
- Then the task entry contains `id`, `subject`, `description`, `activeForm`, `blockedBy`, and `metadata` fields

`@skill-file-generation:3.4`
#### Scenario: Task definition serialized as a JSON array

- Given fsm.json is generated
- When the file is written
- Then the root structure is a JSON array where each element is a task object

`@skill-file-generation:3.5`
#### Scenario: Task IDs renumbered to topological order

- Given the workflow has tasks with dependencies that impose a topological ordering
- When fsm.json is generated
- Then task IDs are assigned in topological order
- And the author is notified of the old-to-new ID mapping

---

`@skill-file-generation:4`
### Rule: Generated files are placed in the correct plugin directory

`@skill-file-generation:4.1`
#### Scenario: Generated files placed in the plugin's skills directory

- Given the author has specified a target skill name and plugin directory
- When file generation completes
- Then SKILL.md and fsm.json are written to `<plugin>/skills/<skill-name>/`

`@skill-file-generation:4.2`
#### Scenario: Existing skill directory collision prompts author to choose resolution

- Given the target skill directory already exists
- When file generation would overwrite existing files
- Then the skill presents the author with options: overwrite, choose a different name, or abort

## MODIFIED Requirements

## REMOVED Requirements

## RENAMED Requirements
