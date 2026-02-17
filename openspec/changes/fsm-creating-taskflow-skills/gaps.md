# Gaps

<!-- GAP TEMPLATE - Fields by workflow stage:
CRITIQUE adds: ID, Severity, Source, Description
RESOLVE adds: Category, Decision

New gaps from critique should NOT have Category or Decision fields.

See tokamak:managing-spec-gaps for gap creation quality and category semantics.
-->

## GAP-137
- **Severity**: Medium
- **Source**: implicit-detection
- **Description**: The Confirmation Gate Mechanism (technical.md) specifies that confirmation gates use "AskUserQuestion (or equivalent user prompt)" but does not define what qualifies as an "equivalent" prompt mechanism. The same phrasing appears in infra.md's verification-by-design section. An implementor writing task descriptions that instruct the agent to pause for author approval would not know whether alternative mechanisms (e.g., a plain text question without AskUserQuestion, TodoWrite with a question, or other prompting patterns) satisfy the "equivalent" qualifier. This could lead to inconsistent confirmation gate implementations across tasks, where some use AskUserQuestion and others use an undefined alternative.

## GAP-138
- **Severity**: Low
- **Source**: implicit-detection
- **Description**: The Progressive Construction Protocol's Recovery clause (technical.md, State Management section) states that if the agent loses the in-progress artifact, it should "reconstruct from the most recent complete phase output visible in conversation history." The procedure assumes that at least one complete phase output remains visible after context compaction. No guidance exists for the scenario where aggressive compaction removes all intermediate artifacts from the visible conversation history, leaving no recovery baseline. While this may be an unlikely edge case, the recovery procedure provides no fallback or detection mechanism for when its own precondition (a visible phase output) fails to hold.

## GAP-139
- **Severity**: Medium
- **Source**: implicit-detection
- **Description**: The Known Risks section (functional.md) documents that large workflows may have poor UX during dependency mapping because "no upper workflow size limit is defined, and no scalability criteria (pagination, search, grouping) exist for presenting tasks during dependency mapping." While this is acknowledged as a risk, neither functional.md nor technical.md provides any actionable guidance for the implementor: no recommended maximum task count, no warning threshold at which the skill should advise the author about potential UX issues, and no fallback presentation strategy. An implementor has no basis for deciding when or how to address UX degradation, leaving the behavior entirely undefined for workflows above some unspecified size.

## GAP-140
- **Severity**: Low
- **Source**: implicit-detection
- **Description**: During authoring, CMP-dependency-map assigns task IDs sequentially (technical.md: "Newly added tasks receive the next sequential ID (max existing ID + 1); existing task IDs remain stable during authoring"). However, CMP-fsm-json renumbers all task IDs to topological order ("Renumber all task IDs to topological order (sequential starting at 1) and update all blockedBy references to match the new IDs"). The documentation does not specify whether the author is informed that the IDs they interacted with during dependency mapping and description writing will change in the final output. If the author references task IDs from earlier phases (e.g., in notes, external documentation, or verbal communication), the renumbering could cause confusion. No guidance exists on whether the skill should present the ID mapping to the author or acknowledge the renumbering during finalization.
