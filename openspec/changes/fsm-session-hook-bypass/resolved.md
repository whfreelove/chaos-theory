# Resolved Gaps

<!-- GAP TEMPLATE:
### GAP-XX: Title
- **Source**: <kebab-case with type suffix, e.g., functional-critic, implicit-detection>
- **Severity**: high|medium|low
- **Description**: ... (original concern, immutable)
- **Triage**: check-in|delegate|defer-release|defer-resolution (preserved from gaps.md)
- **Decision**: ... (immutable point-in-time decision)
- **Status**: resolved|superseded|deprecated (set on move to resolved.md)
- **Superseded by**: GAP-XX (only when Status is superseded)
- **Outcome**: ... (optional — records what actually changed in artifacts after Decision was applied)
- **Rationale**: ... (only when Status is deprecated — must cite specific evidence: artifact change, code evidence, or context shift)
- **Current approach**: ... (only when Status is superseded — points to up-to-date information)

See tokamak:managing-spec-gaps for triage and status semantics.
-->

## High

### GAP-1: what-changes describes mechanism not behavior
- **Source**: functional-critic
- **Severity**: high
- **Triage**: delegate
- **Decision**: Rewrite CHG-env-bypass and CHG-denial-message descriptions as user-observable behavior changes. Remove script names and hook API field references. Co-thematic with GAP-5 and GAP-17.
- **Description**: CHG-env-bypass says "block-skill-internals.sh checks an environment variable and skips denial when set" — this describes the internal mechanism (script checks env var, skips denial). A functional framing would describe what the developer experiences: e.g., "Developer can set a session-scoped flag to allow skill file reads without disabling the plugin." Similarly CHG-denial-message references "Denial systemMessage and reason" — hook API fields, not user-facing concepts.
- **Status**: resolved
- **Outcome**: Rewrote CHG-env-bypass description to "Setting a shell environment variable allows skill file reads for the current session without disabling the plugin." Rewrote CHG-denial-message description to "When a skill file read is denied, the message tells the developer how to set the bypass environment variable instead of suggesting plugin disablement."

### GAP-2: No testability documentation for env-var bypass mechanism
- **Source**: technical-critic
- **Severity**: high
- **Triage**: delegate
- **Decision**: Add manual test procedure to infra testing-strategy documenting how to invoke block-skill-internals.sh with fabricated JSON payloads and inspect stdout/stderr for expected behavior. Co-resolves GAP-14.
- **Description**: DEC-env-var-over-file-flag describes why an env var was chosen over alternatives, but neither the decision nor any other section documents how the bypass behavior can be validated. There is no description of how to simulate the hook invocation with and without FSM_BYPASS set, and no mention of what observable outcome constitutes a passing test (e.g., hook exits 0 with no output vs. emits deny JSON). For a PreToolUse hook whose correctness depends on environment state, this omission leaves implementers without a verification path.
- **Status**: resolved
- **Outcome**: Added manual-test-procedure field to infra testing-strategy documenting hook invocation with fabricated JSON payloads via stdin, FSM_BYPASS env var setup for bypass/denial scenarios, and stdout inspection criteria for both allow (empty stdout, exit 0) and deny (JSON with decision, systemMessage, permissionDecisionReason fields) outcomes. Co-resolves GAP-14.

### GAP-3: Tasks implement manual shell commands, not automated tests
- **Source**: test-tasks-critic
- **Severity**: high
- **Triage**: delegate
- **Decision**: Accept manual testing as proportionate to change scope (single shell script edit). Enhance TSK-verify-bypass description to include denial message content verification, referencing the manual test procedure from GAP-2 resolution. Co-resolves GAP-16.
- **Description**: TSK-verify-bypass describes manual shell commands ("export FSM_BYPASS=1, confirm skill file reads are allowed") rather than structured, repeatable test scripts. The infra testing strategy maps all three scenarios to `manual` coverage, which is the root cause — but the tasks inherit this inadequacy rather than compensating with automation. No task creates a test file that encodes the scenarios as executable, verifiable assertions.
- **Status**: resolved
- **Outcome**: Expanded TSK-verify-bypass description to reference the manual test procedure from infra testing-strategy and include verification that systemMessage contains "export FSM_BYPASS=1" and does not contain "Disable finite-skill-machine". Co-resolves GAP-16.

