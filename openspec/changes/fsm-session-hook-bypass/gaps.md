# Gaps

<!-- GAP TEMPLATE:
### GAP-XX: Title
- **Source**: <kebab-case with type suffix, e.g., functional-critic, implicit-detection>
- **Severity**: high|medium|low
- **Description**: ...
- **Triage**: check-in|delegate|defer-release|defer-resolution (added by resolve workflow)
- **Decision**: ... (added by resolve workflow)

CRITIQUE adds: ID, Source, Severity, Description
RESOLVE adds: Triage, Decision

New gaps from critique should NOT have Triage or Decision fields.

See tokamak:managing-spec-gaps for triage and status semantics.
-->

## Low

### GAP-24: Functional `why` uses "task hydration" implementation term
- **Source**: resolution-leakage-detection
- **Severity**: low
- **Triage**: defer-release
- **Decision**: Acknowledge as acceptable — "task hydration" is established project terminology used in the project's own functional.md. Borderline implementation flavor but consistent with existing project vocabulary.
- **Description**: Resolution of GAP-5 introduced "task hydration" in functional `why`. This is an implementation mechanism name (internal FSM jargon for how the plugin populates task lists). The rewrite removed script names but substituted an internal term.
