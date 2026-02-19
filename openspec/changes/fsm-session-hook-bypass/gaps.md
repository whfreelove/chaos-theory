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

### GAP-1: what-changes describes mechanism not behavior
- **Source**: functional-critic
- **Severity**: high
- **Description**: CHG-env-bypass says "block-skill-internals.sh checks an environment variable and skips denial when set" — this describes the internal mechanism (script checks env var, skips denial). A functional framing would describe what the developer experiences: e.g., "Developer can set a session-scoped flag to allow skill file reads without disabling the plugin." Similarly CHG-denial-message references "Denial systemMessage and reason" — hook API fields, not user-facing concepts.

### GAP-2: No testability documentation for env-var bypass mechanism
- **Source**: technical-critic
- **Severity**: high
- **Description**: DEC-env-var-over-file-flag describes why an env var was chosen over alternatives, but neither the decision nor any other section documents how the bypass behavior can be validated. There is no description of how to simulate the hook invocation with and without FSM_BYPASS set, and no mention of what observable outcome constitutes a passing test (e.g., hook exits 0 with no output vs. emits deny JSON). For a PreToolUse hook whose correctness depends on environment state, this omission leaves implementers without a verification path.

### GAP-3: Tasks implement manual shell commands, not automated tests
- **Source**: test-tasks-critic
- **Severity**: high
- **Description**: TSK-verify-bypass describes manual shell commands ("export FSM_BYPASS=1, confirm skill file reads are allowed") rather than structured, repeatable test scripts. The infra testing strategy maps all three scenarios to `manual` coverage, which is the root cause — but the tasks inherit this inadequacy rather than compensating with automation. No task creates a test file that encodes the scenarios as executable, verifiable assertions.

### GAP-4: Integration section is entirely empty
- **Source**: integration-critic
- **Severity**: high
- **Description**: `integration: {}` contains no scenarios. The integration critic flagged this as missing cross-capability coverage. However, the integration-coverage critic (independently) found no issues, arguing that the two capabilities' interaction is already fully covered by single-capability requirement scenarios (SCN-bypass-not-set spans both capabilities). This is a conflicting assessment — one critic demands integration scenarios, the other finds existing coverage sufficient.

## Medium

### GAP-5: `why` references script name instead of human burden
- **Source**: functional-critic
- **Severity**: medium
- **Description**: The `why` names the internal artifact `block-skill-internals.sh` and frames the problem around its behavior rather than the developer's experience. A user-burden framing would focus on the disproportionate cost: developers who need to read a skill file must disable the entire FSM plugin, losing task hydration and all other functionality.

### GAP-6: Objectives lack context — no connection to problem being solved
- **Source**: design-critic
- **Severity**: medium
- **Description**: OBJ-zero-state and OBJ-minimal-diff are constraints on the solution, not statements of what success looks like. Neither objective names the actual goal (enabling authorized bypass of the skill internals gate). A reader cannot tell from the objectives alone what the feature does or why it exists. The implementation constraints belong in context or decisions, not as objectives.

### GAP-7: Decision missing Y-statement format
- **Source**: design-critic
- **Severity**: medium
- **Description**: DEC-env-var-over-file-flag names a chosen approach and brief rationale but does not follow the Y-statement format required by the schema. It omits: the quality concern being faced, the explicit neglected alternatives, and the accepted trade-off. A reader cannot tell what a temp file or config flag approach would have looked like, or what is accepted by choosing env vars.

### GAP-8: Vague outcome "proceeds normally" in SCN-bypass-active
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: In SCN-bypass-active, the then-step "The Read proceeds normally" is not a testable observable outcome — "normally" has no defined meaning and cannot be verified. The first then-item (exit 0 with no JSON output) is the actual observable signal; this second bullet adds nothing concrete and introduces ambiguity.

### GAP-9: SCN-denial-shows-bypass-instructions tests two independent behaviors
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: SCN-denial-shows-bypass-instructions has two then-assertions that test independent behaviors: (1) the new bypass instruction is present, and (2) the old plugin-disable advice is absent. A test failure on either would have a different root cause. Per one-scenario-one-behavior, these belong in separate scenarios.

### GAP-10: Missing scenarios for Glob/Grep bypass path
- **Source**: requirements-coverage-critic, validation-critic, verification-critic
- **Severity**: medium
- **Description**: REQ-env-var-bypass's rule states the bypass must allow "Read, Glob, and Grep access," but SCN-bypass-active only covers Read. There is no requirement scenario verifying that Glob and Grep are also allowed through when FSM_BYPASS is set. The existing script extracts paths from `.tool_input.pattern` (used by Glob/Grep), so these are distinct code paths worth covering.

