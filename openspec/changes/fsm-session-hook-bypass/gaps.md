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

### GAP-36: `permissionDecisionReason` lacks implementer-actionable content contract
- **Source**: design-critic
- **Severity**: medium
- **Description**: In `INT-deny-response`, `permissionDecisionReason` retains changelog language rather than a stable content contract. Unlike `systemMessage`, which carries explicit MUST/MUST NOT constraints, `permissionDecisionReason` provides no concrete content requirement an implementer can follow to produce a conforming value. The intended "brief denial reason referencing bypass mechanism" is not reflected as a normative constraint in the artifact.

### GAP-37: `CMP-block-skill-internals` does not specify per-tool path field extraction
- **Source**: technical-critic
- **Severity**: medium
- **Description**: The `CMP-block-skill-internals` responsibility to "pattern-match tool input paths against protected file names" does not specify that path extraction requires reading different JSON fields depending on the invoking tool (`tool_input.file_path` for Read, `tool_input.pattern` for Glob, `tool_input.path` for Grep). An implementer reading only the technical component responsibility would likely implement single-field extraction, silently allowing Glob and Grep invocations to pass without matching. The infra manual-test-procedure documents correct payload shapes, but the behavioral contract for field selection belongs at the component responsibility level.

### GAP-38: No denial scenario for Grep tool path
- **Source**: requirements-coverage-critic
- **Severity**: medium
- **Description**: Denial behavior is verified for the Read and Glob tools, but no scenario verifies that Grep is denied when bypass is inactive. The Grep tool uses a different JSON field for path extraction (`tool_input.path`) than Read or Glob. Because denial scenarios cover only Glob, a silent pass-through caused by wrong-field extraction for Grep would be indistinguishable from a correctly denied request. The denial content scenarios for `CAP-actionable-denial` similarly cover only Glob, leaving the Grep code branch without denial coverage.

### GAP-39: Grep bypass test payload uses directory path rather than a skill-internal file
- **Source**: verification-critic
- **Severity**: medium
- **Description**: The infra manual-test-procedure payload for the Grep bypass scenario specifies a directory path rather than a specific skill-internal file name. If the hook matches on file names such as SKILL.md, fsm.json, or hooks.json, a directory path would not match any blocked pattern, causing the bypass assertion to pass trivially regardless of whether bypass logic fired. This is the same distinguishability concern identified for other scenarios, applied to the Grep payload specifically.

### GAP-40: Infra payloads omit `tool_name` field, leaving hook routing behavior undocumented
- **Source**: design-for-test-critic
- **Severity**: medium
- **Description**: The manual test procedure provides fabricated JSON payloads containing only `tool_input`, but Claude Code PreToolUse hooks receive a payload that also includes a `tool_name` field. The infra does not document whether the hook script uses `tool_name` to distinguish tool types or infers the tool from which `tool_input` keys are present. If the script routes on `tool_name`, payloads missing that field would not faithfully reproduce real invocations, causing bypass and tool-routing tests to behave differently in the test harness than in production.

### GAP-41: Bypass env-var scenarios couple allow/deny behavior with denial message content assertions
- **Source**: requirements-critic
- **Severity**: low
- **Description**: The bypass env-var requirement scenarios for the "bypass not set" and "bypass empty string" cases each contain a second then-clause asserting denial message content. The scope of `REQ-env-var-bypass` is allow/deny behavior based on env var state; message content is the domain of `REQ-updated-denial-message` and is covered by dedicated denial content scenarios. These second then-clauses couple two capabilities' assertions in a single scenario, violating the one-scenario-one-behavior principle.

### GAP-42: "the hook" in `REQ-updated-denial-message` uses internal implementation terminology
- **Source**: requirements-critic
- **Severity**: low
- **Description**: The normative rule in `REQ-updated-denial-message` retains the phrase "to bypass the hook for the session," where "the hook" refers to the Claude Code PreToolUse hook mechanism — an internal implementation concept, not a user-observable behavior. Established cleanup patterns in this spec removed "hook" from user-impact language and "systemMessage" from the same rule body, but this phrase was not addressed. The rule should use behavioral language consistent with those prior cleanups.

### GAP-43: `TSK-update-denial-message` implies identical treatment of `systemMessage` and `permissionDecisionReason`
- **Source**: code-tasks-critic
- **Severity**: low
- **Description**: `TSK-update-denial-message` describes updating both `systemMessage` and `permissionDecisionReason` with unified language, implying identical treatment of both fields. `INT-deny-response` in the technical section makes their requirements qualitatively different: `systemMessage` carries explicit MUST/MUST NOT content constraints, while `permissionDecisionReason` requires only a brief reason referencing the bypass mechanism. The task's unified framing could lead an implementer to write full instructional text in `permissionDecisionReason` or a brief reason in `systemMessage`, both of which would violate the respective field's contract.

### GAP-44: `TSK-verify-bypass` denial scenario assertions are underspecified
- **Source**: test-tasks-critic
- **Severity**: low
- **Description**: Denial scenario assertions in `TSK-verify-bypass` state only "deny JSON emitted" without asserting exit code or JSON structure. The infra testing-strategy explicitly distinguishes denial-via-JSON (hook exits 0 with JSON) from denial-via-nonzero-exit, and requires verifying that stdout contains a JSON object with `decision`, `systemMessage`, and `permissionDecisionReason` fields. The task's reference to the manual test procedure is scoped to payload construction, not verification criteria. A tester following only the task's enumerated assertions would skip both exit-code verification and structural field checks, leaving distinct observable behaviors unasserted.
