---
name: verification-before-completion
description: Run verification commands before claiming work is complete or fixed. Use before asserting any task is done, bug is fixed, tests pass, or feature works.
---

# Verification Before Completion

**Core Principle:** No completion claims without fresh verification evidence.

## The Verification Gate

BEFORE any claim of success, completion, or satisfaction — execute the task list. Each task must complete in order before proceeding to the next.

## When This Applies

ALWAYS before:

- Claiming "tests pass", "build succeeds", "linter clean", "bug fixed"
- Expressing satisfaction ("Great!", "Done!", "Perfect!")
- Using qualifiers ("should work", "probably fixed", "seems to")
- Committing, creating PRs, marking tasks complete
- Moving to next task or delegating work
- ANY statement implying success or completion

## Red Flags

Stop and verify if you're about to:

- Use hedging language ("should", "probably", "seems to")
- Express satisfaction before running verification
- Trust agent/tool success reports without independent verification
- Rely on partial checks or previous runs
- Think "just this once" or "I'm confident it works"

## Evidence Requirements

| Claim                 | Required Evidence                | Not Sufficient                |
| --------------------- | -------------------------------- | ----------------------------- |
| Tests pass            | `yarn test` output: 0 failures   | Previous run, "looks correct" |
| Build succeeds        | Build command: exit 0            | Linter clean, "should work"   |
| Bug fixed             | Test reproducing bug: now passes | Code changed, assumed fix     |
| Linter clean          | Linter output: 0 errors          | Partial check, spot test      |
| Regression test works | Red→Green cycle verified         | Test passes once              |
| Agent task complete   | VCS diff shows expected changes  | Agent reports "success"       |

## Key Examples

**Regression test (TDD Red-Green):**

```
✅ Write test → Run (fail) → Fix code → Run (pass) → Revert fix → Run (MUST fail) → Restore → Run (pass)
❌ "I've written a regression test" (without verifying red-green cycle)
```

**Build vs Linter:**

```
✅ Run `npm run build` → See "exit 0" → Claim "build passes"
❌ Run linter → Claim "build will pass" (linter ≠ compiler)
```

**Agent delegation:**

```
✅ Agent reports success → Check `git diff` → Verify changes → Report actual state
❌ Trust agent's success message without verification
```
