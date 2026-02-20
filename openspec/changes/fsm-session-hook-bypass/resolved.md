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

### GAP-34: TSK-verify-bypass omits code paths added by later gap resolutions
- **Source**: code-tasks-critic
- **Severity**: high
- **Triage**: delegate
- **Decision**: Expand TSK-verify-bypass to explicitly enumerate all requirement scenarios, replacing the generic reference to "the manual test procedure" with a complete checklist covering bypass for Read, Glob, Grep, and hooks.json patterns, plus the empty-string FSM_BYPASS denial case.
- **Description**: TSK-verify-bypass covers only the original bypass and denial scenarios present at the time of GAP-3's resolution. Scenarios added by later gap resolutions — bypass for Glob tool, Grep tool, hooks.json file pattern, and the empty-string FSM_BYPASS denial case — are absent from the task description. An implementer executing only the steps in the task would skip these distinct code paths. The task's deferral to "the manual test procedure" does not enumerate which scenarios must be executed, leaving coverage gaps undetectable.
- **Status**: resolved
- **Outcome**: Rewrote TSK-verify-bypass description to enumerate all 8 requirement scenarios explicitly: 4 bypass scenarios (Read SKILL.md, Glob, Grep, Read hooks.json), 2 denial scenarios (FSM_BYPASS unset, FSM_BYPASS empty string), and 2 denial message content scenarios (contains bypass instructions, does not contain plugin-disable advice). Each scenario lists the expected payload and assertion.

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

### GAP-36: `permissionDecisionReason` lacks implementer-actionable content contract
- **Source**: design-critic
- **Severity**: medium
- **Description**: In `INT-deny-response`, `permissionDecisionReason` retains changelog language rather than a stable content contract. Unlike `systemMessage`, which carries explicit MUST/MUST NOT constraints, `permissionDecisionReason` provides no concrete content requirement an implementer can follow to produce a conforming value. The intended "brief denial reason referencing bypass mechanism" is not reflected as a normative constraint in the artifact.
- **Triage**: delegate
- **Decision**: Rewrite `permissionDecisionReason` field description to remove changelog language ("Updated to reference") and replace with a stable descriptive contract: "Brief denial reason referencing the bypass mechanism rather than plugin disablement." No MUST constraints added — aligns with GAP-19's established deferral of field-level normative coverage beyond systemMessage.
- **Status**: resolved
- **Outcome**: Replaced 'Brief reason for the denial shown alongside the tool use block. Updated to reference the bypass mechanism instead of plugin disablement.' with 'Brief denial reason referencing the bypass mechanism rather than plugin disablement.' in INT-deny-response fields. [diff: +2/-3 spec.yaml]

### GAP-37: `CMP-block-skill-internals` does not specify per-tool path field extraction
- **Source**: technical-critic
- **Severity**: medium
- **Description**: The `CMP-block-skill-internals` responsibility to "pattern-match tool input paths against protected file names" does not specify that path extraction requires reading different JSON fields depending on the invoking tool (`tool_input.file_path` for Read, `tool_input.pattern` for Glob, `tool_input.path` for Grep). An implementer reading only the technical component responsibility would likely implement single-field extraction, silently allowing Glob and Grep invocations to pass without matching. The infra manual-test-procedure documents correct payload shapes, but the behavioral contract for field selection belongs at the component responsibility level.
- **Triage**: delegate
- **Decision**: Expand the existing CMP responsibility from "Pattern-match tool input paths against protected file names" to include per-tool field extraction: "Extract target path from tool-specific input fields (file_path for Read, pattern for Glob, path for Grep) and pattern-match against protected file names."
- **Status**: resolved
- **Outcome**: Changed responsibility from 'Pattern-match tool input paths against protected file names' to 'Extract target path from tool-specific input fields (file_path for Read, pattern for Glob, path for Grep) and pattern-match against protected file names'. [diff: +1/-1 spec.yaml]

