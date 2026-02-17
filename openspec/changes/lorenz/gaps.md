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

### GAP-1: Verdict signal format is unspecified
- **Source**: implementation-critic
- **Severity**: high
- **Description**: The verdict signal written by plan-gate-skill and consumed by post-tool-hook has no defined JSON schema. The field names, value types, and enumerated verdict values are not specified anywhere in the requirements or technical spec. Without a schema, the conversion protocol in post-tool-hook cannot be validated, and the hash-sensitive handoff between components is untestable. Contributing critics: design-critic (TECHNICAL-2), verification-critic (FUNCTIONAL-2), logic-critic (DESIGN-1), validation-critic (COVERAGE-1).

### GAP-2: Hash computation boundary is ambiguous
- **Source**: technical-critic
- **Severity**: high
- **Description**: The spec references plan file hashing but does not define which bytes are included in the computation — whether the full file content, content excluding metadata sections, or content excluding the gaps block. This ambiguity makes it impossible to determine when a hash mismatch is legitimate and creates an unspecified race condition when a verdict signal write and hash recalculation occur within the same hook invocation. Contributing critics: logic-critic (DESIGN-2), integration-coverage-critic (integration-critic-3).

### GAP-3: plan-gate-skill scenarios are not testable with defined test infrastructure
- **Source**: verification-critic
- **Severity**: medium
- **Description**: The scenarios covering plan-gate-skill critic analysis invoke subagent behavior, but the test infrastructure does not define how subagent outputs are mocked or injected during test execution. Without a fixture or mock contract for subagent responses, the scenarios describe behavior that cannot be exercised by the defined test layout. Contributing critic: design-for-test-critic (TESTABILITY-1).

### GAP-4: pre-tool-hook Rule 3 (empty gaps block handling) belongs in plan-gate-skill, not the hook
- **Source**: verification-critic
- **Severity**: high
- **Description**: A rule in pre-tool-hook governs behavior when the gaps block is empty. This behavior — determining whether there are actionable gaps before allowing the agent to exit — is a skill-level concern, not a hook-level concern. Placing it in the hook conflates enforcement policy with business logic and means the rule has no corresponding scenario in the skill where it semantically belongs. Its test mapping is also incorrect as a consequence. Contributing critics: validation-critic (COVERAGE-2), design-for-test-critic (INFRA-2).

### GAP-5: Leakage detector output contract is unspecified
- **Source**: logic-critic
- **Severity**: medium
- **Description**: The leakage detector subagent produces output that is consumed by subsequent components, but the spec does not define the structure or schema of that output. It is unspecified whether leakage detection modifies the gaps block directly, what format its findings take, and whether a leakage-detection modification triggers a hash recalculation. This gap affects both the integration handoff between the leakage detector and the critic, and the testability of any scenario that involves leakage detection. Contributing critics: technical-critic (FEASIBILITY-3), validation-critic (COVERAGE-3), integration-coverage-critic (integration-critic-1).

### GAP-6: Subagent orchestration sequence conflicts with CLAUDE.md parallel launch policy
- **Source**: design-critic
- **Severity**: high
- **Description**: The architecture specifies that subagents run in sequence — leakage detector before critic, critic before validator — because later subagents depend on earlier outputs. CLAUDE.md mandates that all Task subagents be launched in a single message. These requirements contradict when the dependency chain is sequential. The spec does not acknowledge or justify this conflict, leaving implementors without guidance on how to reconcile the constraint.

### GAP-7: sed platform constraint scope is overstated
- **Source**: design-critic
- **Severity**: low
- **Description**: The technical spec claims that a platform-detection helper for sed portability is needed in every hook. However, at least one hook does not list python3 as a dependency, yet the same sed portability constraint applies there. The claim overstates the scope and creates an internal inconsistency between the dependency list and the stated platform constraint.

### GAP-8: Session discovery via grep has no documented failure mode handling
- **Source**: technical-critic
- **Severity**: medium
- **Description**: pre-tool-hook discovers the plan file by grepping for a session marker. The spec does not document what happens when the grep returns zero matches (no plan file found) or multiple matches (ambiguous plan file). The source of the session ID used in the grep is also unspecified.

### GAP-9: jq dependency lacks Y-statement justification
- **Source**: dependency-critic
- **Severity**: medium
- **Description**: Both hooks declare jq as a dependency for JSON parsing. The spec does not provide a Y-statement justifying why jq was chosen over python3's json module, which is already a required runtime dependency for realpath. Adding jq introduces a non-POSIX dependency without documenting the rationale or the alternatives considered.

### GAP-10: python3 realpath usage is undocumented as a decision
- **Source**: dependency-critic
- **Severity**: low
- **Description**: python3 is used to provide a portable realpath implementation. The spec documents this as a dependency but does not record it as a decision — there is no explanation of why python3 was chosen over readlink -f or shell string operations for this purpose. Without a decision record, future contributors lack context for this choice.