### GAP-4: Integration section is entirely empty
- **Source**: integration-critic
- **Severity**: high
- **Triage**: delegate
- **Decision**: Keep `integration: {}` with a YAML comment explaining cross-capability interaction is already covered by single-capability scenarios. The integration-coverage critic's analysis confirms no emergent behavior exists — SCN-bypass-not-set already spans both capabilities.
- **Description**: `integration: {}` contains no scenarios. The integration critic flagged this as missing cross-capability coverage. However, the integration-coverage critic (independently) found no issues, arguing that the two capabilities' interaction is already fully covered by single-capability requirement scenarios (SCN-bypass-not-set spans both capabilities). This is a conflicting assessment — one critic demands integration scenarios, the other finds existing coverage sufficient.
- **Status**: resolved
- **Outcome**: Enhanced YAML comment above `integration: {}` to explain that cross-capability interaction is already covered by single-capability scenarios, SCN-bypass-not-set spans both capabilities, and the two capabilities modify the same script in non-conflicting ways with no emergent behavior.

## Medium

### GAP-5: `why` references script name instead of human burden
- **Source**: functional-critic
- **Severity**: medium
- **Triage**: delegate
- **Decision**: Rewrite `why` to focus on developer experience without naming internal scripts. Frame as the disproportionate cost of disabling the entire plugin just to read a skill file. Co-thematic with GAP-1 and GAP-17.
- **Description**: The `why` names the internal artifact `block-skill-internals.sh` and frames the problem around its behavior rather than the developer's experience. A user-burden framing would focus on the disproportionate cost: developers who need to read a skill file must disable the entire FSM plugin, losing task hydration and all other functionality.
- **Status**: resolved
- **Outcome**: Rewrote functional `why` to focus on developer experience: "When a developer is denied access to a skill file, the only suggested workaround is to disable the entire finite-skill-machine plugin..." with no script name references. Co-thematic with GAP-1 and GAP-17.

### GAP-6: Objectives lack context — no connection to problem being solved
- **Source**: design-critic
- **Severity**: medium
- **Triage**: delegate
- **Decision**: Rename OBJ-zero-state -> OBJ-session-bypass and OBJ-minimal-diff -> OBJ-self-contained. Rewrite descriptions as measurable outcomes that connect to the feature's purpose rather than implementation constraints.
- **Description**: OBJ-zero-state and OBJ-minimal-diff are constraints on the solution, not statements of what success looks like. Neither objective names the actual goal (enabling authorized bypass of the skill internals gate). A reader cannot tell from the objectives alone what the feature does or why it exists. The implementation constraints belong in context or decisions, not as objectives.
- **Status**: resolved
- **Outcome**: Renamed OBJ-zero-state to OBJ-session-bypass ("Developer can allow skill file access for a shell session using only an environment variable") and OBJ-minimal-diff to OBJ-self-contained ("The bypass is fully implemented within the existing hook script with no new files, dependencies, or plugin configuration changes").

### GAP-7: Decision missing Y-statement format
- **Source**: design-critic
- **Severity**: medium
- **Triage**: delegate
- **Decision**: Rewrite DEC-env-var-over-file-flag as full Y-statement with context, facing, decided, to achieve, accepting clauses. Include neglected alternatives (temp file, config flag) and accepted trade-off (bypass inherited by child processes, env inspection is only discovery method).
- **Description**: DEC-env-var-over-file-flag names a chosen approach and brief rationale but does not follow the Y-statement format required by the schema. It omits: the quality concern being faced, the explicit neglected alternatives, and the accepted trade-off. A reader cannot tell what a temp file or config flag approach would have looked like, or what is accepted by choosing env vars.
- **Status**: resolved
- **Outcome**: Rewrote DEC-env-var-over-file-flag as full Y-statement: "In the context of the skill-internals access gate, facing the need for a session-scoped bypass that requires no setup or cleanup, we decided on a shell environment variable (FSM_BYPASS) and neglected a temporary file flag and a plugin config flag, to achieve zero-configuration bypass that is session-scoped by default and follows standard shell conventions, accepting that the bypass is inherited by child processes and that environment inspection is the only discovery method."

