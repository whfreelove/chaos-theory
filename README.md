# Chaos Theory Plugin Marketplace

Claude Code plugins leveraging stochastic agent behavior. "Agents, uhh, find a way."

## Installation

```bash
claude plugins marketplace add whfreelove/chaos-theory
```

If you prefer installing plugins from Claude Code TUI:

```
/plugins marketplace add whfreelove/chaos-theory
/plugins install tokamak
/exit
claude --continue
/init-schemas
```

## Available Plugins

### tokamak

Turn thrashing agentic work plasma into forward motion.

An OpenSpec-centered, iterative specification improvement workflow.
Agents push you to understand your design through repeated rounds of finding gaps, clarifying your solutions, documenting your decisions, then updating specifications.

```bash
claude plugins install tokamak && claude /init-schemas

/critique-specs
/resolve-gaps
```

**Primary Skills:**

- `tokamak:critique-specs` - parallel critics find and document gaps in specifications
- `tokamak:resolve-gaps` - agents help resolve gaps and update specifications

Also provides skills for writing functional specs, requirements, technical design documents, and architecture decision records.

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
