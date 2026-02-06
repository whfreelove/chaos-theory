# Chaos Theory Plugin Marketplace

Claude Code plugins leveraging stochastic agent behavior. "Agents, uhh, find a way."

## Installation

Add this marketplace to your Claude Code:

```bash
# CLI
claude plugins marketplace add whfreelove/chaos-theory

# In-session
/plugins marketplace add whfreelove/chaos-theory
```

Then install a plugin:

```bash
# CLI
claude plugins install tokamak

# In-session
/plugins install tokamak
```

## Available Plugins

### tokamak

OpenSpec artifact validation using parallel critics. Provides skills for writing functional specs, technical designs, requirements (MDG format), and Y-statement decisions.

**Skills included:**
- `tokamak:writing-functional-specs` - Functional specification writing
- `tokamak:writing-technical-design` - Technical design documents
- `tokamak:writing-markdown-gherkin` - MDG (Markdown-Gherkin) requirements
- `tokamak:writing-y-statements` - Y-statement decision format
- `tokamak:critique-specs` - Parallel critic validation
- `tokamak:resolve-gaps` - Gap resolution workflow

### worktree-isolation

Restricts Claude Code to git worktree or Jujutsu workspace boundaries. Prevents access to project root or sibling worktrees.

## Updating

```bash
# CLI
claude plugins marketplace update

# In-session
/plugins marketplace update
```

## Developing Plugins

See `plugins/tokamak/` for a full-featured reference implementation with skills, hooks, and OpenSpec schemas.

For hook types, input/output formats, and publishing: [Claude Code Hooks Documentation](https://docs.anthropic.com/en/docs/claude-code/hooks)

## License

MIT
