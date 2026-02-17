## Context

The project's `pyproject.toml` configures `testpaths = ["tests/plugins/*"]`, which causes pytest to add every matching plugin test directory to `sys.path`. This enables automatic test discovery across plugins but creates an import collision hazard.

pytest handles `conftest.py` through two distinct mechanisms:

1. **Fixture auto-discovery**: `@pytest.fixture` functions in `conftest.py` are auto-discovered by pytest's collection machinery — scoped to their directory and injected without any `import` statement. This works correctly across multiple directories.
2. **Bare Python imports**: Non-fixture functions accessed via `from conftest import func` resolve through Python's standard module system using `sys.path`. When multiple directories on `sys.path` each contain a `conftest.py`, which module Python loads is ambiguous.

Currently, `tests/plugins/finite-skill-machine/conftest.py` mixes both: 14 `@pytest.fixture` functions (correctly auto-discovered) and 2 plain helper functions (`run_hook`, `_make_task_file`) consumed via `from conftest import` in `test_hydrate_tasks.py:8`. Any new plugin adding its own `conftest.py` will shadow or be shadowed by FSM's conftest for bare imports.

pytest's `importmode = "importlib"` (available since pytest 6.0, within the existing >=7.2.0 requirement) stops adding test directories to `sys.path`, making bare module name collisions structurally impossible. Under importlib mode, bare `from conftest import` or `from helpers import` statements fail by design — helper functions must be fixture-wrapped: conftest.py loads helper modules via `importlib.util.spec_from_file_location` and exposes their functions as session-scoped fixtures for test files to receive via injection.

## Objectives

`OBJ-conftest-fixtures-only`: Every `conftest.py` in `tests/plugins/*/` contains exclusively `@pytest.fixture`-decorated functions — no plain helpers, no utility functions, no constants consumed via bare import.

`OBJ-zero-bare-conftest-imports`: Zero `from conftest import` statements exist across all plugin test directories. Verifiable via `grep -r "from conftest import" tests/` returning no matches.

## Architecture

### System Overview

Two changes: a pytest configuration addition and a file layout shift within `tests/plugins/finite-skill-machine/`.

**Configuration** (`pyproject.toml`):
```
[tool.pytest.ini_options]
importmode = "importlib"       # NEW — prevents sys.path-based collisions
```

**File layout**:
```
Before:                              After:
conftest.py                          conftest.py
  ├── 14 @pytest.fixture functions     ├── 14 @pytest.fixture functions
  ├── run_hook()                       ├── run_hook fixture       (session-scoped, wraps helpers.run_hook)
  └── _make_task_file()                └── make_task_file fixture (session-scoped, wraps helpers._make_task_file)
                                     helpers.py
                                       ├── run_hook()
                                       └── _make_task_file()
test_hydrate_tasks.py                test_hydrate_tasks.py
  └── from conftest import ...         └── run_hook, make_task_file (via fixture injection)
```

### Component Interactions

No new inter-component interactions. The change is a pytest configuration addition and a module-level reorganization within a single test directory.

## Components

`CMP-pyproject` (modified): pyproject.toml
- **Description**: Project configuration file. The `[tool.pytest.ini_options]` section gains `importmode = "importlib"`.
- **Responsibilities**: Configure pytest to use importlib-based module resolution instead of sys.path insertion. This is the root-cause fix for cross-plugin import collisions.
- **Dependencies**: pytest >=7.2.0 (importlib mode available since pytest 6.0).

`CMP-helpers`: helpers.py (new)
- **Description**: Named Python module in a plugin test directory containing non-fixture test helper functions. The module name `helpers` avoids pytest's collection patterns (`test_*.py` or `*_test.py`) — pytest will not attempt to collect it as a test module. Under `importmode = "importlib"`, this module cannot be bare-imported; `conftest.py` loads it via `importlib.util.spec_from_file_location` and exposes its functions as fixtures.
- **Responsibilities**: Define `run_hook` and `_make_task_file` — the helper functions that `test_hydrate_tasks.py` previously bare-imported from conftest.py. Module name `helpers` is a convention — any name other than `conftest` works, but `helpers` communicates intent.
- **Dependencies**: `subprocess`, `json`, `os`, `pathlib.Path`.

