# Chaos Theory Plugin Marketplace

Claude Code plugins leveraging stochastic agent behavior. "Agents, uhh, find a way."

## Installation

```bash
claude plugins marketplace add whfreelove/chaos-theory
```

OpenSpec schemas are auto-initialized on your first session.

## Available Plugins

### Tokamak

A **spec-as-code** reactor that harnesses power from AI agents' thrashing plasma.

An OpenSpec-based, iterative, structured specification workflow based on turning software engineering best practices overhead into background noise.
Agents push you to understand your design through repeated rounds of finding gaps, clarifying your solutions, documenting your decisions, then updating specifications.

#### Setup

[Install OpenSpec](https://github.com/Fission-AI/OpenSpec?tab=readme-ov-file#quick-start) (warning: )

```bash
claude plugins install tokamak
```

A SessionStart hook will install chaos-theory OpenSpec schemas for you (if `openspec/` already exists), and if a Tokamak update includes a new schema version, `/init-schemas` will upgrade.

See [plugins/tokamak/README.md](plugins/tokamak/README.md) for the full change and brownfield documentation workflows.

### finite-skill-machine

Drive complex agent workflows with minimal context and mistakes.

Auto-populates TaskList from skill `fsm.json` companion files. Skills can define multi-step workflows that automatically populate the task list when invoked.

```bash
claude plugins install finite-skill-machine
```

Create a skill with an `fsm.json` alongside `SKILL.md`:

```
my-skill/
├── SKILL.md      # Agent instructions
└── fsm.json      # Task definitions
```

Example `fsm.json`:

```json
[
  {"id": 1, "subject": "Set up environment", "activeForm": "Setting up"},
  {"id": 2, "subject": "Implement feature", "blockedBy": [1]}
]
```

When the skill is invoked, tasks appear automatically in the task list with proper dependencies.

### worktree-isolation

Restricts Claude Code to git worktree or Jujutsu workspace boundaries. Prevents access to project root or sibling worktrees.

## Updating

```bash
# CLI
claude plugins marketplace update

# In-session
/plugins marketplace update
```

## Testing

```bash
python -m venv .venv
source .venv/bin/activate
pip install ".[test]"
```

Run all plugin tests:

```bash
make test
```

Run tests for a specific plugin (target name matches directory name under `tests/plugins/`):

```bash
make test-finite-skill-machine
```

List all available targets:

```bash
make help
```

## License

MIT
