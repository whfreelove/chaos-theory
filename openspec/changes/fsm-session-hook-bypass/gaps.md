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

### GAP-55: INT-deny-response field paths conflict with verification preamble field references
- **Source**: design-technical-consistency-critic
- **Severity**: high
- **Description**: `INT-deny-response` documents the routing fields using a nested structure under a `hookSpecificOutput` wrapper (e.g., `hookSpecificOutput.permissionDecision`, `hookSpecificOutput.permissionDecisionReason`), alongside a flat `systemMessage` field. The verification preamble in `TSK-verify-bypass` checks that stdout contains `decision`, `systemMessage`, and `permissionDecisionReason` fields — referencing top-level field names without the `hookSpecificOutput.` prefix. An implementer following the interface contract would emit nested fields under `hookSpecificOutput`; the verification preamble checking for top-level `decision` would not find them. The two artifacts describe mutually incompatible field locations.

## Medium

### GAP-56: INT-deny-response provides no concrete JSON shape example
- **Source**: design-technical-consistency-critic
- **Severity**: medium
- **Description**: `INT-deny-response` documents its fields using dot-notation (e.g., `hookSpecificOutput.hookEventName`, `hookSpecificOutput.permissionDecision`, `hookSpecificOutput.permissionDecisionReason`) alongside a flat `systemMessage` field, but provides no concrete JSON object showing the full nesting structure. A reader must infer that `systemMessage` is a root-level sibling of a `hookSpecificOutput` object. This is related to the concern raised in resolved GAP-15, which added field descriptions to the interface but did not introduce an example JSON envelope.

### GAP-57: Tool-type routing mechanism is documented only in infra, not in the technical section
- **Source**: technical-critic
- **Severity**: medium
- **Description**: `CMP-block-skill-internals` specifies per-tool path field extraction (file_path for Read, pattern for Glob, path for Grep), but does not describe how the script determines which tool is invoking it. Resolved GAP-40 added a note in the infra manual-test-procedure stating the script routes via `tool_input` key presence rather than `tool_name`. That note lives exclusively in the infra section. A competent engineer reading only the technical section would have no guidance on the routing mechanism and might implement `tool_name`-based routing. The routing behavior belongs at the component responsibility level in the technical section, alongside the per-tool extraction already described there (resolved GAP-37).

### GAP-58: SCN-denial-grep Given clause uses imprecise language instead of established taxonomy
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: The Given clause of `SCN-denial-grep` uses the phrase "FSM_BYPASS is not set" to describe the precondition. Resolved GAP-47 established a precise two-term taxonomy for FSM_BYPASS absence: "not present in the shell environment" and "exported as an empty string". The phrase "not set" does not map to either established term and is ambiguous as to whether it covers the empty-string case. The Given clause should use one of the two taxonomy terms to unambiguously identify which precondition the scenario covers.

## Low

### GAP-59: TSK-verify-bypass does not assert the hookEventName field value
- **Source**: code-tasks-critic
- **Severity**: low
- **Description**: `INT-deny-response` specifies `hookSpecificOutput.hookEventName` as always "PreToolUse". `TSK-verify-bypass` checks `hookSpecificOutput.permissionDecision equals "deny"` but does not assert that `hookSpecificOutput.hookEventName` equals "PreToolUse". The field value is part of the interface contract and is unverified by any task assertion.