### GAP-11: shasum dependency is undocumented
- **Source**: dependency-critic
- **Severity**: low
- **Description**: Both hooks depend on shasum for SHA-256 hashing, but shasum is not documented as a dependency decision. Since python3 is already required, python3's hashlib module could provide cross-platform hashing without the shasum/sha256sum aliasing problems that arise on different platforms. No decision record explains why shasum was chosen.

### GAP-12: Weak normative language in plan-gate-skill requirements
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: Multiple scenarios in the plan-gate-skill requirements use descriptive or future-tense language ("will", "have") instead of normative SHALL/MUST. This weakens the testability and enforceability of the requirements, as it is unclear which behaviors are mandatory constraints versus informational descriptions.

### GAP-13: Weak normative language in post-tool-hook requirements
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: Scenarios in the post-tool-hook requirements use descriptive language without SHALL/MUST normative markers. As with plan-gate-skill, this makes it unclear which Then-clause behaviors are mandatory specifications versus descriptions of expected system behavior.

### GAP-14: Compound scenario in pre-tool-hook bypass scenarios
- **Source**: requirements-critic
- **Severity**: high
- **Description**: One pre-tool-hook scenario tests two distinct hook behaviors in a single scenario — behaviors from separate hooks that should be independently verifiable. Compound scenarios obscure which specific behavior is under test and make failure diagnosis harder. Each distinct hook behavior should be its own atomic scenario.

### GAP-15: Non-observable outcome in pre-tool-hook scenario
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: A pre-tool-hook scenario describes internal metadata state (hash value update, validation pending flag) as the observable outcome, rather than describing behavior visible to the agent or the test harness. Requirements scenarios should express outcomes in terms of externally observable behavior, not internal implementation state.

### GAP-16: Individual scenarios lack capability tag labels
- **Source**: requirements-critic
- **Severity**: low
- **Description**: All scenarios across the requirements lack individual @capability:N.M tags. Only Rule blocks carry tags. Without per-scenario tags, cross-referencing scenarios in test mappings, coverage matrices, and gap decisions requires describing behavior rather than citing a stable identifier.

### GAP-17: Non-observable outcome in plan-gate-skill critic analysis scenario
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: A plan-gate-skill scenario describes an internal relationship between critic findings ("findings are independent") rather than an observable behavior produced by the system. Scenarios should express outcomes that a test can verify externally, not internal structural properties of the subagent's output.

### GAP-18: Missing scenario for post-tool-hook when plan file has no gaps block markers
- **Source**: requirements-coverage-critic
- **Severity**: medium
- **Description**: No scenario covers what happens when post-tool-hook fires on a plan file that does not yet contain any gaps block markers. This is a plausible early-lifecycle state, and without a scenario, the hook's behavior in this case is unspecified and untested.

### GAP-19: Missing scenario for multiple session markers in a single plan file
- **Source**: requirements-coverage-critic
- **Severity**: medium
- **Description**: No scenario covers a plan file that has accumulated multiple session markers across different sessions. It is unspecified whether the hook should process all markers, only the most recent, or treat this as an error condition.

### GAP-20: Missing scenario for verdict signal timing gap between skill invocation and next exit attempt
- **Source**: requirements-coverage-critic
- **Severity**: low
- **Description**: If the agent invokes plan-gate-skill and then immediately attempts to exit without any further file edit, the verdict signal has not yet been converted by post-tool-hook. No requirement captures this timing scenario or specifies how the system should behave in this state.

### GAP-21: Missing scenario for post-tool-hook fail-open behavior
- **Source**: requirements-coverage-critic
- **Severity**: medium
- **Description**: The technical spec states that post-tool-hook uses a fail-open design — errors in the hook do not block the agent. However, no testable scenario in the requirements covers what happens when the hook encounters an error. The fail-open principle has no corresponding behavioral specification.

### GAP-22: Capabilities are named after components, not actor outcomes
- **Source**: functional-critic
- **Severity**: high
- **Description**: The three capabilities in the functional spec are named after internal implementation components (plan-gate-skill, post-tool-hook, pre-tool-hook) and describe behavior in terms of internal mechanisms. Capability names should describe what an actor can accomplish, not what implementation artifact provides it. The current framing exposes implementation structure rather than user value.

### GAP-23: User Impact section describes technical footprint instead of experience changes
- **Source**: functional-critic
- **Severity**: high
- **Description**: The Scope section under User Impact lists file paths, HTML comment formats, and metadata field names. This describes the technical surface area of the change, not what changes for the user. User Impact should describe observable differences in actor experience before and after the change is applied.

