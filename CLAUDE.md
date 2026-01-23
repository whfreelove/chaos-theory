# Chaos-Theory Plugin Marketplace

Claude Code plugins leveraging "stochastic" agent behavior.

## Plugins

```
plugins/
  worktree-isolation/  # Restricts agent to worktree bounds (active)
  rodin/               # ExitPlanMode gate (design phase)
```

Create plugins following `worktree-isolation/` pattern:
- `.claude-plugin/plugin.json` - metadata
- `hooks/hooks.json` - hook definitions
- `scripts/` - validation scripts

## Decision Checkpoints

### 1. TodoWrite framing
When creating todos, use AskUserQuestion to confirm whether they are design decisions or implementation tasks. If they are design decisions (not implementation tasks), use collaborative verbs:
- ❌ "Resolve GAP-X" (implies autonomous action)
- ❌ "Fix the authentication issue"
- ✅ "Propose resolution for GAP-X" (implies presenting options)
- ✅ "Discuss authentication approach"

### 2. Check in before committing
Before updating artifacts with user intent, architectural decisions, or design style, STOP and present:
- The decision being made
- At least 2 alternatives considered
- Your recommendation and why

Triggers requiring check-in:
- Scoping something out of a proposal
- Choosing between technical approaches
- Adding workarounds for missing APIs
- Changing stated goals or problem definitions

### 3. AskUserQuestion for multi-path decisions
When a gap/problem has multiple valid resolutions, use AskUserQuestion to present options rather than picking one. Frame as:
- "Option A: [approach] — [tradeoff]"
- "Option B: [approach] — [tradeoff]"
- "Which direction?"

When the problem could be **definitively** answered with a short 
When you're handling multiple gaps/problems, batch up questions instead of presenting one at a time when possible.

<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->
