## Why

Plan mode output quality is inconsistent. Analysis of 24 existing plan files showed agents skip Context/Why sections (33% compliance), omit references to existing code (13% compliance), and sometimes exit plan mode with unresolved questions. The plan mode system prompt requests structure but cannot enforce it — agents comply probabilistically with natural language instructions.

The previous rodin design (v1) used a skill + programmatic hooks architecture: a `/rodin:plan-gate` skill orchestrated adversarial gap analysis, a PostToolUse hook on Write/Edit maintained embedded metadata, and a PreToolUse hook on ExitPlanMode enforced the assessment verdict. This approach validated plans against their own internal consistency but could not check whether the plan accurately captured what happened in the conversation that produced it.

## What changes

### Hook: `PreToolUse` command hook on Write — structure instructions

When the agent writes a plan file (detected by `.claude/plans/` in `tool_input.file_path`), this hook injects structure instructions into the agent's context. The hook does not modify the file — it returns a message reminding the agent of the required sections:

- **Context** — Why this work is needed, in terms of user burden
- **Decisions** — Choices made and rationale, in Y-Statements
- **Files** — Paths to modify and create
- **Tasks** — Ordered implementation steps
- **Verification** — Commands that confirm success

Five required sections. The instructions establish expectations that the exit review will enforce. Agents that follow the structure produce complete plans; agents that deviate still face the exit review. The hook allows the write to proceed (`{continue: true}`) with supplementary context rather than modifying content.

### Hook: `PreToolUse` prompt hook on ExitPlanMode — plan quality review

A prompt hook that receives the full plan text via `$ARGUMENTS` (specifically `tool_input.plan`) and evaluates it. When the agent attempts to exit plan mode, this hook:

1. **Classifies the plan** as implementation or non-implementation
2. **Reviews the plan for structural completeness and content quality**, checking:
   - Does the Context section explain why the work is needed?
   - Are decisions documented with rationale?
   - Do the Tasks cover what the plan's approach describes?
   - Is there a verification strategy?
3. **Allows or denies** ExitPlanMode with specific, grounded feedback

The prompt hook receives the plan inline — no file reading needed. It evaluates using the default model (sonnet) without a configurable `model` field. This provides semantic review beyond structural linting: distinguishing meaningful Context from placeholder text, checking that Tasks align with stated goals, and verifying Decisions include rationale.

**Limitation**: Conversation-aware review is not feasible. `transcript_path` contains no conversation content at hook time, and agent hooks (which could use tools to read files) are non-functional. The review evaluates the plan text in isolation.

### Non-implementation plans

Not all plans are implementation plans. Design documents, explorations, and research notes use plan mode but don't need the full five-section structure. The prompt hook classifies the plan based on content analysis — not markers — and applies appropriate checks:

- **Implementation plans**: All five sections required, semantic review applied
- **Non-implementation plans**: Only Context and Verification required, lighter review

Classification relies on the prompt hook's judgment of the plan's content (does it describe code changes, or is it a design exploration?). No in-band markers are used — the plan text is untrusted input inside the prompt hook's LLM context, so any marker mechanism would be a prompt injection vector.

## Capabilities

### New capabilities

- `plan-structure-instructions`: PreToolUse command hook on Write injects structure instructions into the agent's context when writing to `.claude/plans/`. Establishes the structural expectations that the exit review enforces without modifying the file content.

- `plan-exit-review`: PreToolUse prompt hook on ExitPlanMode reviews the plan text (received inline via `$ARGUMENTS`) for structural completeness and content quality. Uses the default model (sonnet) to evaluate whether sections are meaningful, tasks align with goals, and decisions include rationale.

- `non-implementation-classification`: Prompt hook classifies plans by content analysis. Non-implementation plans (design docs, explorations) receive lighter review without requiring in-band markers. No marker mechanism — plan text is untrusted input in the prompt context.

### Modified capabilities

(none — this is a fresh design replacing rodin v1)

## Design decisions

### Prompt hook over agent hook

Agent hooks (`type: "agent"`) are silently ignored on Claude Code 2.1.45. Prompt hooks (`type: "prompt"`) work reliably for deny/allow decisions and receive the full hook input via `$ARGUMENTS`. The prompt hook receives `tool_input.plan` directly — no tool access needed to read the plan file.

**Decision**: Prompt hook. Agent hooks are non-functional, and the plan text is delivered inline, eliminating the need for file-reading tools.

### Context injection over file modification

The structure instructions hook injects instructions into the agent's context rather than modifying the plan file content. This keeps the hook non-destructive — it reminds the agent of required structure without overwriting what the agent has written.

**Decision**: Context injection via Write hook. The hook returns `{continue: true}` with a supplementary message. The agent sees the structure expectations; the file write proceeds unmodified.

### Prompt review over structural linting

Structural linting (regex for headings) is deterministic but can't evaluate content quality. A prompt hook with a structured checklist achieves reliability on structural checks while also handling:

