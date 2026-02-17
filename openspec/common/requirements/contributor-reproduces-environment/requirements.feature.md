# Feature: Contributor Reproduces Environment (contributor-reproduces-environment)

<!--
DO NOT REMOVE THIS HEADER - it documents terminology mapping for editors.

MDG format. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

TERMINOLOGY (proposal language → Gherkin keyword):
- "Capability" → "Feature" (one Feature per capability)
- "Requirement" → "Rule" (requirements are grouped as Rules)

PROJECT-LEVEL: Flat structure, no delta wrappers (ADDED/MODIFIED/REMOVED).
-->

## Requirements

`@contributor-reproduces-environment:1`
### Rule: Project configuration SHALL declare test dependencies

A `pyproject.toml` at the project root declares pytest as a test dependency and configures test discovery for plugin test suites. Contributors install dependencies via standard Python tooling without manual intervention.

`@contributor-reproduces-environment:1.1`
#### Scenario: pip install resolves pytest from pyproject.toml

- Given the repository is freshly cloned
- And a virtual environment is created
- When the contributor runs `pip install ".[test]"`
- Then `pytest --version` exits with code 0

`@contributor-reproduces-environment:1.2`
#### Scenario: pytest discovers plugin tests when run from root

- Given test dependencies are installed
- When the contributor runs `pytest` from the project root
- Then pytest discovers tests under `tests/plugins/*/`
- And pytest exits with code 0 when all tests pass

`@contributor-reproduces-environment:1.3`
#### Scenario: New plugin tests are auto-discovered

- Given test dependencies are installed
- And a test file exists at `tests/plugins/<plugin>/test_placeholder.py` containing one passing test
- When the contributor runs `pytest` from the project root
- Then pytest discovers tests under `tests/plugins/<plugin>/`

`@contributor-reproduces-environment:2`
### Rule: A contributor SHALL be able to run all tests from the project root

A Makefile at the project root provides `make test` (all tests) and `make test-<plugin>` (single plugin) targets. These are the standard entry points for test execution.

`@contributor-reproduces-environment:2.1`
#### Scenario: make test exits 0 when tests pass

- Given test dependencies are installed
- And all tests are passing
- When the contributor runs `make test` from the project root
- Then pytest runs against all configured test paths
- And the exit code is 0

`@contributor-reproduces-environment:2.2`
#### Scenario: make test exits non-zero on failure

- Given test dependencies are installed
- And at least one test is failing
- When the contributor runs `make test` from the project root
- Then the exit code is non-zero

`@contributor-reproduces-environment:2.3`
#### Scenario: make test-<plugin> runs only that plugin's tests

- Given test dependencies are installed
- And test files exist under `tests/plugins/example-other/`
- When the contributor runs `make test-<plugin>` from the project root
- Then pytest runs only tests under `tests/plugins/<plugin>/`
- And no tests from other plugin directories are collected

`@contributor-reproduces-environment:2.4`
#### Scenario: pytest does not discover tests from unconfigured directories

- Given test dependencies are installed
- And a test file exists at `tests/rogue/test_outside.py` outside the configured `tests/plugins/*/` testpaths
- When the contributor runs `pytest` from the project root
- Then only tests from configured testpaths are collected
- And no tests from directories outside `tests/plugins/*/` are discovered

`@contributor-reproduces-environment:2.5`
#### Scenario: make test collects tests from multiple plugin directories

- Given test dependencies are installed
- And test files exist under two or more `tests/plugins/*/` directories
- When the contributor runs `make test` from the project root
- Then pytest discovers tests from all plugin directories

`@contributor-reproduces-environment:3`
### Rule: Python version SHALL be pinned for reproducibility

A `.python-version` file at the project root specifies the Python version used for development and testing.

`@contributor-reproduces-environment:3.1`
#### Scenario: .python-version exists at project root

- Given the repository is freshly cloned
- When the contributor lists files at the project root
- Then a `.python-version` file is present

`@contributor-reproduces-environment:4`
### Rule: Python artifacts SHALL be excluded from version control

`.gitignore` MUST cover Python and pytest artifacts such that running tests SHALL NOT produce git-tracked files.

`@contributor-reproduces-environment:4.1`
#### Scenario Outline: Git ignores Python artifacts

- Given `.gitignore` exists at the project root
- When the contributor runs tests
- And the `<artifact>` path is produced
- Then `git status` does not list `<artifact>` as untracked

##### Examples
| artifact |
|---|
| .pytest_cache/ |
| __pycache__/ |
| *.pyc |
| .venv/ |

`@contributor-reproduces-environment:5`
### Rule: The README SHALL document test setup and execution

The project README contains contributor-facing documentation for setting up the test environment and running tests.

`@contributor-reproduces-environment:5.1`
#### Scenario: README contains environment setup steps

- Given the contributor opens `README.md` at the project root
- When they read the testing section
- Then it describes how to create a virtual environment
- And it describes how to install test dependencies

`@contributor-reproduces-environment:5.2`
#### Scenario: README references Makefile targets

- Given the contributor opens `README.md` at the project root
- When they read the testing section
- Then it documents the `make test` command
- And it documents the `make test-<plugin>` pattern
