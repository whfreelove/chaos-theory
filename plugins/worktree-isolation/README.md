# Worktree Isolation Plugin for Claude Code

Automatically isolate Claude Code to git worktree or jujutsu workspace boundaries, preventing access to project root or sibling worktrees.

I find worktrees amazing to isolate work for orchestrated agents, but policing permission denials when agents would attempt to read or run tests or make changes in the project root, in a completely different state, would stop me too often.

## What It Does

When working in **any git worktree** or **jujutsu workspace**:

- Provides isolation warning at session start with boundaries to agent
- **Blocks file operations** (Read, Write, Edit, etc.) that escape the worktree
- **Validates Bash commands** to prevent parent and absolute path traversal
- **Allows access to `~/.claude/plans/`** for Claude Code plan mode

## Installation

This plugin relies on [`jq`](https://jqlang.org/download) to parse hook JSON.

In Claude Code:

```bash
/plugin install worktree-isolation@your-marketplace
```

Or manually enable in your Claude Code settings.

## How It Works

The plugin uses three hooks:

1. **SessionStart** - Displays isolation warning if in worktree/workspace
2. **PreToolUse (file ops)** - Validates paths for Read, Write, Edit, MultiEdit, Glob, Grep, LS, NotebookEdit, NotebookRead, and Search
3. **PreToolUse (Bash)** - Parses commands to block `..`, absolute paths, and `~/` escapes

### Worktree Detection

Supports both version control systems:

| System | Detection | Worktree Indicator |
|--------|-----------|-------------------|
| **Git** | `.git` is a FILE | Contains `gitdir: /path/to/main/.git/worktrees/name` |
| **Jujutsu** | `.jj/repo` is a FILE | Contains `/path/to/main/.jj/repo` |

Main repositories (where `.git` or `.jj/repo` is a directory) are not isolated.

## What's Blocked

When in a worktree, Claude Code cannot:

| Pattern | Example |
|---------|---------|
| Parent traversal | `../../README.md` |
| Absolute project root | `/path/to/project/file` |
| Tilde paths outside worktree | `~/.bashrc` |
| Bash with `..` | `cd ..`, `cat ../../file` |
| Sibling worktrees | `.worktrees/other/file` |

## What's Allowed

Even in isolation mode, access is permitted to:

| Path | Reason |
|------|--------|
| `~/.claude/plans/*` | Claude Code plan mode files |

## License

MIT
