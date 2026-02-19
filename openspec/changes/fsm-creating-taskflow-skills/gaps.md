# Gaps

<!-- GAP TEMPLATE - Fields by workflow stage:
CRITIQUE adds: ID, Severity, Source, Description
RESOLVE adds: Category, Decision

New gaps from critique should NOT have Category or Decision fields.

See tokamak:managing-spec-gaps for gap creation quality and category semantics.
-->

### GAP-185: CMP-fsm-json-finalize assumes CMP-skill-md has created the target directory without a blocking dependency
- **Severity**: low
- **Source**: implicit-detection
- **Description**: CMP-fsm-json-finalize's responsibilities state "directory creation and collision detection are handled by CMP-skill-md" (technical.md, CMP-fsm-json-finalize component). However, no blocking task dependency exists from CMP-fsm-json-finalize on CMP-skill-md — the dependency graph shows CMP-skill-md branching off CMP-normalize independently while CMP-fsm-json-finalize is at the end of the DM->DE->FJ linear chain. CMP-fsm-json-finalize's task description (tasks.yaml entry 8) says "guide the author on file placement alongside the delivered skill's documentation file" without any fallback for directory creation if the target directory does not yet exist. While the typical execution path makes this unlikely (CMP-skill-md becomes available much earlier than CMP-fsm-json-finalize), the specification's self-containment principle requires each task to stand alone — CMP-fsm-json-finalize's description relies on CMP-skill-md having already run, which is a cross-task assumption without enforcement.