### GAP-38: No denial scenario for Grep tool path
- **Source**: requirements-coverage-critic
- **Severity**: medium
- **Description**: Denial behavior is verified for the Read and Glob tools, but no scenario verifies that Grep is denied when bypass is inactive. The Grep tool uses a different JSON field for path extraction (`tool_input.path`) than Read or Glob. Because denial scenarios cover only Glob, a silent pass-through caused by wrong-field extraction for Grep would be indistinguishable from a correctly denied request. The denial content scenarios for `CAP-actionable-denial` similarly cover only Glob, leaving the Grep code branch without denial coverage.
- **Triage**: delegate
- **Decision**: Add SCN-denial-grep scenario under REQ-env-var-bypass: Given FSM_BYPASS not set, When agent Greps with path targeting a skill-internal file, Then hook emits deny. Denial message content is tool-agnostic and already covered by CAP-actionable-denial scenarios. Also add corresponding coverage-mapping and manual-test-procedure payload entries.
- **Status**: resolved
- **Outcome**: Added SCN-denial-grep scenario (given FSM_BYPASS not set, when Grep targets skill-internal file, then deny emitted) under REQ-env-var-bypass. Added SCN-denial-grep to coverage-mapping as manual. Added SCN-denial-grep payload to manual-test-procedure. Added SCN-denial-grep to TSK-verify-bypass denial scenarios checklist. [diff: +10/-0 spec.yaml]

### GAP-39: Grep bypass test payload uses directory path rather than a skill-internal file
- **Source**: verification-critic
- **Severity**: medium
- **Description**: The infra manual-test-procedure payload for the Grep bypass scenario specifies a directory path rather than a specific skill-internal file name. If the hook matches on file names such as SKILL.md, fsm.json, or hooks.json, a directory path would not match any blocked pattern, causing the bypass assertion to pass trivially regardless of whether bypass logic fired. This is the same distinguishability concern identified for other scenarios, applied to the Grep payload specifically.
- **Triage**: delegate
- **Decision**: Update SCN-bypass-active-grep payload path from directory ("/path/to/skills/") to a specific skill-internal file ("/path/to/skills/SKILL.md") so the hook's pattern matching would trigger without bypass, making bypass behavior distinguishable from non-triggered hook.
- **Status**: resolved
- **Outcome**: Changed SCN-bypass-active-grep payload path from '/path/to/skills/' to '/path/to/skills/SKILL.md' so the hook's pattern matching would trigger without bypass, making bypass behavior distinguishable. Also updated TSK-verify-bypass description from 'path to skills/' to 'path to SKILL.md' for consistency. [diff: +2/-2 spec.yaml]

### GAP-40: Infra payloads omit `tool_name` field, leaving hook routing behavior undocumented
- **Source**: design-for-test-critic
- **Severity**: medium
- **Description**: The manual test procedure provides fabricated JSON payloads containing only `tool_input`, but Claude Code PreToolUse hooks receive a payload that also includes a `tool_name` field. The infra does not document whether the hook script uses `tool_name` to distinguish tool types or infers the tool from which `tool_input` keys are present. If the script routes on `tool_name`, payloads missing that field would not faithfully reproduce real invocations, causing bypass and tool-routing tests to behave differently in the test harness than in production.
- **Triage**: delegate
- **Decision**: Add tool_name field to all manual-test-procedure payloads (Read, Glob, Grep as appropriate per scenario) for production-faithful payloads. Add a note documenting that the hook script routes via tool_input key presence (not tool_name), so tool_name serves as documentation fidelity, not a routing key.
- **Status**: resolved
- **Outcome**: Added tool_name field (Read, Glob, or Grep as appropriate) to all 9 per-scenario payloads. Added a note explaining that the hook script routes via tool_input key presence, not via tool_name, so tool_name serves as documentation fidelity. [diff: +13/-9 spec.yaml]

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

