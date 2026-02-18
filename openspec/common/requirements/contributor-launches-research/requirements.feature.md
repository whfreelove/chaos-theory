# Feature: Research notebook environment (contributor-launches-research)

<!--
MDG format. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

TERMINOLOGY (functional spec language → Gherkin keyword):
- "Capability" → "Feature" (one Feature per capability)
- "Requirement" → "Rule" (requirements are grouped as Rules)

PROJECT-LEVEL: Flat structure, no delta wrappers (ADDED/MODIFIED/REMOVED).
-->

## Requirements

`@contributor-launches-research:1`
### Rule: Project configuration SHALL declare research dependencies as optional extras

#### Background

- Given the project uses `pyproject.toml` for dependency management
- And a `test` optional-dependencies group already exists

`@contributor-launches-research:1.1`
#### Scenario: Research extras make JupyterLab importable

- Given the contributor has installed the project with research extras via `pip install -e ".[research]"`
- When the contributor runs `python -c "import jupyterlab"`
- Then the import succeeds without error

`@contributor-launches-research:1.2`
#### Scenario: Research extras do not install with test extras

- Given the contributor has installed the project with test extras only via `pip install -e ".[test]"`
- When the contributor runs `python -c "import jupyterlab"`
- Then the import fails with ModuleNotFoundError

`@contributor-launches-research:2`
### Rule: A contributor SHALL be able to launch JupyterLab from the project root

`@contributor-launches-research:2.1`
#### Scenario: Makefile research target launches JupyterLab

- Given the contributor has a virtual environment activated
- When the contributor runs `make research`
- Then research extras are installed
- And JupyterLab launches with notebook-dir pointed at the `research/` directory

`@contributor-launches-research:3`
### Rule: Research artifacts SHALL be excluded from version control

`@contributor-launches-research:3.1`
#### Scenario: Jupyter checkpoint directories are gitignored

- Given the `research/` directory contains a `.gitignore` file
- When a notebook creates a `.ipynb_checkpoints/` directory inside `research/`
- Then `git status` does not show the checkpoint directory as untracked