### GAP-24: Known Risks describe technical portability concerns, not human-facing hazards
- **Source**: functional-critic
- **Severity**: medium
- **Description**: The Known Risks section lists implementation portability concerns — sed -i portability, jq dependency, POSIX sed edge cases, whitespace-sensitive hashing. These are engineering concerns. Functional risks should describe hazards that affect users or contributors, expressed in terms of what goes wrong from their perspective, not from the implementation's perspective.

### GAP-25: Overview describes orchestration internals rather than high-level mechanism
- **Source**: functional-critic
- **Severity**: medium
- **Description**: The Overview section names specific model tiers, tool names, and hook firing sequences. At the overview level, readers need to understand how the project works at a high level — what problem it solves and how components relate conceptually. Implementation detail at this level makes the document harder to onboard from.

### GAP-26: Why section describes mechanism instead of human burden
- **Source**: functional-critic
- **Severity**: low
- **Description**: The Why section begins explaining the problem being solved but drifts into describing the solution mechanism. The Why section should articulate the burden or friction that exists without the change — leaving solution description to the Overview and capabilities.

### GAP-27: Verdict signal conversion scenario has undefined ordering conflict in post-tool-hook
- **Source**: verification-critic
- **Severity**: medium
- **Description**: Two post-tool-hook scenarios apply to the same file-edit event but are described as mutually exclusive. The spec does not state what the hook should do when both a verdict signal is present and the content hash has changed simultaneously. The ordering conflict leaves an implementation ambiguity that no scenario resolves.

### GAP-28: Integration Rule 2 scenarios do not cover the gaps-edit re-assessment path
- **Source**: verification-critic
- **Severity**: low
- **Description**: The integration requirements cover the re-assessment path triggered by a plan file edit, but not the path where an agent edits the gaps file and then re-assesses before attempting to exit. This alternative trigger path has no integration-level scenario coverage.

### GAP-29: test_integration.sh is referenced in the test layout but does not exist
- **Source**: design-for-test-critic
- **Severity**: high
- **Description**: The Test Categories table maps at least one scenario to test_integration.sh, but this file does not appear in the Test Layout directory tree. A reference to a non-existent test file makes the test plan internally inconsistent and leaves those scenarios without an executable test location.

### GAP-30: Leakage fixture does not cover threshold boundary scenarios
- **Source**: design-for-test-critic
- **Severity**: low
- **Description**: The skill subagent mocking fixture uses a single leakage_found.json fixture. This fixture cannot distinguish between the different phrase-count threshold states that determine whether leakage is detected. Boundary conditions at each threshold value are not covered by the current fixture design.

### GAP-31: Hash mismatch and pending status precedence is unspecified when both apply simultaneously
- **Source**: logic-critic
- **Severity**: medium
- **Description**: The pre-tool-hook lists hash mismatch and validation-pending status as separate trigger conditions but does not specify which takes precedence when both conditions are true simultaneously — for example, when an agent modifies the gaps file after an assessment has been recorded. The behavior in this compound state is undefined.

### GAP-32: Weak normative language in integration scenario outcomes
- **Source**: integration-critic
- **Severity**: high
- **Description**: All Then clauses across the integration scenarios use descriptive or weak language rather than SHALL/MUST normative markers. Integration scenarios assert cross-component behavior and must use normative language to be verifiable as requirements rather than as narrative descriptions.

### GAP-33: Integration scenario conflates state setup with interaction trigger
- **Source**: integration-critic
- **Severity**: medium
- **Description**: The re-assessment after content change scenario embeds the outcome of a prior interaction as a precondition rather than as a distinct scenario step. This makes the scenario describe internal state transitions as Given clauses instead of establishing clean pre-conditions and testing a single interaction boundary.

### GAP-34: Integration scenarios lack individual scenario identifiers
- **Source**: integration-critic
- **Severity**: high
- **Description**: None of the integration scenarios have individual @integration:N.N tags. Without per-scenario identifiers, scenarios cannot be referenced in gap decisions, test mappings, or coverage matrices by stable identifier. All referencing must describe behavior rather than cite a tag.

### GAP-35: File-level capability tags are duplicated on Rule blocks non-standardly
- **Source**: integration-critic
- **Severity**: low
- **Description**: File-level capability tags appear at the header level and are also duplicated on Rule blocks, which is non-standard. This duplication is not consistent with the tagging approach used in other requirement files and may cause tooling or parsing issues if tag extraction is automated.

### GAP-36: Subagent retry failure leaves plan file in indeterminate metadata state
- **Source**: integration-coverage-critic
- **Severity**: medium
- **Description**: No integration scenario covers what happens to the plan file's metadata when a subagent fails partway through an assessment — for example, if the critic subagent fails after the leakage detector has already written output. The plan file could be left in a state where metadata is partially updated, with no specified recovery path.