### GAP-27: System-overview diagram contradicts established empty-string bypass semantics
- **Source**: design-critic
- **Severity**: medium
- **Triage**: delegate
- **Decision**: Update diagram labels from "FSM_BYPASS set/unset" to "FSM_BYPASS non-empty" / "FSM_BYPASS empty or unset" while keeping the two-branch structure. Update CMP responsibility to "Check FSM_BYPASS env var non-empty early-exit."
- **Description**: The system-overview diagram models bypass as a two-state decision: FSM_BYPASS set leads to Allow, FSM_BYPASS unset leads to Deny. In shell semantics, a variable exported as an empty string counts as "set." The requirements section (per the resolution that added the empty-string denial scenario) establish that bypass requires a non-empty value. The diagram's two-state model does not reflect this and would lead an implementer to use a presence check rather than a non-empty value check. The CMP responsibility describing the bypass check also omits the non-empty constraint.
- **Status**: resolved
- **Outcome**: Updated system-overview diagram edge labels from "FSM_BYPASS set" to "FSM_BYPASS non-empty" and "FSM_BYPASS unset" to "FSM_BYPASS empty or unset". Updated CMP-block-skill-internals responsibility from "Check FSM_BYPASS env var early-exit" to "Check FSM_BYPASS env var non-empty early-exit."

### GAP-28: DEC-env-var-over-file-flag does not establish inheritance chain feasibility
- **Source**: technical-critic
- **Severity**: medium
- **Triage**: delegate
- **Decision**: Add a feasibility note to the technical context documenting that Claude Code hooks execute as child processes (standard Unix subprocess model), and that environment variables are inherited by default in this model. The project's own Context section already states hooks communicate via stdin/stdout, confirming standard subprocess behavior. The manual test procedure provides empirical validation by testing with FSM_BYPASS exported in the shell.
- **Description**: DEC-env-var-over-file-flag accepts that bypass is inherited by child processes as a known trade-off, but neither the decision nor any other section documents that the full inheritance chain — from the developer's shell through the Claude Code process to the hook subprocess — is actually preserved. If Claude Code strips or resets environment variables when invoking hooks, FSM_BYPASS would never be visible to the hook at runtime. No feasibility evidence or reference appears anywhere in the spec.
- **Status**: resolved
- **Outcome**: Extended technical context to document that Claude Code hooks execute as child processes following the standard Unix subprocess model where environment variables are inherited by default, that stdin/stdout communication confirms standard subprocess behavior, and that the manual test procedure provides empirical validation.

### GAP-29: REQ-updated-denial-message rule body uses hook API field name
- **Source**: requirements-critic
- **Severity**: medium
- **Triage**: delegate
- **Decision**: Replace "systemMessage" with "denial message" in the REQ-updated-denial-message rule statement, consistent with GAP-25's approach in the Then clauses.
- **Description**: The normative rule statement for REQ-updated-denial-message instructs what "the denial systemMessage MUST tell the user." GAP-25 updated the Then clauses in the scenarios under this requirement to use behavioral language, but the rule statement itself was not updated. The word "systemMessage" in the rule body is a hook API field name, not a user-facing concept — the same class of issue GAP-25 resolved in the Then clauses. The rule and its scenarios now use inconsistent language for the same concept.
- **Status**: resolved
- **Outcome**: Changed REQ-updated-denial-message rule from "The denial systemMessage MUST tell the user" to "The denial message MUST tell the user", consistent with GAP-25's behavioral language in the Then clauses.

### GAP-30: REQ-env-var-bypass scenario When clauses name an internal script
- **Source**: requirements-critic
- **Severity**: medium
- **Triage**: delegate
- **Decision**: Rewrite all REQ-env-var-bypass When clauses to use behavioral action framing: "The agent attempts to [Read/Glob/Grep] a skill-internal file" instead of naming the internal script. Co-thematic with GAP-31 for denial scenario When clauses.
- **Description**: Every scenario under REQ-env-var-bypass uses an internal script name as the When step trigger. BDD When clauses should describe the external action that initiates behavior, not the name of the internal component that runs. Coupling When to a script name means any rename of that component invalidates all scenario statements. GAP-1, GAP-5, and GAP-17 removed internal component names from other spec sections but the scenario When clauses were not addressed.
- **Status**: resolved
- **Outcome**: Rewrote all 6 REQ-env-var-bypass scenario When clauses from "block-skill-internals.sh executes" to behavioral action framing (e.g., "The agent attempts to Read a skill-internal file (SKILL.md)"). Moved the agent action from Given to When, making When the behavioral trigger and Given purely preconditions. Co-thematic with GAP-31.

