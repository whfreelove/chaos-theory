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

### GAP-1: helpers.py has same sys.path collision as conftest.py
- **Source**: technical-critic
- **Severity**: high
- **Description**: The proposed solution (moving helper functions to helpers.py) creates the same Python module resolution collision that conftest.py has. When multiple plugins have same-named modules (helpers.py in this case), sys.path resolution is identical for both `from helpers import` and `from conftest import`. No feasibility proof demonstrates that helpers.py avoids the collision that motivated the change.
- **Triage**: check-in
- **Decision**: Adopt `importmode = "importlib"` in pyproject.toml to fix the root cause. pytest's importlib mode stops adding test directories to sys.path, making bare module name collisions structurally impossible. Bare `from conftest import` or `from helpers import` will fail by design — helpers must use fixtures or explicit path-based imports. This is pytest's built-in solution for multi-directory test isolation, available since pytest 6.0 (within the existing >=7.2.0 requirement).
- **Status**: resolved
- **Outcome**: Added importlib context paragraph to technical.md Context section. Added CMP-pyproject component with `importmode = "importlib"` to technical.md Components. Added importlib configuration block to technical.md Architecture/System Overview. Updated Y-statement to reflect importlib as root-cause fix (co-resolved with GAP-18). Added importlib as Migration step 1 in infra.md.

### GAP-2: Scope and What Changes sections describe implementation details instead of user outcomes
- **Source**: functional-critic
- **Severity**: high
- **Description**: The Scope section describes internal file conventions (conftest.py reserved for fixtures, helpers.py for non-fixtures, specific function migration) rather than user-facing behavior boundaries. The What Changes section describes file layout rules (conftest.py contains only fixtures, helpers.py with explicit imports) instead of user-visible outcomes. Functional specs should frame capabilities by actor outcomes, not implementation mechanisms.
- **Triage**: check-in
- **Decision**: Reframe Scope and What Changes sections around user outcomes. Move file conventions (conftest.py, helpers.py) to technical.md. Functional spec should describe what test authors experience, not internal file layout rules.
- **Status**: resolved
- **Outcome**: Rewrote functional.md Scope to describe user outcomes (test isolation, no coordination needed, one migration file). Rewrote What Changes to describe observable effects (no breakage from new plugins, structural isolation, tests pass after migration). File conventions remain in technical.md and infra.md only.

### GAP-3: Requirements scenarios verify internal state instead of observable behavior
- **Source**: requirements-critic
- **Severity**: high
- **Description**: Multiple scenarios test internal implementation state rather than observable behavior. Examples include verifying fixture return values instead of their effects, and checking module loading state (which specific module file was imported) instead of the behavior provided by that import. This couples tests to implementation details.
- **Triage**: check-in
- **Decision**: Rewrite scenarios to verify observable pytest outcomes (test pass/fail, error messages, pytest output) instead of internal state (fixture return values, module loading). With importlib mode, module-loading scenarios are moot — bare imports don't work structurally.
- **Status**: resolved
- **Outcome**: Rewrote all scenarios in requirements/isolated-plugin-tests/requirements.feature.md. Rule 1 scenarios verify test pass counts, absence of import errors, and fixture isolation via test outcomes. Rule 2 scenarios verify collection exclusion, warning-free runs, and post-migration test pass counts. No internal state assertions remain. Co-resolved with GAP-8 (atomicity) in a single rewrite pass.

### GAP-4: Test infrastructure missing for cross-plugin scenarios
- **Source**: verification-critic
- **Severity**: high
- **Description**: Multiple requirement scenarios assume multi-plugin test infrastructure that the change doesn't create. Scenarios require adding new plugins with conftest files, same-named fixtures across plugins, and multiple plugins with helpers.py files. No verification mechanism exists for cross-plugin import isolation or same-named fixture isolation. The migration creates a single-plugin refactoring but requirements validate multi-plugin behavior.
- **Triage**: check-in
- **Decision**: Trust pytest importlib mode for structural isolation — don't test pytest itself. Verify only that our migration works: tests pass, no bare imports remain, no regressions. Multi-plugin test infrastructure is unnecessary when isolation is a pytest config setting.
- **Status**: resolved
- **Outcome**: Verified after all artifact updates. infra.md documents importlib mode in Migration step 1 and explains that isolation is a pytest configuration setting. Verification Commands test the end state (make test, grep, -W error). No multi-plugin test infrastructure created.

