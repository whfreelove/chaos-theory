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

## High

## Medium


### GAP-60: Untitled finding
- **Source**: Defer-Release Coverage Detection-detection
- **Severity**: medium
- **Description**: GAP-19 defer-release deferral text missing from functional out-of-scope. GAP-19 and GAP-23 outcomes both reference an out-of-scope entry acknowledging that individual denial message field coverage beyond the primary developer-visible text is deferred to a future iteration, but the current functional out-of-scope contains only three items (persistent bypass configuration, plugin enable/disable, file pattern changes) with no mention of the deferral.
- **Triage**: delegate
- **Decision**: Append 'Individual denial message field coverage beyond the primary developer-visible text — deferred to a future iteration.' to functional user-impact out-of-scope in spec.yaml. This materializes the artifact change documented in GAP-19 and GAP-23 outcomes that was never applied to the spec files.
- **Primary-file**: spec.yaml

## Low