### GAP-32: Manual test procedure Grep payload places file path in wrong field
- **Source**: verification-critic
- **Severity**: medium
- **Triage**: delegate
- **Decision**: Split Glob and Grep payload examples in the manual test procedure. Glob uses `{"tool_input": {"pattern": "..."}}` (file glob). Grep uses `{"tool_input": {"pattern": "some_regex", "path": "/path/to/skills/"}}` (search regex + file path). Co-resolves with GAP-33 for per-scenario payload examples.
- **Description**: The manual test procedure's Glob and Grep payload example uses `{"tool_input": {"pattern": "..."}}` for both tools. In the Claude Code Grep tool schema, `pattern` carries the search regex and `path` carries the file path to search within. Placing a file path in the `pattern` field constructs a syntactically valid but semantically incorrect payload. A tester following the procedure literally for a Grep scenario does not exercise real Grep behavior; the hook would receive a path where a regex is expected.
- **Status**: resolved
- **Outcome**: Rewrote manual-test-procedure to list per-scenario payload examples. Glob scenarios use {"tool_input": {"pattern": "..."}} (file glob). Grep scenario uses {"tool_input": {"pattern": "some_regex", "path": "/path/to/skills/"}} (search regex + file path). Read scenarios use {"tool_input": {"file_path": "..."}} with the correct file path per scenario (SKILL.md or hooks.json). Co-resolves with GAP-33.

### GAP-31: Denial scenario When clauses use deny emission as the triggering action
- **Source**: requirements-critic
- **Severity**: low
- **Triage**: delegate
- **Decision**: Restructure SCN-denial-contains-bypass-instructions and SCN-denial-removes-plugin-advice Given/When/Then: move the tool invocation to When (agent attempts to Glob a skill-internal file), make the denial content a Then assertion. Co-thematic with GAP-30 for When clause consistency.
- **Description**: SCN-denial-contains-bypass-instructions and SCN-denial-removes-plugin-advice both describe the When step as the hook emitting a deny. In BDD structure, the When step is the external action that initiates the behavior under test; the deny emission is the behavioral outcome that belongs in the Then step. Using an outcome as the When conflates the action being taken with the result being asserted, making the scenario's causal structure ambiguous.
- **Status**: resolved
- **Outcome**: Restructured SCN-denial-contains-bypass-instructions and SCN-denial-removes-plugin-advice: moved tool invocation from Given to When ("The agent attempts to Glob a skill-internal file (fsm.json)"), added "The hook emits a deny decision" as a Then assertion before the denial content assertions. Given now contains only preconditions (FSM_BYPASS not set). Co-thematic with GAP-30.

### GAP-33: Manual test procedure hooks.json scenario uses SKILL.md path example
- **Source**: design-for-test-critic
- **Severity**: low
- **Triage**: delegate
- **Decision**: Add per-scenario payload examples to the manual test procedure showing the correct file path for each scenario (SKILL.md, fsm.json, or hooks.json). Co-resolves with GAP-32 for comprehensive payload restructuring.
- **Description**: The manual test procedure provides a SKILL.md file path as the example path for all Read scenarios, including the scenario added specifically to verify hooks.json blocking behavior. A tester following the procedure literally for the hooks.json scenario would supply a SKILL.md path, never exercising the hooks.json file pattern that the scenario was created to cover.
- **Status**: resolved
- **Outcome**: Co-resolved with GAP-32. Manual-test-procedure now lists per-scenario payload examples with correct file paths: SCN-bypass-active and SCN-bypass-not-set use SKILL.md, SCN-bypass-active-hooks-json uses hooks.json, SCN-denial-contains-bypass-instructions and SCN-denial-removes-plugin-advice use fsm.json glob pattern.

