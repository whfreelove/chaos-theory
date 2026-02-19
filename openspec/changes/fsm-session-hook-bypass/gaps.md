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

### GAP-34: TSK-verify-bypass omits code paths added by later gap resolutions
- **Source**: code-tasks-critic
- **Severity**: high
- **Description**: TSK-verify-bypass covers only the original bypass and denial scenarios present at the time of GAP-3's resolution. Scenarios added by later gap resolutions — bypass for Glob tool, Grep tool, hooks.json file pattern, and the empty-string FSM_BYPASS denial case — are absent from the task description. An implementer executing only the steps in the task would skip these distinct code paths. The task's deferral to "the manual test procedure" does not enumerate which scenarios must be executed, leaving coverage gaps undetectable.

## Medium

### GAP-27: System-overview diagram contradicts established empty-string bypass semantics
- **Source**: design-critic
- **Severity**: medium
- **Description**: The system-overview diagram models bypass as a two-state decision: FSM_BYPASS set leads to Allow, FSM_BYPASS unset leads to Deny. In shell semantics, a variable exported as an empty string counts as "set." The requirements section (per the resolution that added the empty-string denial scenario) establish that bypass requires a non-empty value. The diagram's two-state model does not reflect this and would lead an implementer to use a presence check rather than a non-empty value check. The CMP responsibility describing the bypass check also omits the non-empty constraint.

### GAP-28: DEC-env-var-over-file-flag does not establish inheritance chain feasibility
- **Source**: technical-critic
- **Severity**: medium
- **Description**: DEC-env-var-over-file-flag accepts that bypass is inherited by child processes as a known trade-off, but neither the decision nor any other section documents that the full inheritance chain — from the developer's shell through the Claude Code process to the hook subprocess — is actually preserved. If Claude Code strips or resets environment variables when invoking hooks, FSM_BYPASS would never be visible to the hook at runtime. No feasibility evidence or reference appears anywhere in the spec.

### GAP-29: REQ-updated-denial-message rule body uses hook API field name
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: The normative rule statement for REQ-updated-denial-message instructs what "the denial systemMessage MUST tell the user." GAP-25 updated the Then clauses in the scenarios under this requirement to use behavioral language, but the rule statement itself was not updated. The word "systemMessage" in the rule body is a hook API field name, not a user-facing concept — the same class of issue GAP-25 resolved in the Then clauses. The rule and its scenarios now use inconsistent language for the same concept.

### GAP-30: REQ-env-var-bypass scenario When clauses name an internal script
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: Every scenario under REQ-env-var-bypass uses an internal script name as the When step trigger. BDD When clauses should describe the external action that initiates behavior, not the name of the internal component that runs. Coupling When to a script name means any rename of that component invalidates all scenario statements. GAP-1, GAP-5, and GAP-17 removed internal component names from other spec sections but the scenario When clauses were not addressed.

### GAP-32: Manual test procedure Grep payload places file path in wrong field
- **Source**: verification-critic
- **Severity**: medium
- **Description**: The manual test procedure's Glob and Grep payload example uses `{"tool_input": {"pattern": "..."}}` for both tools. In the Claude Code Grep tool schema, `pattern` carries the search regex and `path` carries the file path to search within. Placing a file path in the `pattern` field constructs a syntactically valid but semantically incorrect payload. A tester following the procedure literally for a Grep scenario does not exercise real Grep behavior; the hook would receive a path where a regex is expected.

## Low

### GAP-24: Functional `why` uses "task hydration" implementation term
- **Source**: resolution-leakage-detection
- **Severity**: low
- **Triage**: defer-release
- **Decision**: Acknowledge as acceptable — "task hydration" is established project terminology used in the project's own functional.md. Borderline implementation flavor but consistent with existing project vocabulary.
- **Description**: Resolution of GAP-5 introduced "task hydration" in functional `why`. This is an implementation mechanism name (internal FSM jargon for how the plugin populates task lists). The rewrite removed script names but substituted an internal term.

### GAP-26: User-impact section uses "hook" terminology in two places
- **Source**: functional-critic
- **Severity**: low
- **Description**: The functional user-impact section uses the word "hook" in two places: once in an out-of-scope item referencing persistent bypass configuration changes, and once in a known-risks entry describing the access gate as a development guardrail. A developer experiencing a denial does not think in terms of hooks — they interact with a denial message. Both uses expose implementation framing where behavioral or user-experience language is appropriate.

### GAP-31: Denial scenario When clauses use deny emission as the triggering action
- **Source**: requirements-critic
- **Severity**: low
- **Description**: SCN-denial-contains-bypass-instructions and SCN-denial-removes-plugin-advice both describe the When step as the hook emitting a deny. In BDD structure, the When step is the external action that initiates the behavior under test; the deny emission is the behavioral outcome that belongs in the Then step. Using an outcome as the When conflates the action being taken with the result being asserted, making the scenario's causal structure ambiguous.

### GAP-33: Manual test procedure hooks.json scenario uses SKILL.md path example
- **Source**: design-for-test-critic
- **Severity**: low
- **Description**: The manual test procedure provides a SKILL.md file path as the example path for all Read scenarios, including the scenario added specifically to verify hooks.json blocking behavior. A tester following the procedure literally for the hooks.json scenario would supply a SKILL.md path, never exercising the hooks.json file pattern that the scenario was created to cover.