### GAP-5: conftest-only constraint lacks verification coverage
- **Source**: requirements-coverage-critic
- **Severity**: high
- **Description**: No scenario covers the conftest-only constraint (conftest.py contains only fixtures), and no enforcement mechanism exists for this constraint. The requirement OBJ-conftest-fixtures-only is specified but not validated.
- **Triage**: check-in
- **Decision**: importlib mode makes the conftest-only convention self-enforcing — non-fixture code in conftest.py can't be bare-imported. No separate enforcement mechanism needed. Document this structural guarantee in technical.md.
- **Status**: resolved
- **Outcome**: Updated CMP-conftest description in technical.md to document that under `importmode = "importlib"`, the conftest-only convention is self-enforcing. Added explanation to infra.md Conventions section (conftest.py is fixtures-only).

### GAP-6: Missing concrete migration steps and file paths
- **Source**: implementation-critic
- **Severity**: high
- **Description**: The technical specification doesn't document exact file paths, import syntax changes, or step-by-step migration procedure. The What Changes section describes intent but doesn't provide concrete commands or paths for implementation.
- **Triage**: check-in
- **Decision**: Add concrete migration steps to infra.md Migration section: (1) add importmode="importlib" to pyproject.toml, (2) move helpers to helpers.py, (3) update imports from bare conftest to helpers. Include explicit file paths and import syntax.
- **Status**: resolved
- **Outcome**: Added 6-step Migration section to infra.md with explicit file paths (`pyproject.toml`, `tests/plugins/finite-skill-machine/helpers.py`, `test_hydrate_tasks.py`, `conftest.py`), import syntax changes, FSM spec updates, and verification step. Includes rollback instruction.

### GAP-7: Missing verification and testing strategy
- **Source**: design-critic
- **Severity**: medium
- **Description**: The specification lacks a Unit Testing section documenting how objectives will be verified. No verification mechanism is defined for objectives in the technical specification. This creates ambiguity about what constitutes successful implementation.
- **Triage**: check-in
- **Decision**: Consolidate verification in infra.md. Update existing Verification Commands to include importlib mode verification. No separate Unit Testing section in technical.md needed — infra.md is the single source for verification strategy.
- **Status**: resolved
- **Outcome**: infra.md now contains a complete Testing Strategy section with Requirements Coverage (mapping rules to verification methods), Test Approach, Conventions, and Verification Commands (3 commands with expected outputs and rationale for defense-in-depth approach). Co-resolved with GAP-15 (verification consolidation).

### GAP-8: Atomicity violations in requirement scenarios
- **Source**: requirements-critic
- **Severity**: medium
- **Description**: Multiple scenarios test two independent behaviors in a single scenario. Examples include testing both pass count and absence of import errors, testing both positive module resolution and negative non-loading, and testing both absence of collection and absence of warnings. Each behavior should be verified independently.
- **Triage**: check-in
- **Decision**: Co-resolve with GAP-3. When rewriting scenarios for observable outcomes, also split multi-behavior scenarios into atomic ones. Single rewrite pass addresses both concerns.
- **Status**: resolved
- **Outcome**: All scenarios in requirements/isolated-plugin-tests/requirements.feature.md are atomic. Rule 1 split into: 1.1 (pass count), 1.2 (no import errors), 1.3 (fixture isolation). Rule 2 split into: 2.1 (no collection), 2.2 (no warnings), 2.3 (post-migration pass count). Each scenario tests exactly one observable outcome. Co-resolved with GAP-3.

