# Chaos Theory Plugin Marketplace

Claude Code plugins leveraging stochastic agent behavior. "Agents, uhh, find a way."

## Installation

Add this marketplace to your Claude Code:

```bash
/plugin marketplace add whfreelove/chaos-theory
```

## Available Plugins

### worktree-isolation

Restricts Claude Code to git worktree or Jujutsu workspace boundaries. Prevents access to project root or sibling worktrees.

## Updating

```bash
/plugin marketplace update
```

## Developing Plugins

See `plugins/worktree-isolation/` for a reference implementation.

For hook types, input/output formats, and publishing: [Claude Code Hooks Documentation](https://docs.anthropic.com/en/docs/claude-code/hooks)

## License

MIT
