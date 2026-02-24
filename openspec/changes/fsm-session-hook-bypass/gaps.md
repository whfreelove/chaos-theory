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





### GAP-63: Bypass Then clauses retain hook exit-code mechanism language
- **Source**: Resolution Normative Detection-detection
- **Severity**: medium
- **Description**: Resolution of GAP-10, GAP-11, and GAP-49 introduced 'The hook exits 0 with no JSON output' in Then clauses of SCN-bypass-active-glob, SCN-bypass-active-grep, SCN-bypass-active-hooks-json, and SCN-bypass-active-fsm-json in requirements.yaml. The same text exists in the original SCN-bypass-active. GAP-61 removed 'The hook emits a deny decision' from denial Then clauses on the grounds that it names an internal mechanism rather than an observable behavioral outcome, establishing that Then clauses must describe externally observable outcomes. The bypass Then clauses follow the parallel pattern: 'hook exits 0' references the internal script exit code, and 'no JSON output' references the hook API's stdout contract — both are implementation mechanism details, not developer-observable behavior. GAP-61's cleanup was applied only to denial Then clauses and did not address the logically symmetric bypass Then clauses, leaving the same class of issue unresolved across all 5 bypass scenarios. Observable behavioral language consistent with GAP-61 would be 'The tool request is allowed' or 'Skill file access is granted.' File: openspec/changes/fsm-session-hook-bypass/.sections/requirements.yaml
- **Triage**: delegate
- **Decision**: Replace 'The hook exits 0 with no JSON output' with 'The tool request is allowed' in all 5 bypass scenario Then clauses (SCN-bypass-active, SCN-bypass-active-glob, SCN-bypass-active-grep, SCN-bypass-active-hooks-json, SCN-bypass-active-fsm-json). Creates a direct symmetric pair with denial Then clauses ('The tool request is denied'). Matches REQ-env-var-bypass rule language ('MUST be allowed'). Completes the cleanup started by GAP-61, which addressed denial Then clauses but not the logically symmetric bypass Then clauses. Infra, architecture, and task sections retain implementation-level language (exit codes, stdout) appropriate to their verification and design purposes.
- **Primary-file**: openspec/changes/fsm-session-hook-bypass/spec.yaml

## Low