### `CMP-helpers` Interfaces

`INT-run-hook`: run_hook (exposed as session-scoped fixture)
- **Signature**: `run_hook(session_id: str, command_name: str, cwd: str, task_root: str | None = None, plugins_file: str | None = None, user_skills_root: str | None = None) -> tuple[int, str, str]`
- **Purpose**: Execute the hydrate-tasks.py hook script with JSON stdin, return `(exit_code, stdout, stderr)`. Defined in `helpers.py`; loaded by `conftest.py` via `importlib.util.spec_from_file_location` and exposed as a `@pytest.fixture(scope="session")` that returns the callable. Test files receive `run_hook` via fixture injection.
- **Dependencies**: `subprocess`, `json`, `os`, `pathlib.Path`

`INT-make-task-file`: _make_task_file (exposed as session-scoped fixture)
- **Signature**: `_make_task_file(task_dir: Path, filename: str, content: dict) -> Path`
- **Purpose**: Create a JSON task file in the given directory, return the file path. Defined in `helpers.py`; loaded by `conftest.py` via `importlib.util.spec_from_file_location` and exposed as a `@pytest.fixture(scope="session")` that returns the callable. Test files and conftest.py fixtures receive `_make_task_file` via fixture injection.
- **Dependencies**: `json`, `pathlib.Path`

`CMP-conftest` (modified): conftest.py
- **Description**: pytest auto-discovery file containing exclusively `@pytest.fixture` definitions. Under `importmode = "importlib"`, the conftest-only convention is self-enforcing — non-fixture code in conftest.py cannot be bare-imported because pytest no longer adds the directory to `sys.path`.
- **Responsibilities**: Provide fixtures (`task_dir`, `skill_dir`, `hydrate_module`, etc.) to test files in the same directory. Loads `helpers.py` via `importlib.util.spec_from_file_location` and exposes both `run_hook` and `_make_task_file` as `@pytest.fixture(scope="session")` fixtures returning the callables — this is the bridge between importlib-isolated helper modules and test files.
- **Dependencies**: pytest (for `@pytest.fixture` decorator), `importlib.util` (for loading helpers.py).
- **Warning behavior**: `importlib.util.spec_from_file_location` is a standard library function that does not emit warnings during normal module loading. The `-W error::pytest.PytestCollectionWarning` verification flag targets collection-specific warnings, ensuring that any collection warnings about helper modules surface as failures. This narrowed scope avoids false positives from unrelated warnings (deprecation, resource, third-party) while still catching the collection issues relevant to the helper module migration.

## Decisions

In the context of multi-plugin test infrastructure where `testpaths` glob adds all plugin directories to `sys.path`, facing ambiguous `from conftest import` resolution when multiple plugins have `conftest.py`, we decided to adopt `importmode = "importlib"` in `pyproject.toml` and place non-fixture helpers in named modules (e.g., `helpers.py`) with conftest.py loading them via `importlib.util.spec_from_file_location` and exposing their functions as session-scoped fixtures, and neglected restructuring `testpaths` to avoid `sys.path` sharing, introducing a shared test utilities package, or having test files import helpers directly via `importlib.util`, to achieve collision-free imports by eliminating `sys.path`-based module resolution, affecting bare-imported helpers in existing test files, accepting that bare `from conftest import` and `from helpers import` statements fail by design under importlib mode -- all cross-module helper functions must be fixture-wrapped in conftest.py -- and future contributors must follow this convention without automated enforcement.

**Isolation guarantee**: Cross-plugin test isolation is a structural property of `importmode = "importlib"` — pytest no longer adds test directories to `sys.path`, so module name collisions between plugin directories are impossible by configuration. This guarantee holds for both `conftest.py` and named helper modules. Because the isolation is enforced by pytest's import machinery rather than by test infrastructure we build, the requirement scenarios focus on verifying the helper module migration (the change we make) rather than testing pytest's importlib behavior (GAP-4, GAP-22).
