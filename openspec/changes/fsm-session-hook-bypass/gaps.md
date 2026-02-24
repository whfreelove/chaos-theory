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




### GAP-62: REQ-env-var-bypass rule places MUST obligation on internal hook component
- **Source**: Resolution Normative Detection-detection
- **Severity**: medium
- **Description**: Resolution of GAP-18 introduced 'the hook MUST allow' in the REQ-env-var-bypass rule text in spec.yaml, placing the normative obligation on the internal hook script rather than expressing an observable behavioral constraint. GAP-61 subsequently updated the tail of the same rule sentence ('without emitting a deny' → 'without denying the request') but did not address the subject. The established cleanup pattern across GAP-1, GAP-5, GAP-17, GAP-26, GAP-30, GAP-42, and GAP-61 has been to remove 'hook' from all behavioral sections. A rule-level normative statement should not name an internal implementation artifact as the acting subject; it should describe the required observable outcome, e.g. 'Read, Glob, and Grep access to skill files MUST be allowed without denying the request when FSM_BYPASS is set to a non-empty value.'
- **Triage**: delegate
- **Decision**: Rewrite REQ-env-var-bypass rule from 'the hook MUST allow Read, Glob, and Grep access to skill files without denying the request' to 'Read, Glob, and Grep access to skill files MUST be allowed without denying the request.' Removes the internal implementation artifact as the normative subject, expressing the requirement as an observable behavioral outcome. Completes the cleanup started by GAP-61, which updated the tail of the same sentence but not the subject. Consistent with the established pattern across GAP-1, GAP-5, GAP-17, GAP-26, GAP-30, GAP-42, and GAP-61.
- **Primary-file**: openspec/changes/fsm-session-hook-bypass/spec.yaml

## Low
