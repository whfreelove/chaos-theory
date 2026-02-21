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

## Medium

### GAP-47: SCN-bypass-not-set Given clause is a compound precondition that includes the empty-string case
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: The Given clause of the denial-when-unset scenario in the env-var-bypass requirement uses a compound precondition covering both the unset case and the empty-string case. The empty-string case was subsequently extracted into its own dedicated scenario. The compound Given was never narrowed after that extraction, leaving the two scenarios with overlapping preconditions rather than distinct ones.

### GAP-48: REQ-updated-denial-message lacks a normative negative constraint
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: The rule body for the updated denial message requirement contains only a positive behavioral constraint. The scenario that asserts the denial message does not contain plugin-disablement advice has no normative anchor in the rule. A MUST NOT clause is absent, leaving the negative behavioral claim unsupported by a rule-level contract.

### GAP-49: No Read bypass scenario for the fsm.json file pattern
- **Source**: validation-critic
- **Severity**: medium
- **Description**: Bypass coverage for the env-var-bypass requirement includes scenarios for SKILL.md reads and hooks.json reads, and bypass scenarios for Glob and Grep tool types. No scenario covers a Read tool invocation targeting an fsm.json path. The fsm.json file pattern is one of the blocked patterns in the PreToolUse guard, and its bypass behavior under the env-var-bypass capability has no dedicated scenario.

### GAP-50: Manual test procedure omits repository path for the hook script
- **Source**: design-for-test-critic
- **Severity**: medium
- **Description**: The manual test procedure in the infra testing-strategy instructs testers to invoke the PreToolUse guard script but does not specify its location in the repository. A tester following the procedure cannot locate the script without separately searching the repository.

### GAP-52: Denial scenario assertions do not verify the `decision` field value
- **Source**: code-tasks-critic
- **Severity**: medium
- **Description**: The verification task preamble checks that the denial response JSON contains the `decision`, `systemMessage`, and `permissionDecisionReason` fields, confirming field presence. The interface contract in the technical section defines the `decision` field value as always "deny". No assertion in the verification task or in any requirement scenario checks that the field value conforms to this contract.

### GAP-53: Verification preamble scope does not clearly cover denial message content scenarios
- **Source**: test-infra-critic
- **Severity**: medium
- **Description**: The verification task preamble states it applies to denial scenarios, but the task's scenario list contains a distinct category of denial message content scenarios that are labeled separately. It is ambiguous whether the structural verification requirements in the preamble are understood to extend to those separately-labeled scenarios. A similar concern arises from the infra perspective: the testing-strategy preamble's scope boundary does not explicitly include the denial message content scenario category. This gap is related to GAP-44, which addressed underspecified assertions in denial scenarios; the present concern is specifically about preamble scope clarity across scenario categories.

## Low

### GAP-45: DEC-null-component-interactions cites an external mitigant without a cross-reference
- **Source**: design-critic
- **Severity**: low
- **Description**: The decision documenting the deliberate choice to leave component-interactions null accepts the ambiguity by treating a comment in the integration section as the mitigant, but provides no pointer to where that comment lives. A reader must separately locate the integration section to confirm the mitigant exists.

### GAP-46: Technical context frames a spec artifact introduced by this change as pre-existing evidence
- **Source**: design-critic
- **Severity**: low
- **Description**: The final sentence of the technical context section presents the infra manual test procedure as existing baseline context. The manual test procedure was introduced as part of this same spec change. Context should describe what exists independent of this change, not artifacts this change introduces.

### GAP-51: No tooling specified for JSON structural verification in the testing strategy
- **Source**: design-for-test-critic
- **Severity**: low
- **Description**: The testing strategy requires structural JSON field verification in denial scenarios but names no tool for performing that verification. A tester following the procedure has no guidance on how to inspect JSON field presence from stdout.