### GAP-11: Missing scenario for hooks.json file pattern
- **Source**: requirements-coverage-critic
- **Severity**: medium
- **Description**: The existing script blocks three file patterns: SKILL.md, fsm.json, and hooks.json. All requirement scenarios only mention SKILL.md and fsm.json. There is no scenario that verifies behavior for hooks.json — either bypass or denial. If a regression breaks hooks.json handling specifically, no scenario would catch it.

### GAP-12: Bypass indistinguishable from non-triggered hook
- **Source**: verification-critic
- **Severity**: medium
- **Description**: SCN-bypass-active asserts "The hook exits 0 with no JSON output" but makes no distinction between the hook exiting 0 because bypass is active vs. the hook exiting 0 because the path didn't match a blocked pattern at all. Without constraining the file path to one that would be blocked under normal conditions, the scenario cannot distinguish bypass from a non-triggered hook.

### GAP-13: No scenario covers empty-string FSM_BYPASS case
- **Source**: verification-critic
- **Severity**: medium
- **Description**: REQ-env-var-bypass specifies bypass triggers when FSM_BYPASS is "a non-empty value." SCN-bypass-not-set covers the unset case, SCN-bypass-active covers the non-empty set case. The empty-string case (`FSM_BYPASS=""`) is explicitly part of the rule ("not set or is empty") but there is no scenario verifying that an empty-string export does not bypass the hook.

### GAP-14: No test execution procedure for manual coverage claims
- **Source**: design-for-test-critic
- **Severity**: medium
- **Description**: All three scenarios are mapped to `manual` coverage, but the infra spec provides no procedure for how manual testing is carried out. Without a documented invocation pattern (e.g., how to call block-skill-internals.sh directly with a fabricated JSON payload, how to capture and inspect stdout), there is no reproducible way to verify these assertions pass.

### GAP-15: No interface contract for deny JSON shape
- **Source**: logic-critic, code-tasks-critic
- **Severity**: medium
- **Description**: SCN-denial-shows-bypass-instructions asserts specific content in `systemMessage`, but the technical section has `interfaces: {}` and documents no interface for the deny JSON payload. The responsibility "Emit deny JSON with actionable bypass instructions" is the only guidance. TSK-update-denial-message references specific JSON fields (systemMessage, permissionDecisionReason) that are never named in the technical design, creating a disconnect between spec and tasks.

### GAP-16: No verification task for denial message content
- **Source**: test-infra-critic, code-tasks-critic
- **Severity**: medium
- **Description**: TSK-verify-bypass checks that a deny fires when FSM_BYPASS is unset, but does not assert that the denial message text contains the bypass instruction (e.g., `FSM_BYPASS=1`). The message content change from TSK-update-denial-message is therefore unverified by any task.

## Low

### GAP-17: Capabilities reference internal component names
- **Source**: functional-critic
- **Severity**: low
- **Description**: CAP-session-bypass says "bypass block-skill-internals.sh" and CAP-actionable-denial says "bypass the hook." Capabilities should be framed as actor outcomes without naming internal components. The developer doesn't think in terms of hooks or script names — they see a denial message and want to proceed.

### GAP-18: Normative language uses lowercase "must"
- **Source**: requirements-critic
- **Severity**: low
- **Description**: Both rule statements use lowercase "must" ("the hook must allow", "must tell the user"). The normative language standard requires SHALL or MUST (uppercase) for mandatory behavior.

### GAP-19: Missing scenario for denial reason field content
- **Source**: requirements-coverage-critic, validation-critic
- **Severity**: low
- **Description**: CHG-denial-message says both systemMessage and reason are updated. REQ-updated-denial-message only asserts on systemMessage content — it has no rule or then-step verifying the `permissionDecisionReason` field is also updated. If `reason` still says "disable the plugin," the requirement passes but the behavior is incomplete.

### GAP-20: Empty component-interactions diagram slot
- **Source**: design-critic
- **Severity**: low
- **Description**: The architecture block has `component-interactions: null`. For a single-component change this may be intentional, but the null key creates ambiguity: placeholder that was forgotten, or deliberate omission? Should either be removed or carry an explicit note.

### GAP-21: Tool inconsistency across scenarios
- **Source**: verification-critic
- **Severity**: low
- **Description**: SCN-bypass-active and SCN-bypass-not-set both specify Read as the tool, while SCN-denial-shows-bypass-instructions uses Glob. Since these are separate capabilities, the scenarios should either share a common tool for parallelism, or the coverage mapping should note that both code paths must be verified.