### GAP-8: Vague outcome "proceeds normally" in SCN-bypass-active
- **Source**: requirements-critic
- **Severity**: medium
- **Triage**: delegate
- **Decision**: Remove "The Read proceeds normally" from SCN-bypass-active then-block. The existing assertion (exit 0 with no JSON output) fully describes the hook's allow behavior.
- **Description**: In SCN-bypass-active, the then-step "The Read proceeds normally" is not a testable observable outcome — "normally" has no defined meaning and cannot be verified. The first then-item (exit 0 with no JSON output) is the actual observable signal; this second bullet adds nothing concrete and introduces ambiguity.
- **Status**: resolved
- **Outcome**: Removed "The Read proceeds normally" from SCN-bypass-active then-block, leaving only "The hook exits 0 with no JSON output" as the single observable assertion.

### GAP-9: SCN-denial-shows-bypass-instructions tests two independent behaviors
- **Source**: requirements-critic
- **Severity**: medium
- **Triage**: delegate
- **Decision**: Split SCN-denial-shows-bypass-instructions into two scenarios: SCN-denial-contains-bypass-instructions (systemMessage contains "export FSM_BYPASS=1") and SCN-denial-removes-plugin-advice (systemMessage does not contain "Disable finite-skill-machine").
- **Description**: SCN-denial-shows-bypass-instructions has two then-assertions that test independent behaviors: (1) the new bypass instruction is present, and (2) the old plugin-disable advice is absent. A test failure on either would have a different root cause. Per one-scenario-one-behavior, these belong in separate scenarios.
- **Status**: resolved
- **Outcome**: Split SCN-denial-shows-bypass-instructions into SCN-denial-contains-bypass-instructions (then: systemMessage contains "export FSM_BYPASS=1") and SCN-denial-removes-plugin-advice (then: systemMessage does not contain "Disable finite-skill-machine"). Updated infra coverage-mapping to reference both new scenario names.

### GAP-10: Missing scenarios for Glob/Grep bypass path
- **Source**: requirements-coverage-critic, validation-critic, verification-critic
- **Severity**: medium
- **Triage**: delegate
- **Decision**: Add SCN-bypass-active-glob and SCN-bypass-active-grep scenarios under REQ-env-var-bypass, covering Glob pattern and Grep path extraction respectively. Each scenario names a skill-internal file in its given conditions. Co-resolves GAP-12 (bypass distinguishability) and GAP-21 (tool inconsistency).
- **Description**: REQ-env-var-bypass's rule states the bypass must allow "Read, Glob, and Grep access," but SCN-bypass-active only covers Read. There is no requirement scenario verifying that Glob and Grep are also allowed through when FSM_BYPASS is set. The existing script extracts paths from `.tool_input.pattern` (used by Glob/Grep), so these are distinct code paths worth covering.
- **Status**: resolved
- **Outcome**: Added SCN-bypass-active-glob (Glob a pattern matching a skill-internal file) and SCN-bypass-active-grep (Grep with a path targeting a skill-internal file) scenarios under REQ-env-var-bypass, both asserting exit 0 with no JSON output. Added both to infra coverage-mapping. Co-resolves GAP-12 and GAP-21.

### GAP-11: Missing scenario for hooks.json file pattern
- **Source**: requirements-coverage-critic
- **Severity**: medium
- **Triage**: delegate
- **Decision**: Add SCN-bypass-active-hooks-json scenario under REQ-env-var-bypass to cover bypass behavior for the hooks.json file pattern.
- **Description**: The existing script blocks three file patterns: SKILL.md, fsm.json, and hooks.json. All requirement scenarios only mention SKILL.md and fsm.json. There is no scenario that verifies behavior for hooks.json — either bypass or denial. If a regression breaks hooks.json handling specifically, no scenario would catch it.
- **Status**: resolved
- **Outcome**: Added SCN-bypass-active-hooks-json scenario under REQ-env-var-bypass (given: FSM_BYPASS exported and non-empty, agent attempts to Read a hooks.json file; then: hook exits 0 with no JSON output). Added to infra coverage-mapping.

