## Why

Plugin test authors need to create test fixtures and helper modules without breaking other plugins' test suites. Contributors need a reproducible, zero-coordination path from clone to green tests. CI needs to validate every PR automatically.

## Capabilities

- `isolated-plugin-tests`: Test authors can create `conftest.py` and helper modules in any plugin test directory without cross-plugin import collisions
- `contributor-reproduces-environment`: A contributor can clone the repo, follow documented steps, and run all plugin tests from the project root
- `ci-validates-pr`: Tests run automatically on push and pull request via GitHub Actions, reporting status to GitHub

## User Impact

### Scope

- Each plugin's tests run in isolation — adding or modifying one plugin's test files cannot break another plugin's test suite
- Test authors can define fixtures and helpers freely within their plugin directory without coordinating with other plugins
- New contributors can set up a working test environment without asking anyone for help
- Existing contributors get a single command to run all plugin tests from the project root
- New plugin tests are automatically discovered without modifying project configuration
- All contributors and CI use the same Python version without manual coordination
- Pull requests are automatically validated — test results are reported as status checks
- The README documents environment setup and test execution for new contributors
- Running tests does not produce files that show up in version control

### Out of Scope

- Version manager compatibility testing (behavior varies across pyenv, asdf, mise)
- Pre-commit hooks for test execution
- Docker-based test environments
- Multi-Python version CI matrix (single version only)
- Documenting minimum tooling requirements (pip 21.3+) and platform-specific alternatives (Windows without Make) in contributor setup instructions
- Specifying which GitHub Actions pull_request activity types trigger CI (platform defaults accepted)
- Failure-path scenarios for individual Makefile targets beyond `make test`
- Explicit CI dependency contract naming which packages must be importable after installation
- Failure-path scenario for malformed `pyproject.toml` (e.g., missing `[project.optional-dependencies]` section)

### Current Limitations

- Introducing shared cross-plugin test utilities or a common test library
- Automated enforcement (linting) of test organization conventions
- Changes to pytest fixture discovery behavior
- Explicit mitigations for four Known Risks: Version file format validation, CI failure disambiguation, Exit code chain assumption, Empty test discovery

### Planned Future Work

- Adding tests for currently untested plugins (worktree-isolation, rodin, tokamak)
- Code coverage tooling or coverage thresholds
- Linting or formatting enforcement in CI

### Known Risks

- **Monorepo test cross-contamination**: Contributors may see false test results if test suites from different plugins interfere with each other. Mitigation: each plugin's tests run in isolation via `importmode = importlib` and per-plugin testpaths.
- **Version file format validation**: Contributors using an invalid Python version string may see cryptic errors from their version manager with no guidance on what went wrong. Accepted without mitigation for initial release.
- **CI failure disambiguation**: Contributors may not be able to distinguish CI dependency installation failures from actual test execution failures in workflow logs. Accepted without mitigation for initial release.
- **Missing venv activation**: Contributors who skip `source .venv/bin/activate` will see `pytest: command not found`. The README documents activation as a mandatory step.
- **Exit code chain assumption**: CI may silently report success when tests fail, giving contributors false confidence to merge. If Makefile recipes are modified to use multi-line commands or pipes, exit codes may be silently swallowed. Accepted without mitigation for initial release.
- **Empty test discovery**: If no plugin test directories exist under `tests/plugins/`, pytest discovers zero tests and exits successfully, giving false confidence that tests pass. Accepted without mitigation for initial release.

## Overview

Plugin test suites are structurally isolated from each other. Adding a new plugin test directory with `conftest.py` and helper modules does not risk breaking existing plugins' tests. Cross-plugin import collisions are prevented by configuration, allowing plugin test suites to maintain independent fixture and helper modules.

Test dependencies are installable via standard Python tooling without manual intervention. All plugin tests are runnable from the project root with a single command. The README documents environment setup and test execution for new contributors. Tests run automatically on push and pull request, reporting test status to GitHub.