### GAP-35: what-changes descriptions say "reads"/"read" but feature covers Read, Glob, and Grep
- **Source**: implicit-detection
- **Severity**: low
- **Triage**: delegate
- **Decision**: Update CHG-env-bypass from "skill file reads" to "skill file access" and CHG-denial-message from "skill file read is denied" to "skill file access is denied," consistent with the broader tool coverage established by GAP-10.
- **Description**: CHG-env-bypass says "allows skill file reads" and CHG-denial-message says "When a skill file read is denied" but the bypass and denial cover Read, Glob, and Grep operations. The what-changes descriptions were written before GAP-10 broadened scope to include Glob/Grep scenarios, creating an inconsistency between functional change descriptions and the capabilities/requirements they support.
- **Status**: resolved
- **Outcome**: Updated CHG-env-bypass from "allows skill file reads" to "allows skill file access" and CHG-denial-message from "When a skill file read is denied" to "When skill file access is denied."

### GAP-24: Functional `why` uses "task hydration" implementation term
- **Source**: resolution-leakage-detection
- **Severity**: low
- **Triage**: delegate
- **Decision**: Replace "task hydration" with behavioral language ("automatic task creation") in functional `why`. The developer's experience is that tasks appear automatically — "task hydration" is internal FSM mechanism terminology.
- **Description**: Resolution of GAP-5 introduced "task hydration" in functional `why`. This is an implementation mechanism name (internal FSM jargon for how the plugin populates task lists). The rewrite removed script names but substituted an internal term.
- **Status**: resolved
- **Outcome**: Replaced "task hydration" with "automatic task creation" in functional `why`.

### GAP-26: User-impact section uses "hook" terminology in two places
- **Source**: functional-critic
- **Severity**: low
- **Triage**: delegate
- **Decision**: Replace "hook" with behavioral language in user-impact: out-of-scope "Persistent hook configuration changes" → "Persistent bypass configuration changes"; known-risks "the hook is a development guardrail" → "the access gate is a development guardrail."
- **Description**: The functional user-impact section uses the word "hook" in two places: once in an out-of-scope item referencing persistent bypass configuration changes, and once in a known-risks entry describing the access gate as a development guardrail. A developer experiencing a denial does not think in terms of hooks — they interact with a denial message. Both uses expose implementation framing where behavioral or user-experience language is appropriate.
- **Status**: resolved
- **Outcome**: Replaced "Persistent hook configuration changes" with "Persistent bypass configuration changes" in out-of-scope. Replaced "the hook is a development guardrail" with "the access gate is a development guardrail" in known-risks.

### GAP-41: Bypass env-var scenarios couple allow/deny behavior with denial message content assertions
- **Source**: requirements-critic
- **Severity**: low
- **Description**: The bypass env-var requirement scenarios for the "bypass not set" and "bypass empty string" cases each contain a second then-clause asserting denial message content. The scope of `REQ-env-var-bypass` is allow/deny behavior based on env var state; message content is the domain of `REQ-updated-denial-message` and is covered by dedicated denial content scenarios. These second then-clauses couple two capabilities' assertions in a single scenario, violating the one-scenario-one-behavior principle.
- **Triage**: delegate
- **Decision**: Remove the second Then clauses ("The deny message includes instructions to set FSM_BYPASS") from SCN-bypass-not-set and SCN-bypass-empty-string. Each scenario keeps only "The hook emits a deny decision." Message content is already covered by dedicated scenarios under CAP-actionable-denial. Consistent with GAP-9's established one-scenario-one-behavior pattern.
- **Status**: resolved
- **Outcome**: Removed 'The deny message includes instructions to set FSM_BYPASS' from both SCN-bypass-not-set and SCN-bypass-empty-string Then clauses. Each scenario now asserts only 'The hook emits a deny decision.' Message content is covered by dedicated scenarios under CAP-actionable-denial. [diff: +0/-2 spec.yaml]