### GAP-12: Bypass indistinguishable from non-triggered hook
- **Source**: verification-critic
- **Severity**: medium
- **Triage**: delegate
- **Decision**: Co-resolved by GAP-10. New scenarios explicitly name skill-internal files in their given conditions, ensuring bypass behavior is distinguishable from non-triggered hook behavior.
- **Description**: SCN-bypass-active asserts "The hook exits 0 with no JSON output" but makes no distinction between the hook exiting 0 because bypass is active vs. the hook exiting 0 because the path didn't match a blocked pattern at all. Without constraining the file path to one that would be blocked under normal conditions, the scenario cannot distinguish bypass from a non-triggered hook.
- **Status**: resolved
- **Outcome**: Co-resolved by GAP-10. SCN-bypass-active-glob and SCN-bypass-active-grep scenarios explicitly name skill-internal files in their given conditions, ensuring bypass behavior is distinguishable from non-triggered hook behavior.

### GAP-13: No scenario covers empty-string FSM_BYPASS case
- **Source**: verification-critic
- **Severity**: medium
- **Triage**: delegate
- **Decision**: Add SCN-bypass-empty-string scenario under REQ-env-var-bypass. Given FSM_BYPASS is exported as empty string and agent reads a SKILL.md, the hook emits a deny with bypass instructions.
- **Description**: REQ-env-var-bypass specifies bypass triggers when FSM_BYPASS is "a non-empty value." SCN-bypass-not-set covers the unset case, SCN-bypass-active covers the non-empty set case. The empty-string case (`FSM_BYPASS=""`) is explicitly part of the rule ("not set or is empty") but there is no scenario verifying that an empty-string export does not bypass the hook.
- **Status**: resolved
- **Outcome**: Added SCN-bypass-empty-string scenario under REQ-env-var-bypass (given: FSM_BYPASS exported as empty string, agent attempts to Read a SKILL.md; then: hook emits deny decision with bypass instructions). Added to infra coverage-mapping.

### GAP-14: No test execution procedure for manual coverage claims
- **Source**: design-for-test-critic
- **Severity**: medium
- **Triage**: delegate
- **Decision**: Co-resolved by GAP-2. Manual test procedure added to infra testing-strategy documenting hook invocation with fabricated JSON payloads and stdout/stderr inspection.
- **Description**: All three scenarios are mapped to `manual` coverage, but the infra spec provides no procedure for how manual testing is carried out. Without a documented invocation pattern (e.g., how to call block-skill-internals.sh directly with a fabricated JSON payload, how to capture and inspect stdout), there is no reproducible way to verify these assertions pass.
- **Status**: resolved
- **Outcome**: Co-resolved by GAP-2. The manual-test-procedure field added to infra testing-strategy documents the full invocation procedure including env var setup, fabricated JSON payloads via stdin, and stdout inspection criteria.

### GAP-15: No interface contract for deny JSON shape
- **Source**: logic-critic, code-tasks-critic
- **Severity**: medium
- **Triage**: delegate
- **Decision**: Add INT-deny-response interface to technical interfaces section documenting deny JSON fields (decision, systemMessage, permissionDecisionReason) and their content constraints for the updated denial message.
- **Description**: SCN-denial-shows-bypass-instructions asserts specific content in `systemMessage`, but the technical section has `interfaces: {}` and documents no interface for the deny JSON payload. The responsibility "Emit deny JSON with actionable bypass instructions" is the only guidance. TSK-update-denial-message references specific JSON fields (systemMessage, permissionDecisionReason) that are never named in the technical design, creating a disconnect between spec and tasks.
- **Status**: resolved
- **Outcome**: Added INT-deny-response interface to technical interfaces section with three documented fields: decision (always "deny"), systemMessage (developer-visible text, MUST contain "export FSM_BYPASS=1", MUST NOT contain "Disable finite-skill-machine"), and permissionDecisionReason (brief denial reason referencing bypass mechanism).

