## Why

Plan mode output quality is inconsistent. Analysis of 24 existing plan files showed agents skip Context/Why sections (33% compliance), omit references to existing code (13% compliance), and sometimes exit plan mode with unresolved questions. The plan mode system prompt requests structure but cannot enforce it — agents comply probabilistically with natural language instructions.

The previous rodin design (v1) used a skill + programmatic hooks architecture: a `/rodin:plan-gate` skill orchestrated adversarial gap analysis, a PostToolUse hook on Write/Edit maintained embedded metadata, and a PreToolUse hook on ExitPlanMode enforced the assessment verdict. This approach validated plans against their own internal consistency but could not check whether the plan accurately captured what happened in the conversation that produced it.

## What changes

### Hook: `PostToolUse` on EnterPlanMode — template injection

When the agent enters plan mode, this hook injects a prescribed implementation structure into the plan file:

```markdown
## Context
[Why this work is needed]

## Decisions
[Choices made and rationale]

## Files
[Paths to modify/create]

## Tasks
- [ ] Task 1
- [ ] Task 2

## Verification
[How to confirm success]
```

Five required sections. The template establishes expectations that the exit review will enforce. Agents that follow the template produce structurally complete plans; agents that deviate still face the exit review.

### Hook: `PreToolUse` agent hook on ExitPlanMode — conversation-aware review

A single agent hook that acts as both classifier and reviewer. When the agent attempts to exit plan mode, this hook:

1. **Locates the plan file** (mechanism TBD — see research questions)
2. **Classifies the plan** as implementation or non-implementation
3. **Reviews the plan against the conversation**, checking:
   - Does the Context section reflect the problem the user actually stated?
   - Were decisions discussed in conversation captured in the Decisions section?
   - Were questions raised during the conversation resolved, or do unresolved questions remain?
   - Do the Tasks cover what the plan's approach describes?
4. **Allows or denies** ExitPlanMode with specific, grounded feedback

This shifts from **linting the plan file** (checking headings exist) to **reviewing the plan against its source conversation** (checking fidelity). The agent hook can catch "shallow compliance" — a plan with `## Context` that says "This plan implements X" passes structural checks but fails a review that asks "does this reflect the user's stated problem?"

### Marker: non-implementation bypass

Not all plans are implementation plans. Design documents, explorations, and research notes use plan mode but don't need the full five-section structure. A marker mechanism (passphrase or comment) signals that a plan is non-implementation, and the agent hook classifies accordingly:

- **Implementation plans**: All five sections required, semantic review applied
- **Non-implementation plans**: Only Context and Verification required, lighter review

The agent hook handles classification — it reads the plan, sees or doesn't see the marker, and applies the appropriate checks. No inter-hook communication needed.

## Capabilities

### New capabilities

- `plan-template-injection`: PostToolUse on EnterPlanMode injects prescribed structure (Context, Decisions, Files, Tasks, Verification) into the plan file. Establishes the structural expectations that the exit review enforces.

- `plan-exit-review`: PreToolUse agent hook on ExitPlanMode reviews the plan against the conversation — checks that discussed problems appear in Context, that decisions from conversation are captured, that questions were resolved. Uses tool access to read the plan file and model reasoning to evaluate semantic fidelity.

- `non-implementation-bypass`: Marker mechanism allowing non-implementation plans (design docs, explorations) to bypass strict implementation structure. Classified by the agent hook itself — no separate programmatic check needed.

### Modified capabilities

(none — this is a fresh design replacing rodin v1)

## Design decisions

### Single agent hook over two-hook split

The conversation considered two architectures:

| Approach | Pros | Cons |
|----------|------|------|
| Two hooks (programmatic + agent) | Fast structural fail; separation of concerns | More code; inter-hook coordination for marker |
| Single agent hook | Classification + structure + semantics in one pass; no coordination; marker logic self-contained | Slower on every ExitPlanMode attempt; agent cost per invocation |

**Decision**: Single agent hook. The marker/bypass mechanism works more cleanly when one hook handles classification and review together. Inter-hook communication for marker state was an unsolved coordination problem.

### Agent review over structural linting

Structural linting (regex for headings) is deterministic but can't evaluate content quality. An agent hook with a structured checklist prompt achieves ~99% reliability on structural checks while also handling:

- Heading variants (`## Problem` accepted as equivalent to `## Context`)
- Content quality (distinguishing meaningful Context from placeholder text)
- Conversation fidelity (checking plan against what was actually discussed)

The agent hook prompt uses explicit variant lists and checklist structure to constrain evaluation, reducing model variance.

### Conversation review over plan-internal consistency

The v1 design validated plans against themselves (do documented gaps cover critic findings?). The v2 design validates plans against their source conversation:

| v1 (internal consistency) | v2 (conversation fidelity) |
|---------------------------|---------------------------|
| Does `## Context` exist? | Does Context reflect the user's stated problem? |
| Are there TBD markers? | Were questions from conversation resolved? |
| Does `## Decisions` exist? | Were choices discussed in conversation captured? |
| Does `## Tasks` contain a list? | Do tasks cover what the approach describes? |

Agent hooks with conversation access make this possible. This eliminates the shallow compliance problem where agents write structurally valid but semantically empty plans.

## Outstanding research questions

These must be answered before the design can be finalized and implemented:

1. **What data does PostToolUse receive from EnterPlanMode?**
   Does the hook result include the plan file path? The plan file path appears in the system prompt injection, but it's unclear whether PostToolUse can access it from the tool result.

2. **What data does PreToolUse receive for ExitPlanMode?**
   ExitPlanMode has only optional parameters (`allowedPrompts`, `pushToRemote`). Does the hook receive session ID? Can it infer the plan file location?

3. **Can agent hooks access conversation history?**
   The conversation-aware review design depends on the agent hook being able to check what was discussed. If agent hooks only see the tool input, the "review against conversation" capability is impossible and the design falls back to structural linting with semantic evaluation of the plan file alone.

4. **What model options are available for prompt/agent hooks?**
   Early design assumed Haiku-only for prompt hooks, which made classification unreliable. Confirmation that Sonnet is available changes the reliability calculus. What models can agent hooks use?

5. **How do multiple PreToolUse hooks on the same tool interact?**
   If other plugins also hook ExitPlanMode, do all hooks run? Does the first denial stop execution? This affects whether rodin can coexist with other plan-mode plugins.

6. **How does the agent hook locate the plan file?**
   Options explored:
   - Most recently modified file in `~/.claude/plans/` (simple, breaks with concurrent sessions)
   - Breadcrumb from PostToolUse on EnterPlanMode (robust, requires temp file)
   - Session context from hook input (depends on what data hooks receive)

## Impact

- New plugin at `plugins/rodin/` with hooks
- PostToolUse on EnterPlanMode injects template — low risk, additive
- PreToolUse agent hook on ExitPlanMode gates exit — high impact, blocks workflow if misconfigured
- Non-implementation marker provides escape hatch for plans that shouldn't be gated
- All review happens at ExitPlanMode — no mid-planning interruptions
