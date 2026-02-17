## Why

Plugin test authors who add a `conftest.py` to their test directory silently break other plugins' tests. The failure manifests as confusing import errors pointing to the wrong module, and nothing prevents it from happening again.

## Capabilities

### New Capabilities

- `isolated-plugin-tests`: Test authors can create `conftest.py` and helper modules in any plugin test directory without cross-plugin import collisions

### Modified Capabilities

None.

## User Impact

### Scope

- Each plugin's tests run in isolation — adding or modifying one plugin's test files cannot break another plugin's test suite
- Test authors can define fixtures and helpers freely within their plugin directory without coordinating with other plugins
- One existing test file requires import path updates as part of this migration

### Out of Scope

- Introducing shared cross-plugin test utilities or a common test library
- Automated enforcement (linting) of test organization conventions
- Changes to pytest fixture discovery behavior
- CI workflow configuration verification (the CI workflow path at `.github/workflows/test.yml` is assumed correct; verification is deferred to implementation time)

### Known Risks

- **Migration friction**: One existing test file requires import path updates. If missed, that test fails until corrected.

## What Changes

- Adding a new plugin test directory with `conftest.py` and helper modules no longer risks breaking existing plugins' tests
- Plugin test suites are structurally isolated from each other — cross-plugin import collisions are prevented by configuration
- Existing tests continue to pass after migration with the same test count
