# Chaos-Theory Plugin Marketplace

Claude Code plugins leveraging chaotic agent behavior.

## Plugins

```
plugins/
  finite-skill-machine/  # Auto-populates agent task lists (active)
  tokamak/               # Specification workflow (active)
  worktree-isolation/    # Restricts agent to worktree bounds (active)
  rodin/                 # ExitPlanMode gate (design phase)
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

When the gap/problem could be **definitively** answered with a short feasibility exploration, suggest it as an option.
When you're handling multiple gaps/problems, batch up questions instead of presenting one at a time when possible.

### 4. Check in before adding dependencies
When you see reference to any external tool, library, or runtime dependency, check:
- Does documentation exist to justify why this dependency is needed? If so, continue work
If not, STOP and check in with the user:
- Bring up the dependency and what problem it solves
- Consider at least 2 viable (simple, stable, active, well known) alternatives: feel free to search the web for ideas
- Present the user a choice (and recommend one):
  - The 3 new dependency options
  - Avoid the problem that demands them
  - Solve the problem with complexity in place
  - Build our own dependency
After, suggest a documentation change justifying the choice to prevent future agent confusion

Triggers requiring check-in:
- Any `import`, `require`, or package addition
- Any shell tool assumption (`command -v`, `which`, tool invocation)
- Any runtime requirement (Python, Node, specific shell features)

After approval, document in a Dependencies section with rationale. This creates a record that can be revisited if internal complexity grows too much because of the dependency.

## Parallel Task Launching

When a workflow requires launching multiple Task subagents concurrently (e.g., critics, validators, parallel reviews), ALL Task calls MUST be in a **single message**. Never split them across multiple messages.

- ❌ Launch 2 critics, wait for results, launch 3 more, wait, launch remaining
- ❌ Launch critics in batches of 3-4 across several messages
- ✅ Launch all N critics in one message with N parallel Task tool calls

This applies whenever the workflow says "parallel", "single message", or "all at once". If there are 13 critics, send 13 Task calls in one message. No exceptions.

## OpenSpec Changes

Do not propose OpenSpec changes for implementation work.

## Hook Design

### PreToolUse hooks must use `deny`, not errors
When a PreToolUse hook needs to block an action, return a `deny` response with a reason — not an error. Agents will not interpret error messages as policy; they treat errors as transient failures and retry with variations. A `deny` response is understood as intentional policy and stops retry loops.
