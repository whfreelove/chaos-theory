---
name: managing-spec-gaps
description: Principles for gap lifecycle management during spec critique and resolution. Use when creating, categorizing, resolving, or cleaning up gaps in gaps.md and resolved.md.
---

## Purpose

Gap artifacts (`gaps.md`, `resolved.md`) track concerns surfaced during spec critique. This skill defines lifecycle principles governing how gaps are created, triaged, resolved, and cleaned up. See gap templates for field structure; see orchestration skills (`critique-specs`, `resolve-gaps`) for workflow procedures.

## Triage Semantics

| Triage | Who Decides | When to Use |
|--------|-------------|-------------|
| **check-in** | User (via AskUserQuestion) | Concern requires human judgment on approach |
| **delegate** | Agent autonomously | Clear solution space; agent picks best option |
| **defer-release** | User confirms | Valid concern, but acceptable to ship without addressing |
| **defer-resolution** | User confirms | Blocks release conceptually, but resolution deferred to future round |

### Selection Guidance

Triage authority and available actions are **configurable per-change** via `.triage-policy.json` in the change directory. The policy determines who decides (user or agent) and which actions are available for each severity level.

**Bundled profiles** (set via `resolve_triage_policy.py --init <profile>`):

| Profile | HIGH | MEDIUM | LOW | Intent |
|---------|------|--------|-----|--------|
| **default** | user: check-in, defer-resolution | user: all 4 options | agent: check-in, delegate, defer-release | Safe starting point for most changes |
| **conservative** | user: check-in | user: check-in, defer-release | user: check-in, delegate, defer-release | All user oversight — greenfield design phases |
| **confident** | user: check-in, delegate, defer-resolution | agent: check-in, delegate, defer-release | agent: delegate, defer-release | Stable codebase with decision history |
| **autonomous** | agent: delegate, defer-release | agent: delegate, defer-release | agent: delegate, defer-release | Fully agent-driven — trusted automation |

**Custom policies**: Edit `.triage-policy.json` directly with the same schema — each severity level has `authority` (`"user"` or `"agent"`) and `actions` (array of valid triage values).

When the policy gives a severity level a **single action**, apply it directly without asking. When **multiple actions** are available, the authority decides: user via AskUserQuestion, or agent autonomously.

## Status Semantics

| Status | Who Decides | When to Use |
|--------|-------------|-------------|
| **resolved** | Agent or user | Gap addressed through decision and artifact changes |
| **superseded** | Agent or user | Another gap now covers this concern more completely |
| **deprecated** | Agent or user | Concern is no longer relevant — scope removed, assumption invalidated, or context changed |

Status is set when a gap moves from `gaps.md` to `resolved.md`. Triage is preserved.

## Gap Creation Quality

- **Reference by location, not quotes**: Cite spec sections by heading slug or structural location (e.g., "Functional § Session Management"). Spec text is volatile across critique rounds; quoted text becomes stale.
- **One concern per gap**: A gap that combines multiple concerns becomes hard to categorize, resolve, and track. Split compound concerns into separate gaps.
- **Source attribution**: Each gap records a `Source` field identifying origin. All values use kebab-case with a type suffix. Critic sources use `-critic` suffix (e.g., `functional-critic`, `coverage-critic`, `architecture-accuracy-critic`, `design-for-test-critic`). Detection method sources use `-detection` suffix (e.g., `implicit-detection`, `stale-detection`, `supersession-detection`, `defer-release-coverage-detection`). The suffix makes origin type self-documenting. This enables audit of critic effectiveness and prompt optimization.

## Evergreen Writing

Gap descriptions and outcomes must remain valid as specs evolve. Avoid coupling to volatile identifiers.

- **No hard-coded counts**: Don't write "The requirements define 55 scenarios" — the number changes. Describe coverage qualitatively ("The requirements define scenarios covering...").
- **No brittle scenario references in descriptions**: Don't write "workflow-intake:3.5 specifies fallback behavior." Write "The intake fallback scenario specifies fallback behavior." Reference behavior, not numbering.
- **Scenario IDs are acceptable in Decision and Outcome fields**: These fields record point-in-time decisions and are immutable history. Writing "Added workflow-validation:2.9" in a Decision is fine — it documents what happened at that moment. Descriptions are different because they frame the concern and should remain readable regardless of renumbering.
- **No inline resolution annotations in descriptions**: Don't append `[Resolved: ...]` to Description fields. Use the `Outcome` field instead.

## Supersession & Deprecation Rules

- **Superseded is a status**, not an informal annotation. Superseded gaps move to `resolved.md` with `Status: superseded`.
- **`Superseded by` points to immediate successor(s)**: If GAP-10 supersedes GAP-3, record `Superseded by: GAP-10` on GAP-3. If GAP-10 later gets superseded by GAP-25, GAP-3 still points to GAP-10.
- **`Current approach` provides the up-to-date pointer**: When a supersession chain exists, `Current approach` on earlier gaps points to the latest active gap or resolution, giving readers a fast path to current thinking.
- **Don't flatten chains**: Preserving the chain (GAP-3 → GAP-10 → GAP-25) maintains decision history. Rewriting GAP-3 to point directly to GAP-25 loses the intermediate reasoning.
- **Deprecated is for concerns that lose relevance**, not concerns that get replaced. If a replacement exists, use `superseded`.
- **Higher evidence bar than superseded**: Rationale must cite specific evidence — the artifact change, code evidence, or round-over-round context shift that makes the concern irrelevant. Bare assertions like "no longer relevant" are insufficient.
- **No replacement pointer needed**: Unlike superseded, deprecated gaps don't require `Superseded by` or `Current approach`.
- **Deprecated gaps move to `resolved.md`** with `Status: deprecated`.

## Resolution Completeness

- **Decision text is immutable history**: Once a Decision is recorded on a gap, it represents the reasoning at that point. Corrections or updates create new gaps or supersessions rather than editing past Decisions.
- **Co-resolved gaps use bidirectional refs**: When resolving one gap also addresses another, both gap entries reference each other so future readers can trace the connection.
- **Defer-release requires artifact coverage**: Before moving a defer-release gap to `resolved.md`, verify its concern is explicitly acknowledged in spec artifacts (Out of Scope, Known Risks, or Decisions sections). Undocumented deferrals create invisible technical debt.
- **Outcome records what changed**: When a resolution modifies artifacts, record what actually changed in the `Outcome` field on the resolved gap entry. Descriptions stay as the original concern; Outcome captures the result.

## Cleanup Guidance

- **Skip cleanup when recent critique found zero new gaps**: If the latest critique round surfaced no new concerns, cleanup is unlikely to find meaningful issues. Avoid generating noise.
- **Stale detection focuses on active gaps**: Compare `gaps.md` entries against current spec text. Resolved gaps in `resolved.md` may reference old spec versions — that's expected historical context, not staleness.
- **Implicit gap detection looks for uncertainty language**: Words like "likely," "appears to," "probably," "TBD," and "TODO" in spec artifacts signal undocumented concerns that should be explicit gaps.

## Agent Guidelines

1. **Read this skill before creating or resolving gaps** — it provides the shared principles that orchestration skills reference.
2. **Don't duplicate template fields** — gap field structure lives in the `gaps.md` and `resolved.md` templates. This skill defines when and why to use them, not what they are.
3. **Don't duplicate orchestration procedures** — workflow steps live in `critique-specs` and `resolve-gaps` skills. This skill defines principles those procedures should follow.