### GAP-16: No verification task for denial message content
- **Source**: test-infra-critic, code-tasks-critic
- **Severity**: medium
- **Triage**: delegate
- **Decision**: Co-resolved by GAP-3. TSK-verify-bypass description expanded to include verification of denial message text containing bypass instructions and not containing stale plugin-disable advice.
- **Description**: TSK-verify-bypass checks that a deny fires when FSM_BYPASS is unset, but does not assert that the denial message text contains the bypass instruction (e.g., `FSM_BYPASS=1`). The message content change from TSK-update-denial-message is therefore unverified by any task.
- **Status**: resolved
- **Outcome**: Co-resolved by GAP-3. TSK-verify-bypass description now explicitly includes verification that systemMessage contains "export FSM_BYPASS=1" and does not contain "Disable finite-skill-machine".

## Low

### GAP-17: Capabilities reference internal component names
- **Source**: functional-critic
- **Severity**: low
- **Triage**: delegate
- **Decision**: Rewrite both capability descriptions as actor-outcome statements without naming internal components. Co-thematic with GAP-1 and GAP-5 on functional language quality.
- **Description**: CAP-session-bypass says "bypass block-skill-internals.sh" and CAP-actionable-denial says "bypass the hook." Capabilities should be framed as actor outcomes without naming internal components. The developer doesn't think in terms of hooks or script names — they see a denial message and want to proceed.
- **Status**: resolved
- **Outcome**: Rewrote CAP-session-bypass to "Developer can temporarily allow skill file access for the current shell session without disabling the plugin." Rewrote CAP-actionable-denial to "Developer sees how to allow skill file access directly in the denial message instead of being told to disable the whole plugin." Co-thematic with GAP-1 and GAP-5.

### GAP-18: Normative language uses lowercase "must"
- **Source**: requirements-critic
- **Severity**: low
- **Triage**: delegate
- **Decision**: Replace lowercase "must" with "MUST" in both requirement rule statements (REQ-env-var-bypass and REQ-updated-denial-message).
- **Description**: Both rule statements use lowercase "must" ("the hook must allow", "must tell the user"). The normative language standard requires SHALL or MUST (uppercase) for mandatory behavior.
- **Status**: resolved
- **Outcome**: Replaced "must" with "MUST" in REQ-env-var-bypass rule ("the hook MUST allow") and REQ-updated-denial-message rule ("MUST tell the user").

### GAP-19: Missing scenario for denial reason field content
- **Source**: requirements-coverage-critic, validation-critic
- **Severity**: low
- **Triage**: defer-release
- **Decision**: Record as out-of-scope: individual deny JSON field coverage beyond systemMessage is deferred. systemMessage is the primary developer-visible text and is covered by requirements. Add to functional user-impact out-of-scope.
- **Description**: CHG-denial-message says both systemMessage and reason are updated. REQ-updated-denial-message only asserts on systemMessage content — it has no rule or then-step verifying the `permissionDecisionReason` field is also updated. If `reason` still says "disable the plugin," the requirement passes but the behavior is incomplete.
- **Status**: resolved
- **Outcome**: Added to functional user-impact out-of-scope: "Individual denial message field coverage beyond the primary developer-visible text — deferred to a future iteration." (Wording updated by GAP-23 resolution to remove hook API field names.)

### GAP-20: Empty component-interactions diagram slot
- **Source**: design-critic
- **Severity**: low
- **Triage**: defer-release
- **Decision**: Record as technical decision: in the context of a single-component change with no inter-component interactions, chose to leave component-interactions null rather than removing the schema-expected key, accepting that the null value may appear ambiguous to future readers.
- **Description**: The architecture block has `component-interactions: null`. For a single-component change this may be intentional, but the null key creates ambiguity: placeholder that was forgotten, or deliberate omission? Should either be removed or carry an explicit note.
- **Status**: resolved
- **Outcome**: Added DEC-null-component-interactions decision to technical decisions section documenting the deliberate choice to leave component-interactions null for a single-component change, with a Y-statement explaining the rationale and accepted trade-off.

