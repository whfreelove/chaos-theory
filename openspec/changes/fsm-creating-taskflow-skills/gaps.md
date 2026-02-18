# Gaps

<!-- GAP TEMPLATE - Fields by workflow stage:
CRITIQUE adds: ID, Severity, Source, Description
RESOLVE adds: Category, Decision

New gaps from critique should NOT have Category or Decision fields.

See tokamak:managing-spec-gaps for gap creation quality and category semantics.
-->

## GAP-169
- **Severity**: Medium
- **Source**: design-critic
- **Description**: The task dependency graph mermaid diagram in technical.md does not include an edge from the SKILL.md component to the final validation component. GAP-141 resolved the name-consistency check by adding CMP-final-validation's dependency on SKILL.md content to the component text, but the authoritative diagram was not updated to reflect this fan-in dependency. The diagram and the component description are now inconsistent.

## GAP-170
- **Severity**: Medium
- **Source**: technical-critic
- **Description**: The Progressive Construction Protocol in technical.md defines no feasibility boundary for the protocol itself. The protocol maintains a JSON artifact in conversation context across all construction phases, and for larger workflows this artifact grows with every phase. No documented scale threshold identifies when the progressively maintained artifact itself creates context pressure that undermines the protocol's purpose.

## GAP-171
- **Severity**: Medium
- **Source**: implementation-critic
- **Description**: The dependency-mapping capability description in functional.md states the skill performs automatic graph updates when new tasks are added. The CMP-dependency-map component in technical.md specifies that adding new dependency relationships requires prompted author interaction. The functional claim of automatic updates conflicts with the technical requirement of author-prompted interaction for new relationships.

## GAP-172
- **Severity**: Medium
- **Source**: requirements-critic
- **Description**: Internal technical component identifiers appear in requirement scenario bodies. The skill-file-generation requirements reference a component identifier by name in a Rule body, and the workflow-intake requirements reference another component identifier in a Then clause. Requirement scenarios should describe observable author-facing behavior; exposing internal component names at the requirements layer creates coupling between the requirements and the technical design's naming choices.

## GAP-173
- **Severity**: Low
- **Source**: requirements-critic
- **Description**: The phase-completion summary scenario in workflow-validation uses "agent" as the subject in one Then clause but "skill" in all other Then clauses within the same scenario. All other requirement scenarios consistently use "the skill" as the subject of Then clauses. This inconsistency creates ambiguity about whether the two subjects refer to different actors.

## GAP-174
- **Severity**: Medium
- **Source**: requirements-coverage-critic
- **Description**: No requirement scenario specifies that the task definition output must be in JSON format. The skill-file-generation requirements list required fields but do not pin the serialization format. An implementor could produce the task definition as YAML, TOML, or any other structured format and satisfy all field-presence scenarios without producing valid JSON.

## GAP-175
- **Severity**: Medium
- **Source**: verification-critic
- **Description**: The verification environment setup procedure documented in technical.md always creates the target skill directory before verification begins. This makes it impossible to verify the directory-creation scenario (when the target directory does not exist) and the collision-detection scenario (when a pre-existing skill directory is present) in the defined environment. No documented procedure exists for establishing either precondition in a reproducible way for verification purposes.

## GAP-176
- **Severity**: High
- **Source**: logic-critic
- **Description**: CMP-final-validation defines four checks in technical.md: cycle detection, self-containment audit, structural integrity, and name consistency. The workflow-validation requirements include scenarios covering the first three checks but contain no scenario for the name-consistency check (verifying that the metadata.fsm value in fsm.json matches the SKILL.md frontmatter name field). The fourth check has no requirement coverage.

## GAP-177
- **Severity**: Low
- **Source**: code-tasks-critic
- **Description**: In tasks.yaml, the skill-directory group and the skill-md group are ordered implicitly by document position only. No explicit dependency declaration exists between these groups in the task schema, so an implementor could execute them in any order without violating any stated constraint. The schema has no ordering mechanism beyond document sequence.

## GAP-178
- **Severity**: Medium
- **Source**: code-tasks-critic
- **Description**: The behavioral-verification group in tasks.yaml depends on the validation-enhancement, skill-directory, skill-md, and fsm-json groups completing first. No explicit cross-group dependency declaration captures this ordering constraint, leaving the dependency implicit and unenforceable through the task schema.

