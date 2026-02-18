# Gaps

<!-- GAP TEMPLATE - Fields by workflow stage:
CRITIQUE adds: ID, Severity, Source, Description
RESOLVE adds: Category, Decision

New gaps from critique should NOT have Category or Decision fields.

See tokamak:managing-spec-gaps for gap creation quality and category semantics.
-->

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
