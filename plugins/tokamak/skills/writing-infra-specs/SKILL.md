---
name: writing-infra-specs
description: Conceptual guidance for writing infrastructure specifications. Use when creating
  or reviewing infra.md files — deployment, testing strategy, observability, and migration.
---

## Core Principle

infra.md describes HOW to deploy, test, and operate a change using EXISTING infrastructure.
It does NOT propose infrastructure changes — those belong in technical.md.

**Self-check for every statement:** Does this describe operations for the current change,
or is it proposing new infrastructure?

## Testing Strategy

The Testing Strategy section carries the most weight in infra.md. It defines HOW requirements
get verified — not WHICH scenarios exist (that's owned by requirements files).

### Coverage Model

Describe coverage at the **capability/Rule level**, not per-scenario:

| GOOD (structural) | BAD (enumerative) |
|--------------------|-------------------|
| "Auth capabilities verified via E2E login flow" | "Scenario @auth:1.1 tested by test_login..." |
| "Each Rule has a corresponding test class" | Table listing every scenario → test mapping |

Per-scenario tables mirror requirements and go stale on any change. Describe the *pattern*
that ensures coverage, not the line items.

### Completeness Checklist

A testing strategy is complete when it answers:

1. **Environments** — Where do tests run? (local, CI, staging)
2. **Tooling** — What test frameworks, named specifically? Vague "appropriate tooling" is a gap.
3. **Data management** — How is test data created, maintained, cleaned up?
4. **Verification commands** — Concrete, runnable commands that prove tests pass.
5. **Coverage mechanism** — How does the project verify requirements are actually tested?

### Test Type Selection

Match test type to what's being verified:

| Requirement type | Test approach |
|-----------------|---------------|
| User workflow (multi-step) | E2E test |
| Component interaction | Integration test |
| Isolated logic/algorithm | Unit test (implementation detail, not spec-level) |
| Cross-capability behavior | Integration scenario (in integration.feature.md) |

infra.md covers integration and E2E strategy. Unit testing is an implementation detail.

## Deployment

When included (optional), describe deployment flow, not topology:

| GOOD (flow) | BAD (topology change) |
|-------------|----------------------|
| "Deploy via existing CI pipeline with feature flag" | "Add new staging environment" |
| Mermaid diagram showing rollout sequence | Mermaid diagram showing new service topology |

## Observability

Only document logging, metrics, and alerts for NEW components in this change.
Not infrastructure-wide observability changes.

## Anti-Patterns

| Pattern | Problem |
|---------|---------|
| "Tests will be added later" | Deferred without commitment |
| Testing strategy references tools not in the stack | Stack mismatch |
| Per-scenario coverage tables | Goes stale, duplicates requirements |
| No verification commands | Can't prove tests pass |
| Proposing new infrastructure | Belongs in technical.md |
| Unit testing details | Implementation concern, not spec-level |
