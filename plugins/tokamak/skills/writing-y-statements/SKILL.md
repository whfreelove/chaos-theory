---
name: writing-y-statements
description: Use when documenting low-overhead decisions during feature development. Use when a full ADR is overkill but the decision still needs to be recorded. Use when capturing quick design choices in code comments, PR descriptions, or lightweight decision logs.
---

## Purpose

Y-Statements are a lightweight decision documentation format—ADR-lite for tactical decisions. Record the decision, alternatives, and trade-offs in a single structured sentence without the overhead of a full ADR.

## When to Use Y-Statements

| Situation | Use Y-Statement | Use Full ADR |
|-----------|-----------------|--------------|
| Local implementation choice | ✓ | |
| API design within a service | ✓ | |
| Library/framework selection | | ✓ |
| Cross-cutting architecture | | ✓ |
| Quick trade-off during coding | ✓ | |
| Stakeholder-visible decision | | ✓ |

**Rule of thumb**: If the decision affects only this PR/feature and can be reversed easily, use a Y-Statement. If it's architecturally significant (ASR criteria), use a full ADR.

## Y-Statement Structure

A Y-Statement has 6 parts in a single sentence:

```
In the context of <use case/component>,
facing <non-functional concern>,
we decided <chosen option>
and neglected <alternatives>,
to achieve <quality/benefit>,
accepting <consequences/trade-offs>.
```

### Part Breakdown

| Part | Purpose | Maps to ADR Field |
|------|---------|-------------------|
| **context** | What feature/component | `context` |
| **facing** | The quality concern driving the decision | `decision_drivers` |
| **decided** | The chosen approach | `decision_outcome.chosen_option` |
| **neglected** | Alternatives not chosen | `considered_options` |
| **achieve** | Benefits gained | `consequences.good` |
| **accepting** | Trade-offs accepted | `consequences.bad` |

## Examples

### Example 1: Session State Pattern

```
In the context of the web shop service,
facing the need to keep user session data consistent and current across shop instances,
we decided on the Database Session State Pattern
and neglected Client Session State or Server Session State,
to achieve cloud elasticity,
accepting that a session database needs to be designed, implemented, and replicated.
```

### Example 2: Validation Strategy

```
In the context of the user registration form,
facing the need for immediate feedback on input errors,
we decided on client-side validation with server-side verification
and neglected server-only validation,
to achieve responsive UX,
accepting duplicated validation logic between frontend and backend.
```

### Example 3: Caching Approach

```
In the context of the product catalog API,
facing high read volume with infrequent updates,
we decided on Redis cache with 5-minute TTL
and neglected in-memory cache or no caching,
to achieve sub-100ms response times,
accepting cache invalidation complexity and eventual consistency.
```

### Example 4: Error Handling

```
In the context of the payment processing module,
facing the need for detailed debugging without exposing internals,
we decided on structured error codes with internal logging
and neglected verbose client errors or generic messages only,
to achieve debuggability with security,
accepting the maintenance cost of error code documentation.
```

## Writing Guidelines

### Be Specific in Each Part

| Part | Weak | Strong |
|------|------|--------|
| context | "the app" | "the checkout flow" |
| facing | "performance" | "p95 latency under 200ms for cached queries" |
| decided | "use caching" | "Redis cache with write-through invalidation" |
| neglected | "other options" | "in-memory LRU cache, CDN edge caching" |
| achieve | "better performance" | "sub-50ms response for repeated queries" |
| accepting | "some complexity" | "Redis infrastructure and cache coherence logic" |

### Neglected Alternatives Matter

Always list at least one neglected alternative. This proves:
- Other options were considered
- The decision was deliberate, not default
- Future readers understand why not

**Bad**: "and neglected nothing" or omitting this part
**Good**: "and neglected [specific alternatives]"

### Honest Trade-offs

The "accepting" clause prevents the Fairy Tale anti-pattern. Every decision has costs—name them explicitly.

**Bad**: "accepting minimal overhead"
**Good**: "accepting additional deployment complexity and monitoring requirements"

## Where to Place Y-Statements

### In Code Comments

```python
# Y-Statement: In the context of rate limiting,
# facing the need for distributed request counting,
# we decided on Redis INCR with TTL
# and neglected in-memory counters or database tracking,
# to achieve accurate limits across instances,
# accepting Redis as a required dependency.

class RateLimiter:
    ...
```

### In PR Descriptions

```markdown
## Design Decisions

**Pagination approach**: In the context of the user list API,
facing large datasets (100k+ users),
we decided on cursor-based pagination
and neglected offset pagination or keyset pagination,
to achieve consistent performance regardless of page depth,
accepting slightly more complex client implementation.
```

### In Decision Logs

For projects tracking decisions in a file:

```markdown
# decisions.md

## 2024-03-15: API Versioning

In the context of the public API,
facing the need to evolve endpoints without breaking clients,
we decided on URL path versioning (/v1/, /v2/)
and neglected header versioning or query parameter versioning,
to achieve explicit version visibility and easy routing,
accepting URL proliferation and potential client confusion during transitions.
```

## Converting Y-Statements to ADRs

If a Y-Statement decision becomes architecturally significant, promote it to a full ADR:

1. Create ADR with `status: accepted`
2. Expand each Y-Statement part into the corresponding ADR field
3. Add stakeholders, evidence, and confirmation criteria
4. Link back to original Y-Statement location

## Agent Guidelines

1. **Suggest Y-Statements proactively** — When making implementation decisions during feature work, offer to document them as Y-Statements.
2. **Keep it single-sentence** — A Y-Statement should be readable in one breath. If it needs multiple paragraphs, consider a full ADR.
3. **Preserve the structure** — All 6 parts are required. Missing parts indicate incomplete thinking.
4. **Match formality to context** — Code comments can be terse; PR descriptions should be more complete.

## Quick Template

Copy and fill in:

```
In the context of [feature/component],
facing [quality concern or constraint],
we decided [chosen approach]
and neglected [alternative 1, alternative 2],
to achieve [benefit/quality],
accepting [trade-off/consequence].
```