- Heading variants (`## Problem` accepted as equivalent to `## Context`)
- Content quality (distinguishing meaningful Context from placeholder text)
- Task-goal alignment (checking that tasks cover the stated approach)

The prompt receives the plan inline and uses explicit variant lists and checklist structure to constrain evaluation.

### Plan-text review over conversation-aware review

The v1 design validated plans against themselves. The v2 proposal originally aimed for conversation-aware review, but research showed `transcript_path` has no conversation content at hook time and agent hooks are non-functional. The design now reviews the plan text in isolation:

| Originally proposed | Actual capability |
|---------------------|-------------------|
| Does Context reflect the user's stated problem? | Does Context explain a meaningful problem? |
| Were conversation decisions captured? | Are decisions documented with rationale? |
| Were conversation questions resolved? | Are there unresolved TBD markers? |
| Do tasks cover the discussed approach? | Do tasks align with the plan's own stated goals? |

This is weaker than conversation-aware review but still catches shallow compliance — plans with empty sections, placeholder text, or misaligned tasks.

## Research findings

Empirically tested on Claude Code 2.1.45 (2026-02-18). Evidence in `research/agent-hook-capabilities.ipynb`, `research/plan-mode-data-flow.ipynb`, and `research/hook-interactions.ipynb`.

1. **What data does PostToolUse receive from EnterPlanMode?**
   EnterPlanMode does not fire PreToolUse or PostToolUse hooks at all — 0 events captured across multiple runs. However, the Write tool fires when the agent writes the plan file, and its PreToolUse envelope contains `tool_input.file_path` (with `.claude/plans/` path) and `tool_input.content` (full plan text). `permission_mode=plan` enables filtering. **Write hooks replace EnterPlanMode hooks.**

2. **What data does PreToolUse receive for ExitPlanMode?**
   Full envelope: `session_id`, `transcript_path`, `cwd`, `permission_mode`, `hook_event_name`, `tool_name`, `tool_input`, `tool_use_id`. The `tool_input` contains a single key `plan` with the **complete plan text inline**. No file path lookup needed — the plan is delivered directly to the hook.

3. **Can agent hooks access conversation history?**
   Agent hooks (`type: "agent"`) are **silently ignored** on v2.1.45 — no secondary model appears in `modelUsage`, no denial occurs, no error reported. The feature appears non-functional. Additionally, `transcript_path` exists but contains only 1 line of queue-operation metadata at PreToolUse time — no conversation content. **Conversation-aware review via hooks is not feasible.** The design must fall back to reviewing the plan text alone (delivered via `tool_input.plan`).

4. **What model options are available for prompt/agent hooks?**
   Setting the `model` field on prompt hooks **silently disables them** — hooks with `model: "haiku"` or `model: "sonnet"` do not fire at all, while hooks without a `model` field work correctly. The default prompt hook model appears to be sonnet (observed in `modelUsage` when a prompt hook fires on ExitPlanMode). Agent hooks do not fire regardless of model setting. **Model selection is not available; the default (sonnet) must be used.**

5. **How do multiple PreToolUse hooks on the same tool interact?**
   All hooks run regardless of earlier results — no short-circuiting. Ordering follows array position in `hooks.json`. Any single denial blocks the tool call. Rodin can coexist with other ExitPlanMode hooks.

6. **How does the agent hook locate the plan file?**
   **Not needed.** ExitPlanMode's PreToolUse envelope delivers the full plan text in `tool_input.plan`. No file path lookup, breadcrumb mechanism, or `~/.claude/plans/` scanning required. For template injection, the Write hook receives `tool_input.file_path` with the exact plan file path.

## Design changes required by findings

The research invalidates two proposal assumptions and enables one simplification:

| Proposal assumption | Finding | Required change |
|---------------------|---------|-----------------|
| PostToolUse on EnterPlanMode for template injection | EnterPlanMode doesn't fire hooks | Use PreToolUse on Write, inject structure instructions into context |
| PreToolUse agent hook on ExitPlanMode for review | Agent hooks silently ignored; `model` field breaks prompt hooks | Use `type: "prompt"` hook (no model field) on ExitPlanMode |
| Agent hook reads plan file via tool access | Plan text delivered inline in `tool_input.plan` via `$ARGUMENTS` | No file reading needed; prompt hook receives plan directly |
| Conversation-aware review via transcript | transcript_path has no conversation content at hook time | Review plan text only; conversation fidelity not checkable via hooks |
| Marker mechanism for non-implementation bypass | Plan text is untrusted input in prompt hook context | No in-band markers; classify by content analysis instead |

## Impact

- New plugin at `plugins/rodin/` with hooks
- PreToolUse command hook on Write injects structure instructions into context — low risk, additive, non-destructive
- PreToolUse prompt hook on ExitPlanMode gates exit — high impact, blocks workflow if misconfigured
- Non-implementation classification provides lighter review path without in-band bypass markers
- All review happens at ExitPlanMode — no mid-planning interruptions
