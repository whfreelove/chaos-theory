## Context

This is a CLI plugin repository with no deployed services. Infrastructure consists of the test pipeline: pytest configured via `pyproject.toml`, `make test` entry point, and GitHub Actions CI (`.github/workflows/test.yml`). The existing CI workflow runs on push to `main` and on pull requests — no special deployment process exists beyond merging a PR.

## Objectives

`OBJ-test-pass`: `make test` passes with the same count as before migration — no regressions from moving helpers.

`OBJ-convention-verified`: `grep -r "from conftest import" tests/` returns zero matches after migration, confirming all bare conftest imports are eliminated.

## Testing Strategy

### Requirements Coverage

- **Rule 1** (`@isolated-plugin-tests:1` — helper module separation): Verified by `grep -r "from conftest import" tests/` returning zero matches, `make test` confirming fixture injection resolves correctly, `make test PYTESTFLAGS="-W error::pytest.PytestCollectionWarning"` confirming no collection warnings, and `pytest --collect-only` confirming helper modules are not collected. The existing FSM tests serve as the canary — if the migration introduced any import or fixture resolution issue, these tests would fail. Cross-plugin conftest isolation (previously Rule 1) is a structural property of `importmode = "importlib"` documented in technical.md Decisions, not verified by dedicated scenarios.

### Test Approach

No new test files are needed. The migration is a module-level reorganization — the existing test suite validates that the moved functions work identically from their new location. CI validates automatically on the PR via the existing workflow.

Each plugin's test fixtures and test data are self-contained within its own directory — no shared test data infrastructure is needed. Migration verification relies on each plugin's existing test suite exercising its helpers through its own fixtures.

### Conventions

- **conftest.py is fixtures-only**: Each `conftest.py` under `tests/plugins/*/` contains exclusively `@pytest.fixture`-decorated functions. Under `importmode = "importlib"`, non-fixture code in conftest.py cannot be bare-imported — the convention is self-enforcing.
- **Helper module naming**: Helper modules (e.g., `helpers.py`) must not match pytest's collection patterns (`test_*.py` or `*_test.py`). Any name other than `conftest` works; `helpers` communicates intent and avoids collection. pytest will not attempt to collect `helpers.py` as a test module.
- **No bare imports across plugin boundaries**: Under `importmode = "importlib"`, bare `from conftest import` and `from helpers import` statements fail by design. Helper functions are exposed to test files via fixture wrapping: `conftest.py` loads helper modules via `importlib.util.spec_from_file_location` and exposes their functions as `@pytest.fixture(scope="session")` fixtures. Test files receive helpers through fixture injection — no import statements needed.

### Verification Commands

All verification commands run from the repository root (the directory containing `pyproject.toml`).

```bash
make test                                    # Expected: same count as before migration, all passed
make test PYTESTFLAGS="-W error::pytest.PytestCollectionWarning"  # Expected: same count, no collection warnings
grep -r "from conftest import" tests/        # Expected: zero matches
pytest --collect-only tests/                 # Expected: no helper modules (e.g., helpers.py) appear in collected items
```

The combination of `make test` (behavioral verification), `grep` (static review-time check), and `pytest --collect-only` (collection verification) provides defense in depth. `make test` confirms imports resolve and tests pass at runtime. `grep` catches stale bare imports at review time. The `-W error::pytest.PytestCollectionWarning` flag narrows warning-as-error treatment to collection-specific warnings, ensuring that collection warnings about helper modules surface as test failures without catching unrelated warnings (deprecation warnings, resource warnings, third-party library warnings) that would require triage. `pytest --collect-only` verifies that helper modules named to avoid pytest collection patterns (`test_*.py`, `*_test.py`) are not collected — this is the concrete verification mechanism for the naming convention guarantee (@isolated-plugin-tests:1.1).

No separate verification command is needed to confirm `importmode = "importlib"` is active in pytest's configuration. The defense-in-depth strategy implicitly proves it: if importlib mode were misconfigured, bare imports would still resolve via `sys.path` (so `grep` would find them in use, or tests relying on fixture injection would fail because bare imports would mask the fixtures), and `make test` would surface the resulting failures. The four verification commands together provide stronger evidence of correct importlib configuration than a config-level check alone.

## Migration

All file paths in the migration steps below are relative to the repository root (the directory containing `pyproject.toml`).

### Steps

1. **Add importlib mode to `pyproject.toml`**: In the `[tool.pytest.ini_options]` section, add `importmode = "importlib"`. This stops pytest from adding test directories to `sys.path`, eliminating cross-plugin module name collisions at the root cause.

2. **Create `tests/plugins/finite-skill-machine/helpers.py`**: Move `run_hook()` and `_make_task_file()` from `conftest.py` to this new module. Both are cross-module helpers: `run_hook` is bare-imported by `test_hydrate_tasks.py`, and `_make_task_file` is bare-imported at line 8 alongside `run_hook`. Both follow the same pattern — defined in helpers.py, loaded by conftest.py via `importlib.util.spec_from_file_location`, exposed as session-scoped fixtures.

3. **Update imports in `tests/plugins/finite-skill-machine/test_hydrate_tasks.py`**: Remove line 8 (`from conftest import run_hook, _make_task_file`). Both `run_hook` and `_make_task_file` are now received via fixture injection — conftest.py exposes each as a `@pytest.fixture(scope="session")` that returns the callable loaded from helpers.py via `importlib.util.spec_from_file_location`. No import statement needed in test files.

4. **Remove `run_hook` and `_make_task_file` from `conftest.py`**: Delete both `run_hook()` and `_make_task_file()` function definitions from `tests/plugins/finite-skill-machine/conftest.py`. The 14 `@pytest.fixture` functions remain. conftest.py loads both functions back from helpers.py via `importlib.util.spec_from_file_location` for its own fixture use (e.g., fixtures that call `_make_task_file`) and exposes them as session-scoped fixtures for test files.

5. **Update FSM project specs** (tracked in tasks.yaml):
   - `openspec/finite-skill-machine/technical.md` — update migration note: `from conftest import run_hook, _make_task_file` is replaced by fixture injection from conftest.py
   - `openspec/finite-skill-machine/infra.md` — update helper location: "in `conftest.py`" to "in `helpers.py`"

6. **Run verification commands**: Execute all four verification commands listed above. All must pass before the migration is complete. Note: these commands assume steps 1-5 have been completed — in particular, `--collect-only` and `grep` checks cannot distinguish between "correctly excluded/eliminated" and "never created." Post-migration, `make test` catches helper absence through broken fixture injection, making this a one-time migration concern only.

### Rollback

Revert the PR. No data migration, no state to unwind.
