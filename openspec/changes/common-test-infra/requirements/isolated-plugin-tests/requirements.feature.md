# Feature: Isolated plugin tests (isolated-plugin-tests)

<!--
DO NOT REMOVE THIS HEADER - it documents terminology mapping for editors.

MDG format. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

TERMINOLOGY (proposal language -> Gherkin keyword):
- "Capability" -> "Feature" (one Feature per capability)
- "Requirement" -> "Rule" (requirements are grouped as Rules)

We use Gherkin syntax, so headers say "Feature" and "Rule".
-->

## ADDED Requirements

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

## MODIFIED Requirements

## REMOVED Requirements

`@isolated-plugin-tests:1` (original)
### Rule: Adding a conftest.py to a new plugin test directory SHALL NOT affect existing plugins' test results

Removed per GAP-22. The multi-plugin isolation guarantee is a property of pytest's `importmode = "importlib"` configuration, not behavior this change tests. Original scenarios (1.1 existing tests pass, 1.2 no import errors, 1.3 same-named fixture isolation) assumed multi-plugin test infrastructure that the change deliberately omits (GAP-4). The isolation guarantee is documented in technical.md Decisions section instead.

## RENAMED Requirements
