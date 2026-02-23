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



### GAP-61: Then clauses use 'hook emits' implementation mechanism language
- **Source**: Resolution Normative Detection-detection
- **Severity**: medium
- **Description**: Resolution of GAP-31, GAP-38, and GAP-41 introduced 'The hook emits a deny decision' in Then clauses of SCN-bypass-not-set, SCN-bypass-empty-string, SCN-denial-grep, SCN-denial-contains-bypass-instructions, and SCN-denial-removes-plugin-advice in requirements.yaml. 'The hook emits' names the internal hook script mechanism and its JSON emission action rather than an externally observable outcome. This spec has established (GAP-1, GAP-26, GAP-30) that 'hook' is implementation terminology to be removed from behavioral sections. Observable behavioral language would be 'The tool request is denied' or 'Access to the skill file is blocked.'
- **Triage**: delegate
- **Decision**: Replace 'The hook emits a deny decision' with 'The tool request is denied' in all 5 affected Then clauses (SCN-bypass-not-set, SCN-bypass-empty-string, SCN-denial-grep, SCN-denial-contains-bypass-instructions, SCN-denial-removes-plugin-advice). Also update REQ-env-var-bypass rule text from 'without emitting a deny' to 'without denying the request' for rule-scenario consistency. Follows the established pattern from GAP-1, GAP-26, and GAP-30 of replacing internal mechanism language with observable behavioral outcomes. Parallels INT-deny-response's own language: 'tool use is blocked.'
- **Primary-file**: spec.yaml

## Low
