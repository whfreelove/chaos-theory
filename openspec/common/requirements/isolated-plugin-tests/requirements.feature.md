# Feature: Isolated plugin tests (isolated-plugin-tests)

<!--
MDG format. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

TERMINOLOGY (functional spec language → Gherkin keyword):
- "Capability" → "Feature" (one Feature per capability)
- "Requirement" → "Rule" (requirements are grouped as Rules)

PROJECT-LEVEL: Flat structure, no delta wrappers (ADDED/MODIFIED/REMOVED).
-->

## Requirements

`@isolated-plugin-tests:1`
### Rule: Non-fixture test helpers SHALL be importable without cross-plugin collision

#### Background

- Given multiple plugin test directories exist under `tests/plugins/`
- And pytest is configured with `importmode = "importlib"`

`@isolated-plugin-tests:1.1`
#### Scenario: Helper module does not trigger test collection

- Given a plugin test directory contains a helper module that does not match pytest collection patterns
- When all tests are run from the project root
- Then pytest does not report the helper module in collected items

`@isolated-plugin-tests:1.2`
#### Scenario: No warnings from helper module during collection

- Given a plugin test directory contains a helper module that does not match pytest collection patterns
- When all tests are run from the project root with warnings as errors
- Then the test run completes without collection warnings

`@isolated-plugin-tests:1.3`
#### Scenario: Tests using helper module pass after migration

- Given helper functions have been moved from conftest.py to a helper module
- And test files receive helper functions via fixture injection
- When the migrated plugin's tests run
- Then all tests pass with the same count as before migration
