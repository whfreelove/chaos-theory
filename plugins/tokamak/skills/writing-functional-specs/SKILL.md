---
name: writing-functional-specs
description: Conceptual guidance for writing functional specifications. Use when creating or
reviewing functional.md files.
---

## Core Principle

Functional specifications describe USER BURDEN and USER OUTCOMES, not system mechanics.

**Self-check for every statement:** Would a user who's never seen the code describe their goal this way?

## Framing: Human Burden

State problems in terms of what pain users/developers experience.

| GOOD (human burden) | BAD (implementation gap) |
|---------------------|--------------------------|
| "Manual task creation burns context" | "We need a hook to intercept X" |
| "Users re-explain requirements each time" | "The API is missing endpoint Y" |

## Framing: Actor Outcomes

Group by ACTOR/ROLE, not by feature. Format: `slug`: <actor> can <outcome>

| GOOD (actor-centric with slug) | BAD (feature-centric) |
|--------------------------------|----------------------|
| `workflow-authoring`: Skill authors can ship complete workflows | "FSM Hook: Intercepts skill loading" |
| `task-consistency`: Users see consistent task lists | "TaskList Integration: Creates tasks" |

Each capability should be testable: can you verify an actor achieves the outcome?

## Forbidden Language

These words signal implementation leaking into functional specification:

**Verbs:** implements, uses, supports, calls, invokes, leverages, utilizes
**Nouns:** hook, algorithm, data structure, endpoint, handler, middleware

When you catch yourself using these, reframe around user experience.

## Scope Boundaries

Use **Scope** (what's included), **Out of Scope** (what's deferred), and **Known Risks** to:
- Prevent scope creep during design
- Clarify boundaries for reviewers
- Document future work explicitly
- Surface risks early so reviewers can assess before design begins