### GAP-9: Capability slug names file convention instead of user outcome
- **Source**: functional-critic
- **Severity**: medium
- **Description**: The capability is framed by mechanism (conftest-fixture-only) rather than actor outcome. The slug names a file convention, not what capability the user gains.
- **Triage**: check-in
- **Decision**: Rename capability slug from `conftest-fixture-only` to `isolated-plugin-tests`. This describes the user outcome (each plugin's tests are isolated) rather than the implementation mechanism. Cascades through all artifacts: functional.md, requirements directory name, requirements.feature.md, integration.feature.md.
- **Status**: resolved
- **Outcome**: Renamed slug across all artifacts. functional.md capability slug updated. Requirements directory created at `requirements/isolated-plugin-tests/` (old `requirements/conftest-fixture-only/` should be removed). Feature header and all scenario tags in requirements.feature.md use `isolated-plugin-tests`. integration.feature.md references updated. infra.md Requirements Coverage references updated.

### GAP-10: Missing interfaces documentation for cross-file functions
- **Source**: design-critic
- **Severity**: medium
- **Description**: No Interfaces section documents the signatures for run_hook() and _make_task_file() despite these functions being consumed across test files. This creates ambiguity about expected function contracts.
- **Triage**: check-in
- **Decision**: Document interface signatures for run_hook() and _make_task_file() in technical.md's CMP-helpers component. These are cross-file contracts that implementers need.
- **Status**: resolved
- **Outcome**: Added `CMP-helpers Interfaces` subsection to technical.md Components with INT-run-hook and INT-make-task-file. Each documents signature, purpose, and dependencies. Signatures derived from existing conftest.py implementation.

### GAP-11: No scenario for absence of bare conftest imports
- **Source**: requirements-coverage-critic
- **Severity**: medium
- **Description**: The requirement OBJ-zero-bare-conftest-imports specifies no bare conftest imports should exist, but no scenario validates this constraint.
- **Triage**: check-in
- **Decision**: Grep verification command in infra.md is sufficient. importlib mode makes bare imports fail at runtime; grep catches them at review time. No separate requirement scenario needed.
- **Status**: resolved
- **Outcome**: Verified after all artifact updates. infra.md Verification Commands includes `grep -r "from conftest import" tests/` with expected zero matches. The defense-in-depth rationale explains that grep catches stale imports at review time while importlib mode prevents them at runtime.

### GAP-12: No scenario demonstrating the collision error path
- **Source**: requirements-coverage-critic
- **Severity**: medium
- **Description**: No scenario demonstrates the problem the change solves (the collision error condition that motivated the convention). This makes it unclear what behavior constitutes failure.
- **Triage**: check-in
- **Decision**: Not needed with importlib mode. The collision is prevented structurally by pytest configuration. A regression scenario would test pytest internals, which contradicts the GAP-4 decision to trust pytest.
- **Status**: resolved
- **Outcome**: Verified after all artifact updates. Collision is prevented structurally by CMP-pyproject (`importmode = "importlib"`) documented in technical.md. No collision error scenario added, consistent with GAP-4 decision.

### GAP-13: Migration behavior not covered by requirements
- **Source**: validation-critic
- **Severity**: medium
- **Description**: The actual migration behavior (moving FSM helpers from conftest to helpers.py) is not covered by any requirement scenario. Requirements validate the end state but not the migration path.
- **Triage**: check-in
- **Decision**: Requirements cover end state only. Migration steps are one-time tasks documented in infra.md Migration section, not permanent requirement scenarios.
- **Status**: resolved
- **Outcome**: Verified after all artifact updates. infra.md Migration section contains 6 concrete steps with file paths and syntax. Requirements scenarios (@isolated-plugin-tests:2.3) verify post-migration end state (tests pass with same count). Migration path and end-state validation are properly separated.

### GAP-14: Warning check missing from verification commands
- **Source**: verification-critic
- **Severity**: medium
- **Description**: A scenario specifies checking for absence of warnings during test collection, but the verification commands don't include any warning detection mechanism.
- **Triage**: check-in
- **Decision**: Add pytest -W error flag (or equivalent) to make test so warnings become failures. Update infra.md Verification Commands accordingly. This catches collection warnings about helpers.py.
- **Status**: resolved
- **Outcome**: Added `make test PYTESTFLAGS="-W error"` to infra.md Verification Commands as a separate command with expected output. Rationale explains that `-W error` surfaces collection warnings about helper modules as test failures.

### GAP-15: Verification commands check syntax instead of behavior
- **Source**: design-for-test-critic
- **Severity**: medium
- **Description**: The verification command uses grep to check for import statement syntax rather than verifying the actual behavior (whether imports work correctly, whether isolation is maintained).
- **Triage**: check-in
- **Decision**: Grep + make test together are sufficient. Grep catches stale imports at review time, make test verifies behavior at runtime. importlib mode means bad imports fail loudly. Both verification commands remain in infra.md.
- **Status**: resolved
- **Outcome**: infra.md Verification Commands now lists 3 commands (make test, make test -W error, grep) with a defense-in-depth rationale explaining how behavioral verification (make test) and static review-time checks (grep) complement each other. Co-resolved with GAP-7 (verification consolidation).

### GAP-16: Missing documentation about helpers.py naming preventing test collection
- **Source**: logic-critic
- **Severity**: medium
- **Description**: The specification doesn't document that the helpers.py naming convention prevents pytest from collecting it as a test module (pytest looks for test_*.py or *_test.py patterns). This implicit behavior should be explicitly documented as part of the solution.
- **Triage**: check-in
- **Decision**: Document in infra.md Testing Strategy that helper modules must not match pytest collection patterns (test_*.py or *_test.py).
- **Status**: resolved
- **Outcome**: Added "Helper module naming" convention to infra.md Conventions section explaining that helpers.py avoids pytest collection patterns. Also added collection-prevention note to CMP-helpers description in technical.md.

### GAP-17: Known Risks names specific functions and files instead of user-facing risk
- **Source**: functional-critic
- **Severity**: low
- **Description**: The Known Risks section names specific functions (run_hook, _make_task_file) and test files (test_hydrate_tasks.py) rather than describing risks in terms of user-facing impact. This couples the functional spec to implementation details.
- **Triage**: delegate
- **Decision**: Rewrite Known Risks to user-facing language: "One existing test file requires import path updates. If missed, that test fails until corrected." Remove function names and file paths from functional spec.
- **Status**: resolved
- **Outcome**: Rewrote functional.md Known Risks to: "**Migration friction**: One existing test file requires import path updates. If missed, that test fails until corrected." No function names or file paths remain in the functional spec.

### GAP-18: Y-statement contains unquantified claim about disruption
- **Source**: design-critic
- **Severity**: low
- **Description**: The Y-statement says "minimal disruption" without quantifying what minimal means or what scope of disruption is acceptable. This creates ambiguity about the constraint.
- **Triage**: delegate
- **Decision**: Quantify disruption: replace "minimal disruption" with "affecting 2 helper functions in 1 test file" to make the Y-statement precise and verifiable.
- **Status**: resolved
- **Outcome**: Updated Y-statement in technical.md Decisions section. "minimal disruption" replaced with quantified disruption scope. Y-statement also updated with importlib as root-cause fix (co-resolved with GAP-1). Disruption count later corrected to "1 helper function" by GAP-20 resolution, then broadened to "bare-imported helpers in existing test files" by GAP-28 (which superseded GAP-20 and moved both helpers to helpers.py).

### GAP-19: Convention documentation location unspecified
- **Source**: implementation-critic
- **Severity**: low
- **Description**: The specification doesn't indicate where future contributors should learn about the conftest-only convention. No documentation location or format is specified for capturing this rule.
- **Triage**: delegate
- **Decision**: Document the convention in infra.md Testing Strategy section. This is the natural home for test organization rules, and infra.md already covers test strategy. No new files needed.
- **Status**: resolved
- **Outcome**: Added Conventions subsection to infra.md Testing Strategy with three documented conventions: conftest.py is fixtures-only, helper module naming, and no bare imports across plugin boundaries. This is the canonical location for future contributors.

### GAP-20: Migration steps do not address how conftest.py fixtures will import _make_task_file after it moves to helpers.py
- **Source**: implicit-detection
- **Severity**: high
- **Description**: Migration step 2 instructs moving `_make_task_file` from `conftest.py` to `helpers.py`, and step 4 says to delete it from `conftest.py`. However, 5 `@pytest.fixture` functions in `conftest.py` call `_make_task_file` directly. After the move, `conftest.py` must import `_make_task_file` from `helpers.py` -- but the spec states that bare `from helpers import` "fails by design" under `importmode = "importlib"`. The migration steps never address this circular dependency.
- **Triage**: check-in
- **Decision**: Keep `_make_task_file` in conftest.py. It is only consumed by conftest fixtures — it never crosses module boundaries. Only `run_hook` (which test_hydrate_tasks.py bare-imports) moves to helpers.py. Update migration steps, component descriptions, and interface documentation accordingly.
- **Status**: superseded
- **Superseded by**: GAP-28
- **Outcome**: Updated technical.md: CMP-helpers exports only `run_hook`, CMP-conftest retains `_make_task_file` as internal fixture helper, file layout diagram corrected, Y-statement updated to "1 helper function in 1 test file". Updated infra.md migration steps 2 and 4 to reflect only `run_hook` moving. Removed INT-make-task-file interface from CMP-helpers.
- **Current approach**: GAP-28 reverses this decision — `_make_task_file` is bare-imported by `test_hydrate_tasks.py` (line 8) and therefore does cross module boundaries. Both `run_hook` and `_make_task_file` move to helpers.py, loaded by conftest.py via `importlib.util.spec_from_file_location`, and exposed as session-scoped fixtures.

### GAP-21: Import mechanism for helpers.py under importlib mode not specified
- **Source**: design-critic
- **Severity**: high
- **Description**: The specification proposes `importmode = "importlib"` combined with moving `run_hook()` to helpers.py. Under importlib mode, bare `from helpers import` statements fail by design. The specification states "use fixture injection or explicit path-based imports" (technical.md and infra.md Migration step 3) but never specifies what concrete import mechanism works. While GAP-6 added migration steps, those steps remain vague on the actual import syntax that functions under importlib mode. No feasibility proof demonstrates that a working import path exists for helpers.py under the proposed configuration.
- **Triage**: check-in
- **Decision**: Use fixture wrapping. conftest.py loads helpers.py via `importlib.util.spec_from_file_location` and exposes `run_hook` as a `@pytest.fixture(scope="session")` that returns the callable. test_hydrate_tasks.py receives `run_hook` via fixture injection. This is a pure pytest pattern — no sys.path manipulation, no verbose boilerplate in test files. The trade-off is that run_hook's usage changes from direct import to fixture-injected function.
- **Status**: resolved
- **Outcome**: Updated technical.md: Y-Statement narrowed from "fixtures or explicit path-based imports" to fixture wrapping via `importlib.util.spec_from_file_location` with session-scoped fixtures. Context paragraph updated to match. CMP-helpers updated to document conftest.py loads it via importlib.util. CMP-conftest updated with `importlib.util` dependency and fixture wrapping responsibility. INT-run-hook updated to document fixture injection pattern. File layout diagram updated to show fixture wrapping. Updated infra.md: migration step 3 specifies fixture injection (not generic "fixture injection or path-based imports"), Conventions section specifies fixture wrapping pattern. Updated requirements.feature.md: scenario 2.3 narrowed from "fixture injection or explicit path-based imports" to "fixture injection".

### GAP-22: Requirement scenarios assume multi-plugin test infrastructure
- **Source**: verification-critic
- **Severity**: high
- **Description**: Requirement scenarios in the isolated-plugin-tests feature require adding a second plugin with its own conftest.py to verify isolation between plugins. The test infrastructure deliberately omits multi-plugin test fixtures per GAP-4's decision to "trust pytest importlib mode" rather than testing pytest itself. The requirements should verify that importlib configuration is present and the single-plugin migration works correctly, rather than testing cross-plugin isolation directly through multi-plugin test setups.
- **Triage**: check-in
- **Decision**: Collapse Rule 1 into Rule 2. The multi-plugin isolation guarantee is a property of pytest's importlib mode configuration, not behavior we test. Rule 1 scenarios are migration verification (one-time events), not evergreen behavioral requirements. Remove Rule 1 scenarios, document the isolation guarantee in the Decisions section of technical.md, and let Rule 2 (helper module separation) carry the requirements. Rule 2 already covers the migration outcome and helper module conventions.
- **Status**: resolved
- **Outcome**: Removed Rule 1 (`@isolated-plugin-tests:1` — conftest isolation) and its 3 scenarios (1.1, 1.2, 1.3) from requirements.feature.md. Recorded removal in REMOVED Requirements section with rationale referencing GAP-4 and GAP-22. Former Rule 2 renumbered to Rule 1 (`@isolated-plugin-tests:1` — helper module separation) with scenarios renumbered 1.1, 1.2, 1.3. Background section (importlib configuration context) preserved and moved to the new Rule 1. Added Isolation guarantee paragraph to technical.md Decisions section documenting that cross-plugin isolation is a structural property of importlib mode. Updated infra.md Requirements Coverage to reflect single-rule structure and note that conftest isolation is documented in Decisions rather than tested by scenarios.

### GAP-23: Collection exclusion scenario lacks verification method
- **Source**: verification-critic
- **Severity**: medium
- **Description**: A requirement scenario requires verifying that helpers.py does not appear in pytest's collected items, but verification commands in infra.md only check total pass count and grep for bare imports. No mechanism exists to inspect which files pytest collected versus excluded. The scenario specifies an assertion about pytest's internal collection behavior without providing a command to verify that behavior.
- **Triage**: check-in
- **Decision**: Reframe the collection exclusion scenario as a naming convention guarantee. The scenario should verify that helper modules named to not match pytest's test collection patterns (test_*.py, *_test.py) are not collected — testing the convention, not a specific filename. Add `pytest --collect-only` verification command to infra.md to provide the concrete verification mechanism. This makes the scenario evergreen regardless of what helper modules are named.
- **Status**: resolved
- **Outcome**: Reframed scenario 1.1 (formerly 2.1) in requirements.feature.md from "helpers.py with plain functions" to "helper module that does not match pytest collection patterns" — the scenario now tests the naming convention guarantee, not a specific filename. Also reframed scenario 1.2 (formerly 2.2) with matching language. Added `pytest --collect-only tests/` to infra.md Verification Commands as the 4th command with explanation that it verifies the naming convention guarantee for @isolated-plugin-tests:1.1. Updated infra.md Requirements Coverage to reference `--collect-only` as a verification method for Rule 1.

### GAP-24: Migration step 5 says "new import path" but design eliminates imports entirely
- **Source**: implicit-detection
- **Severity**: low
- **Description**: infra.md Migration step 5 instructs the implementer to update the FSM spec's migration note from `from conftest import run_hook` "to new import path." However, the entire design of this change eliminates bare imports — `run_hook` is accessed via fixture injection, not via any import statement. The phrase "new import path" contradicts the design and could lead an implementer to write an incorrect import statement in the FSM spec update instead of documenting fixture injection.
- **Triage**: delegate
- **Decision**: Update migration step 5 wording to accurately reflect fixture injection. Change "update migration note: `from conftest import run_hook` to new import path" to document that the bare import is replaced by fixture injection from conftest.py, not by a new import path.
- **Status**: resolved
- **Outcome**: Updated infra.md migration step 5 first bullet from "to new import path" to "is replaced by fixture injection from conftest.py".

### GAP-25: No test data management strategy for fixture-based helper injection
- **Source**: design-for-test-critic
- **Severity**: medium
- **Description**: The migration moves `run_hook` to fixture-wrapped helper access, but infra.md provides no guidance on test data setup for scenarios verifying fixture injection behavior. While the Testing Strategy references existing FSM tests as a canary, it doesn't document what test data (task files, hook scripts, or other fixtures) must exist for `run_hook` to execute meaningfully during verification. Similar to GAP-23 in resolved.md which addressed collection verification mechanics, but distinct in that this concerns the test data prerequisites rather than the verification command itself.
- **Triage**: check-in
- **Decision**: Add a plugin-agnostic note to infra.md Test Approach stating that each plugin's test fixtures are self-contained within its directory — no shared test data infrastructure is needed. Migration verification relies on each plugin's existing test suite exercising its helpers through its own fixtures.
- **Status**: resolved
- **Outcome**: Added self-contained test data paragraph to infra.md Test Approach section clarifying that each plugin's test fixtures and test data are self-contained within its own directory, and migration verification relies on each plugin's existing test suite.

### GAP-26: Collection verification command may produce false negatives when helper module absent
- **Source**: design-for-test-critic
- **Severity**: low
- **Description**: The collection exclusion verification command `pytest --collect-only tests/` doesn't distinguish between "helper module correctly excluded from collection" versus "helper module doesn't exist." If the migration step creating the helper module is skipped, the command would still show no helper module in collected items, providing a false negative. Related to GAP-23 in resolved.md which added the `--collect-only` command, but addresses a limitation in that verification method's reliability.
- **Triage**: defer-release
- **Decision**: Add note to infra.md Migration section that verification commands (step 6) assume prior migration steps completed. This is a one-time migration concern, not evergreen — post-migration, `make test` catches helper absence through broken fixture injection.
- **Status**: resolved
- **Outcome**: Added note to infra.md Migration step 6 clarifying that verification commands assume steps 1-5 have been completed, and that `--collect-only` and `grep` checks cannot distinguish between "correctly excluded/eliminated" and "never created." Documents that post-migration, `make test` catches helper absence through broken fixture injection.

### GAP-27: Warning sources during importlib.util helper loading not documented
- **Source**: logic-critic
- **Severity**: low
- **Description**: The technical design does not document what warnings might occur when conftest.py loads a helper module via `importlib.util.spec_from_file_location`, or whether this loading pattern is warning-free by design. While GAP-14 in resolved.md added warning detection via the `-W error` flag, the specification doesn't clarify what warnings (if any) are expected from the importlib.util loading mechanism itself versus warnings from other sources.
- **Triage**: delegate
- **Decision**: Add brief note to CMP-conftest in technical.md clarifying that `importlib.util.spec_from_file_location` is a standard library function that does not emit warnings during normal module loading. The `-W error` verification flag serves as a catch-all for any unexpected warnings from any source.
- **Status**: resolved
- **Outcome**: Added "Warning behavior" field to CMP-conftest in technical.md documenting that `importlib.util.spec_from_file_location` is a standard library function that does not emit warnings during normal module loading, and that the `-W error` flag serves as a catch-all for unexpected warnings from any source.

### GAP-28: _make_task_file is bare-imported in test code but spec treats it as conftest-internal
- **Source**: implicit-detection
- **Severity**: high
- **Description**: technical.md states `_make_task_file()` "never crosses module boundaries" and remains in conftest.py as an "internal helper consumed only by fixtures." The Architecture diagram labels it "(internal, used by fixtures)" in the After layout. However, `test_hydrate_tasks.py:995` directly calls `_make_task_file` via the bare import at line 8 (`from conftest import run_hook, _make_task_file`). Migration step 3 in infra.md removes this import line and explains the fixture-injection replacement for `run_hook`, but does not address how `test_hydrate_tasks.py` will access `_make_task_file` after the bare import is removed. The Decisions section compounds this by stating "affecting 1 helper function in 1 test file" when both `run_hook` and `_make_task_file` are consumed via bare import. An implementer following the migration steps would break the test at line 995. Affected files: technical.md (Architecture diagram, CMP-conftest description, Decisions), infra.md (migration step 3).
- **Triage**: check-in
- **Decision**: Move `_make_task_file` to helpers.py alongside `run_hook`. Both cross-module helpers follow the same pattern: defined in helpers.py, loaded by conftest.py via `importlib.util.spec_from_file_location`, exposed as session-scoped fixtures for test files. conftest.py loads both from helpers.py for its own fixture use. Update technical.md (Architecture diagram, CMP-helpers, CMP-conftest, Decisions count) and infra.md (migration steps) accordingly. This supersedes GAP-20's decision that `_make_task_file` stays in conftest.py.
- **Status**: resolved
- **Outcome**: Updated technical.md: Architecture "After" diagram shows both `run_hook` and `_make_task_file` in helpers.py with conftest.py exposing both as session-scoped fixtures. CMP-helpers responsibilities and description updated to include `_make_task_file`. INT-make-task-file interface added to CMP-helpers Interfaces. CMP-conftest updated to load both functions from helpers.py (removed "internal helper" claim for `_make_task_file`). Y-statement updated from "affecting 1 helper function in 1 test file" to "affecting bare-imported helpers in existing test files" (user-confirmed wording). Updated infra.md: migration step 2 includes both functions moving to helpers.py, step 3 documents both received via fixture injection, step 4 documents both removed from conftest.py with conftest.py loading them back for its own fixtures. GAP-20 marked as superseded.

### GAP-29: Hardcoded test count 79 may be stale
- **Source**: implicit-detection
- **Severity**: low
- **Description**: infra.md OBJ-test-pass and the verification commands hardcode "79" as the expected test count. The requirements scenario `@isolated-plugin-tests:1.3` correctly uses relative language ("same count as before migration"), but the infra verification commands say "Expected: 79 passed." If the test count has changed since spec authoring, an implementer would see a mismatch and might incorrectly conclude the migration introduced a regression. The hardcoded count should either be verified at implementation time or replaced with relative language consistent with the requirements scenario.
- **Triage**: delegate
- **Decision**: Replace hardcoded test count "79" with relative language "same count as before migration" in infra.md OBJ-test-pass and verification commands, consistent with the requirements scenario phrasing. Implementer records the pre-migration count and compares post-migration.
- **Status**: resolved
- **Outcome**: Updated infra.md OBJ-test-pass from "same test count (79)" to "same count as before migration." Verification commands updated from "Expected: 79 passed" to "Expected: same count as before migration, all passed." Requirements Coverage updated from "65 FSM tests" to "FSM tests" (removed hardcoded count).

### GAP-30: Working directory for grep verification command not documented
- **Source**: design-for-test-critic
- **Severity**: medium
- **Description**: The verification command `grep -r "from conftest import" tests/` in infra.md Migration section does not specify the working directory from which to run the command. The Context section in technical.md does not define what "project root" means for command execution. An implementer might execute the command from the wrong directory and receive false negatives, concluding that bare imports were successfully eliminated when they still exist in the codebase.
- **Triage**: check-in
- **Decision**: Add a working directory preamble to infra.md Verification Commands section: "All verification commands run from the repository root (the directory containing `pyproject.toml`)."
- **Status**: resolved
- **Outcome**: Added working directory preamble to infra.md Verification Commands section: "All verification commands run from the repository root (the directory containing `pyproject.toml`)." Also added equivalent preamble to infra.md Migration section since migration steps reference file paths relative to the same root.

### GAP-31: No verification mechanism for importlib mode configuration application
- **Source**: design-for-test-critic
- **Severity**: medium
- **Description**: Migration step 1 in infra.md adds `importmode = "importlib"` to pyproject.toml, but no verification command directly confirms that pytest applied this configuration setting. The verification commands in infra.md test consequences of importlib mode (imports work, tests pass) but do not verify the configuration itself was loaded by pytest. An implementer could have a typo in the configuration or place it in the wrong section, and the verification commands might pass due to other factors.
- **Triage**: check-in
- **Decision**: Document that the defense-in-depth verification strategy (make test + grep + -W error + collect-only) implicitly proves importlib mode is active. If importlib mode were misconfigured, bare imports would succeed (grep would find them) or tests would fail (make test would catch it). No separate config-level verification command needed.
- **Status**: resolved
- **Outcome**: Added explanatory paragraph to infra.md Verification Commands section (after the defense-in-depth paragraph) documenting why the existing four-command verification strategy implicitly proves importlib mode is active, making a separate config-level check unnecessary.

### GAP-32: CI workflow path existence unverified
- **Source**: design-for-test-critic
- **Severity**: low
- **Description**: The Context section in technical.md states that CI runs at `.github/workflows/test.yml`, but no verification confirms this file exists or executes the documented verification commands. An implementer following the spec cannot verify that the CI workflow location is correct or that CI will actually run the verification steps.
- **Triage**: defer-release
- **Decision**: Add "CI workflow configuration verification" to functional.md Out of Scope. CI path is assumed correct; verification is deferred to implementation time.
- **Status**: resolved
- **Outcome**: Added "CI workflow configuration verification" bullet to functional.md Out of Scope section, documenting that the CI workflow path is assumed correct and verification is deferred to implementation time.

### GAP-33: Task groupings in tasks.yaml conflict with sequential migration dependencies
- **Source**: test-infra-critic
- **Severity**: high
- **Description**: The infra.md Migration section defines 6 sequential steps with explicit ordering dependencies (step 1 must complete before step 2, etc.). If tasks.yaml groups these steps into parallel task groups that could execute concurrently, an implementer running tasks in parallel would encounter import errors. The sequential migration steps create temporal dependencies that parallel task execution would violate.
- **Triage**: check-in
- **Decision**: Deprecate. The concern is based on a false premise: task groups in tasks.yaml do not imply parallel execution. Tasks and groups are assumed sequential (top to bottom) by current convention. Parallel task dependency graph generation is a planned future feature, not current behavior.
- **Status**: deprecated
- **Rationale**: The concern assumes tasks.yaml task groups imply parallel execution, but current OpenSpec convention treats task groups as sequential (top to bottom). Parallel task dependency graph generation is a planned future feature documented in the FSM roadmap, not current behavior. The migration steps in infra.md are executed sequentially by convention, and no mechanism exists today that would cause them to run concurrently. The premise that "parallel task groups could execute concurrently" does not apply to the current system.

### GAP-34: Warning flag scope broader than documented purpose
- **Source**: test-infra-critic
- **Severity**: medium
- **Description**: The infra.md Verification Commands document `make test PYTESTFLAGS="-W error"` with the purpose of catching collection warnings about helper modules. The `-W error` flag converts all warnings to errors, not only collection warnings. An implementer encountering warning failures must triage each to distinguish relevant collection warnings from unrelated warnings (deprecation warnings, resource warnings, third-party library warnings). Similar to GAP-14 in resolved.md which added the flag, but concerns the triage process that GAP-14 did not address.
- **Triage**: check-in
- **Decision**: Narrow the `-W error` flag to collection-specific warnings. Replace `make test PYTESTFLAGS="-W error"` with `make test PYTESTFLAGS="-W error::pytest.PytestCollectionWarning"` in infra.md Verification Commands and update the accompanying documentation to reflect the narrowed scope.
- **Status**: resolved
- **Outcome**: Replaced `-W error` with `-W error::pytest.PytestCollectionWarning` in infra.md Verification Commands (code block and comment). Updated defense-in-depth explanation paragraph to describe the narrowed scope. Updated infra.md Requirements Coverage to reference the narrowed flag. Updated technical.md CMP-conftest Warning behavior field to reflect the narrowed flag scope. Resolved GAP-14 and GAP-27 entries in resolved.md were not modified (immutable decision history).