### GAP-42: "the hook" in `REQ-updated-denial-message` uses internal implementation terminology
- **Source**: requirements-critic
- **Severity**: low
- **Description**: The normative rule in `REQ-updated-denial-message` retains the phrase "to bypass the hook for the session," where "the hook" refers to the Claude Code PreToolUse hook mechanism — an internal implementation concept, not a user-observable behavior. Established cleanup patterns in this spec removed "hook" from user-impact language and "systemMessage" from the same rule body, but this phrase was not addressed. The rule should use behavioral language consistent with those prior cleanups.
- **Triage**: delegate
- **Decision**: Rephrase REQ-updated-denial-message rule from "to bypass the hook for the session" to "to allow skill file access for the session." Eliminates internal mechanism terminology and uses positive behavioral language consistent with prior cleanups (GAP-1, GAP-5, GAP-25, GAP-26, GAP-29).
- **Status**: resolved
- **Outcome**: Changed rule text from 'to bypass the hook for the session' to 'to allow skill file access for the session', eliminating internal mechanism terminology consistent with prior cleanups. [diff: +2/-2 spec.yaml]

### GAP-43: `TSK-update-denial-message` implies identical treatment of `systemMessage` and `permissionDecisionReason`
- **Source**: code-tasks-critic
- **Severity**: low
- **Description**: `TSK-update-denial-message` describes updating both `systemMessage` and `permissionDecisionReason` with unified language, implying identical treatment of both fields. `INT-deny-response` in the technical section makes their requirements qualitatively different: `systemMessage` carries explicit MUST/MUST NOT content constraints, while `permissionDecisionReason` requires only a brief reason referencing the bypass mechanism. The task's unified framing could lead an implementer to write full instructional text in `permissionDecisionReason` or a brief reason in `systemMessage`, both of which would violate the respective field's contract.
- **Triage**: delegate
- **Decision**: Rewrite TSK-update-denial-message to differentiate field treatment: "Update systemMessage with developer-facing bypass instructions per INT-deny-response content constraints (MUST/MUST NOT). Update permissionDecisionReason with a brief denial reason referencing the bypass mechanism." One task, distinct guidance per field.
- **Status**: resolved
- **Outcome**: Replaced unified 'Replace systemMessage and permissionDecisionReason with text that instructs...' with differentiated guidance: 'Update systemMessage with developer-facing bypass instructions per INT-deny-response content constraints (MUST/MUST NOT). Update permissionDecisionReason with a brief denial reason referencing the bypass mechanism.' [diff: +5/-2 spec.yaml]

### GAP-44: `TSK-verify-bypass` denial scenario assertions are underspecified
- **Source**: test-tasks-critic
- **Severity**: low
- **Description**: Denial scenario assertions in `TSK-verify-bypass` state only "deny JSON emitted" without asserting exit code or JSON structure. The infra testing-strategy explicitly distinguishes denial-via-JSON (hook exits 0 with JSON) from denial-via-nonzero-exit, and requires verifying that stdout contains a JSON object with `decision`, `systemMessage`, and `permissionDecisionReason` fields. The task's reference to the manual test procedure is scoped to payload construction, not verification criteria. A tester following only the task's enumerated assertions would skip both exit-code verification and structural field checks, leaving distinct observable behaviors unasserted.
- **Triage**: delegate
- **Decision**: Add a general verification preamble to TSK-verify-bypass before the scenario list: "For all denial scenarios, verify: hook exits 0, stdout is a JSON object containing decision, systemMessage, and permissionDecisionReason fields." Avoids per-scenario repetition while making structural requirements explicit. Also add the new SCN-denial-grep scenario to the verification checklist.
- **Status**: resolved
- **Outcome**: Added preamble: 'For all denial scenarios, verify: hook exits 0, stdout is a JSON object containing decision, systemMessage, and permissionDecisionReason fields.' Added SCN-denial-grep as item 7 in denial scenarios. Simplified denial scenario assertions for SCN-bypass-not-set and SCN-bypass-empty-string to 'deny JSON emitted' (structural checks now covered by preamble). Renumbered denial message content scenarios to 8-9. [diff: +11/-8 spec.yaml]
