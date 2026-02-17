# Feature: CI Validates PR (ci-validates-pr)

<!--
DO NOT REMOVE THIS HEADER - it documents terminology mapping for editors.

MDG format. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

TERMINOLOGY (proposal language → Gherkin keyword):
- "Capability" → "Feature" (one Feature per capability)
- "Requirement" → "Rule" (requirements are grouped as Rules)

PROJECT-LEVEL: Flat structure, no delta wrappers (ADDED/MODIFIED/REMOVED).
-->

## Requirements

`@ci-validates-pr:1`
### Rule: Tests SHALL run automatically on push and pull request

A GitHub Actions workflow triggers the test suite on push to main and on pull requests. The workflow installs dependencies and runs pytest.

`@ci-validates-pr:1.1`
#### Scenario: Push to main triggers test workflow

- Given a GitHub Actions workflow file exists in `.github/workflows/`
- When a commit is pushed to the `main` branch
- Then the test workflow is triggered

`@ci-validates-pr:1.2`
#### Scenario: Pull request triggers test workflow

- Given a GitHub Actions workflow file exists in `.github/workflows/`
- When a pull request is opened or updated
- Then the test workflow is triggered

`@ci-validates-pr:1.3`
#### Scenario: Workflow has test dependencies available at test step

- Given the test workflow is triggered
- When the workflow reaches the test step
- Then pytest is available on the runner
- And test dependencies are importable

`@ci-validates-pr:2`
### Rule: CI SHALL report test status to GitHub

The test workflow reports pass/fail status to GitHub. Passing tests produce a success status check; failing tests produce a failure status check.

`@ci-validates-pr:2.1`
#### Scenario: Failing tests produce non-zero exit

- Given the test workflow is running
- When at least one test fails
- Then `pytest` exits with a non-zero code
- And the workflow step reports failure

`@ci-validates-pr:2.2`
#### Scenario: Workflow reports failure status to GitHub on test failure

- Given the test workflow is running
- And at least one test has failed
- When the workflow completes
- Then the workflow run is marked as failed
- And the workflow reports failure status to GitHub

`@ci-validates-pr:2.3`
#### Scenario: Passing tests produce success status

- Given the test workflow is running
- When all tests pass
- Then `pytest` exits with code 0
- And the workflow run is marked as successful
- And the workflow reports success status to GitHub

`@ci-validates-pr:3`
### Rule: CI SHALL use the project's pinned Python version

The workflow uses the Python version specified in `.python-version` to match the local development environment.

`@ci-validates-pr:3.1`
#### Scenario: Workflow installs the same Python version as .python-version

- Given `.python-version` specifies a Python version
- When the test workflow runs
- Then `python --version` on the runner matches `.python-version`