## GAP-179
- **Severity**: Low
- **Source**: code-tasks-critic
- **Description**: The skill-md group tasks in tasks.yaml cover SKILL.md frontmatter but do not verify that the SKILL.md body addresses the collision detection and name normalization behaviors defined in the CMP-skill-md component responsibilities. The behavioral-verification group checks frontmatter structure only; body coverage of these behaviors is not verified by any task.

## GAP-180
- **Severity**: Low
- **Source**: integration-coverage-critic
- **Description**: The integration.feature.md states that CMP-final-validation fans in from CMP-fsm-json-finalize only. GAP-141 resolved the name-consistency check by adding CMP-final-validation's dependency on SKILL.md content from CMP-skill-md. The integration.feature.md cross-artifact dependency description was not updated to reflect this new fan-in relationship.

## GAP-181
- **Severity**: Low
- **Source**: functional-consistency-critic
- **Description**: The authoring-time file write path places SKILL.md and fsm.json under the runtime skill discovery directory. The FSM plugin's runtime active-work-protection guard monitors this directory for in-progress tasks. A partially written fsm.json produced during an authoring session could be detected by the guard, potentially triggering unexpected abort or protection behavior before the file is complete.

## GAP-182
- **Severity**: Low
- **Source**: design-critic
- **Description**: The data transformation table in technical.md uses "Fields added" as the column header for all component rows. The CMP-descriptions row describes replacement semantics (replacing the normalize-phase brief description with the full self-contained instruction), not addition. GAP-97 updated the cell content to say "replaces description" but the column header itself still reads "Fields added," which is semantically incorrect for the replacement case. Similar concern to resolved GAP-97, which updated cell content but not the header.

## GAP-183
- **Severity**: Medium
- **Source**: requirements-coverage-critic
- **Description**: No requirement scenario addresses evaluation of trivially small step descriptions at the intake phase. The self-contained-descriptions requirements cover overly small descriptions during the description writing phase, but a step that is too small to be meaningful could be accepted through the intake and normalization phases without any quality check. Intake-phase evaluation for minimum meaningful size is not covered. Similar concern to resolved GAP-66, which defined the "overly small" threshold at the description writing phase rather than the intake phase.

## GAP-184
- **Severity**: Medium
- **Source**: logic-critic
- **Description**: No requirement scenario covers the ID renumbering transformation that CMP-fsm-json-finalize performs at the end of the authoring workflow. The renumbering strategy (next-sequential during authoring, topological order at finalization) and the old-to-new ID mapping disclosure are documented as technical decisions, but no requirement scenario specifies the transformation itself, author notification, or post-renumber verification that all blockedBy references are consistent. Similar concern to resolved GAP-96 and GAP-140, which established the technical design and author disclosure decisions without adding requirement coverage.

## GAP-165
- **Severity**: Low
- **Source**: implicit-detection
- **Description**: CMP-dependency-map responsibilities and dependency-mapping:5.2 require a "lightweight quality check against intake-quality criteria (specificity, actionability, scope)" when a task is added during dependency mapping, but do not define what makes the check "lightweight" versus the full intake evaluation performed by CMP-intake-written. An implementor cannot determine which checks to abbreviate or omit relative to the full intake path.

## GAP-166
- **Severity**: Medium
- **Source**: implicit-detection
- **Description**: CMP-dependency-map and CMP-final-validation both specify cycle detection "via programmatic tool invocation (e.g., a Python script)" but use "e.g." both times without committing to a specific invocation method. An implementor must decide the concrete tool mechanism (inline Python via Bash tool, standalone script file, or another approach) with no guidance on which to use or where to place a script if one is created.

## GAP-167
- **Severity**: Low
- **Source**: implicit-detection
- **Description**: CMP-intake-written responsibilities and workflow-intake:3.1 specify accepting well-structured descriptions "with at most minor formatting adjustments" but do not define the boundary between minor formatting adjustments and substantive content changes. An implementor cannot distinguish permissible silent adjustments from changes that require author review.

## GAP-168
- **Severity**: Low
- **Source**: implicit-detection
- **Description**: CMP-skill-md responsibilities and skill-file-generation Rule 1 specify SKILL.md frontmatter fields precisely but define body content only as "describing workflow steps in terms the skill's end user understands" in "author-facing language." No template, section structure, or content guidelines exist for the body beyond avoiding internal identifiers. An implementor must invent the body structure without reference material.