### GAP-21: Tool inconsistency across scenarios
- **Source**: verification-critic
- **Severity**: low
- **Triage**: defer-release
- **Decision**: Superseded by GAP-10. GAP-10's resolution adds explicit Glob and Grep scenarios, making all three tool types have dedicated coverage. The original tool inconsistency concern is rendered moot by comprehensive tool-specific scenarios.
- **Description**: SCN-bypass-active and SCN-bypass-not-set both specify Read as the tool, while SCN-denial-shows-bypass-instructions uses Glob. Since these are separate capabilities, the scenarios should either share a common tool for parallelism, or the coverage mapping should note that both code paths must be verified.
- **Status**: superseded
- **Superseded by**: GAP-10
- **Current approach**: GAP-10's resolution adds SCN-bypass-active-glob and SCN-bypass-active-grep scenarios, giving all three tool types (Read, Glob, Grep) dedicated bypass coverage. The original tool inconsistency concern is moot.

### GAP-22: Manual test procedure missing Glob/Grep payload format
- **Source**: implicit-detection
- **Severity**: medium
- **Triage**: delegate
- **Decision**: Add Glob/Grep payload examples to manual-test-procedure showing the `.tool_input.pattern` JSON key used for these tool types, alongside the existing `.tool_input.file_path` example for Read.
- **Description**: Manual test procedure documents only the Read payload format ({"tool_input": {"file_path": "..."}}) but 4 of 8 scenarios use Glob or Grep, which the script handles via a different JSON key (.tool_input.pattern). A tester following the documented procedure cannot construct correct inputs for half the scenarios.
- **Status**: resolved
- **Outcome**: Updated infra manual-test-procedure to include both payload formats: {"tool_input": {"file_path": "..."}} for Read scenarios and {"tool_input": {"pattern": "..."}} for Glob/Grep scenarios.

### GAP-23: Hook API field names leaked into functional out-of-scope
- **Source**: resolution-leakage-detection
- **Severity**: medium
- **Triage**: delegate
- **Decision**: Rewrite functional out-of-scope entry to use behavioral language ("individual denial message field coverage beyond the primary developer-visible text") instead of hook API field names (systemMessage, permissionDecisionReason).
- **Description**: Resolution of GAP-19 introduced hook API field names (systemMessage, permissionDecisionReason) and implementation framing ("deny JSON field") in functional user-impact out-of-scope. These are implementation mechanism names (hook response JSON fields), not user-observable concepts.
- **Status**: resolved
- **Outcome**: Rewrote functional out-of-scope entry from "Individual deny JSON field coverage beyond systemMessage (e.g., permissionDecisionReason content assertions)" to "Individual denial message field coverage beyond the primary developer-visible text — deferred to a future iteration."

### GAP-25: Requirement Then clauses use hook API field name "systemMessage"
- **Source**: resolution-normative-detection
- **Severity**: medium
- **Triage**: delegate
- **Decision**: Normalize SCN-denial-contains-bypass-instructions and SCN-denial-removes-plugin-advice Then clauses to behavioral language ("The denial message contains/does not contain...") consistent with other scenarios.
- **Description**: Resolution of GAP-9 introduced "systemMessage contains..." and "systemMessage does not contain..." in Then clauses, referencing the internal hook API field name. GAP-1 explicitly identified "systemMessage" as a hook API field, not a user-facing concept. Other scenarios use behavioral language ("The deny message includes instructions to set FSM_BYPASS") for equivalent assertions.
- **Status**: resolved
- **Outcome**: Changed SCN-denial-contains-bypass-instructions from "systemMessage contains" to "The denial message contains" and SCN-denial-removes-plugin-advice from "systemMessage does not contain" to "The denial message does not contain", consistent with behavioral language in other scenarios.
