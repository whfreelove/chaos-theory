---
name: compressing-yadr
description: Use when compressing a YAML ADR into Y-Statement format. Use when creating a minimal-context summary of an architectural decision for agent search and retrieval.
---

## Purpose

Compress a single YAML ADR into Y-Statement format (~50 words) for minimal-context indexing. Preserves the decision essence while enabling quick agent scanning.

## Compression Workflow

### Step 1: Extract Core Fields

From the YAML ADR, extract:

| Field | Extract |
|-------|---------|
| `id` | ADR identifier |
| `context` | Problem statement (condense to ~10 words) |
| `decision_drivers` | Primary driver only |
| `decision_outcome.chosen_option` | The chosen approach |
| `considered_options` | List not-chosen options |
| `consequences.good` | Primary benefit (condense) |
| `consequences.bad` | Primary trade-off (condense) |

### Step 2: Compose Y-Statement

```
{id}:
  - In the context of {context},
  - facing {primary_driver},
  - we decided {chosen_option}
  - and neglected {other_options},
  - to achieve {primary_benefit},
  - accepting {primary_tradeoff}.
```

### Step 3: Verify Completeness

Check all 6 parts are present:
- [ ] Context identifies the component/feature
- [ ] Facing states the quality concern
- [ ] Decided names the chosen approach
- [ ] Neglected lists at least one alternative
- [ ] Achieve states the benefit
- [ ] Accepting states the trade-off

## Compression Guidelines

### Target Length

| Part | Target Length |
|------|---------------|
| context | 5-10 words |
| facing | 5-15 words |
| decided | 3-10 words |
| neglected | 3-15 words (comma-separated list) |
| achieve | 5-10 words |
| accepting | 5-15 words |

**Total Y-Statement: 30-75 words**

### Preserve Decision Essence

When condensing:
- Keep specific technology/pattern names
- Keep quantitative thresholds (e.g., "200ms SLA")
- Drop implementation details
- Drop stakeholder names
- Drop evidence/links (available in full ADR)

### Handle Multiple Drivers

If ADR has multiple `decision_drivers`, pick the primary one. The "facing" clause should capture the dominant concern.

### Handle Missing Fields

Fail closed. Tell the user that any missing required fields must be remedied.

## Example

**Input YAML ADR:**
```yaml
- id: 3
  status: accepted
  date_updated: 2024-03-15
  title: Redis caching for API responses
  context: >-
    API response times exceed 500ms under load.
    How can we reduce latency while maintaining consistency?
  decision_drivers:
    response-time: API must respond within 200ms for p95
    operational-cost: Minimize infrastructure overhead
  considered_options:
    redis-cache: Redis with 5-minute TTL
    in-memory: Application-level LRU cache
    cdn: CDN edge caching
  decision_outcome:
    chosen_option: redis-cache
    consequences:
      good:
        - Sub-50ms response for cached queries
        - Shared cache across instances
      bad:
        - Cache invalidation complexity
        - Redis as additional dependency
```

**Output Y-Statement:**
```markdown

3:
  - In the context of API performance under load,
  - facing the need for sub-200ms p95 response times,
  - we decided on Redis cache with 5-minute TTL
  - and neglected in-memory LRU cache and CDN edge caching,
  - to achieve sub-50ms cached responses with shared state,
  - accepting cache invalidation complexity and Redis dependency.
```

## Agent Guidelines

1. **Preserve searchability** — Include key technical terms (technology names, pattern names, component names).
2. **Link back to source** — Always include ADR ID so the full record can be loaded when needed.
3. **Flag incomplete ADRs** — If missing required fields, fail immediately: "incomplete: missing trade-offs"
