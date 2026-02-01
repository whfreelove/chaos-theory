---
name: writing-technical-design
description: Use when creating technical design documents, architecture documentation, or implementation specifications. Use when documenting technical decisions and component responsibilities.
---

## Purpose

Technical design documents bridge functional requirements and implementation. They answer HOW, not WHAT or WHY. A good technical design enables any competent engineer to implement the feature correctly without further clarification.

## Detail Balance

Technical designs enable task assignment. The right detail level lets a team lead direct work without follow-up questions while leaving implementation choices to developers.

### The Assignment Test

Before including a detail, ask: **Would a team lead need this to assign the task?**

| Question | If YES | If NO |
|----------|--------|-------|
| Would removing this cause ambiguity or rework? | Include | Omit |
| Does this lock in an implementation choice? | Omit (or justify in Decisions) | Include |
| Will this need updating when code changes? | Omit | Include |

### What to Include vs Omit

| Include (assignment context) | Omit (developer decisions) |
|------------------------------|---------------------------|
| Component purpose and responsibilities | Internal class/module structure |
| External dependencies and why | How to use those dependencies |
| Contract shapes at boundaries | Data transformations inside |
| Error categories (4xx vs 5xx) | Specific error message text |
| Performance targets (p95 < 200ms) | How to achieve the target |
| What scenarios need testing | How to write the tests |

### Quick Examples

**Over-specified:** "Use sliding window with 1-second buckets, store in Redis with INCR+EXPIRE"
— Locks in algorithm and Redis commands; developer can't choose alternatives

**Under-specified:** "Limits requests"
— Team lead must ask: Per user? Per endpoint? What storage?

**Right level:** "Enforce per-user limits across instances using Redis, reject with 429, sync within 100ms"
— Assignable task, developer chooses implementation

### What This Doesn't Cover

Technical designs don't replace mentorship. If a junior engineer needs guidance on *how* to implement something, that's pairing and code review—not more detailed docs. The detail level should be consistent regardless of who implements.

## Core Sections

| Section | Purpose | Key Questions Answered |
|---------|---------|------------------------|
| Context | Situate the reader | What exists today? What constraints apply? |
| Objectives | Define success | What measurable outcomes? How will we know it worked? |
| Architecture | Show structure | What components exist? How do they connect? |
| Components | Detail parts | What does each part do? What does it need? |
| Interfaces | Define contracts | How do components communicate? What do they exchange? |
| Unit Testing | Component validation | How do we test components in isolation? |
| Decisions | Record choices | Why this approach? What alternatives were rejected? |
| Risks | Flag concerns | What could go wrong? How do we mitigate? |

## Writing Context

Context establishes the starting point. Include:

- **Background**: What exists today, why we're making changes
- **Tech stack**: Technologies relevant to this change
- **Prior decisions**: Reference existing ADRs or specs if applicable
- **Constraints**: Non-negotiable requirements (security, compliance, performance SLAs)

Keep context factual. Save opinions for Decisions section.

## Writing Objectives

Objectives are SMART-ish: Specific, Measurable, Achievable, Relevant. Time-bound is implied by the change scope.

**Good objectives:**
- Reduce API latency p95 from 500ms to 200ms
- Support batch processing of up to 10,000 records
- Enable SSO integration without modifying existing auth flows

**Bad objectives:**
- Improve performance (not measurable)
- Make the system better (not specific)
- Rewrite the entire backend (not achievable in one change)

### Objective Slugs

Use `OBJ-<kebab-case-name>` for traceability. Example: `OBJ-reduce-latency`.

Format:
```
`OBJ-reduce-latency`: Reduce API latency p95 from 500ms to 200ms
`OBJ-batch-support`: Support batch processing of up to 10,000 records
```

Slugs enable:
- Task references: "Implements OBJ-reduce-latency"
- Test references: "Validates OBJ-reduce-latency"
- Review comments: "Does this satisfy OBJ-reduce-latency?"

## Architecture Diagrams

### Diagram Types

| Type | Use When | Mermaid Syntax |
|------|----------|----------------|
| Flowchart | Component relationships, data flow | `flowchart TD` |
| Sequence | Request/response, process steps | `sequenceDiagram` |
| C4 Context | System-level view | `flowchart TD` with stereotypes |
| State | Lifecycle, status transitions | `stateDiagram-v2` |

### Diff vs New

**When modifying existing architecture:**
1. Reference existing documentation (e.g., project.md) for baseline
2. Show CHANGED components/connections with annotations
3. Use consistent styling: new=green/solid, modified=orange/dashed, unchanged=gray/dotted

**When creating new architecture:**
- Full diagram is appropriate
- Start with high-level, add detail as needed

### Diagram Hygiene

- Keep diagrams focused (5-10 nodes max per diagram)
- Split large systems into multiple diagrams (System Overview + Component Interactions)
- Label relationships, not just nodes
- Include legend for non-obvious styling
- Mermaid preferred over ASCII/text diagrams

## Component Documentation

Each component gets a definition block:

```markdown
`CMP-auth-service`: Authentication Service

- **Description**: Handles user authentication and session management
- **Responsibilities**:
  - Validate credentials against identity provider
  - Issue and refresh JWT tokens
  - Manage session lifecycle
- **Dependencies**:
  - `CMP-user-store` (required)
  - Redis for session cache (required)
  - LDAP connector (optional, for enterprise SSO)
```

### Component Slugs

Use `CMP-<kebab-case-name>` for traceability. Example: `CMP-rate-limiter`.

### Responsibility Guidelines

- Use active verbs: "validates input", "routes requests", "caches responses"
- Keep responsibilities cohesive (single responsibility principle)
- If responsibilities seem unrelated, consider splitting the component

### Dependency Guidelines

- List both internal (`CMP-*`) and external dependencies
- Note if dependency is optional vs required
- Flag circular dependencies as design smells

## Interface Documentation

The Interfaces section is OPTIONAL. Use it when components expose contracts that other components or external systems consume.

### When to Include Interfaces

| Include | Skip |
|---------|------|
| Public APIs | Internal helper functions |
| Cross-component communication | Single-component internals |
| External integrations | Implementation details |

### Interface Slugs

Use `INT-<kebab-case-name>` for traceability. Example: `INT-authenticate-user`.

Slugs enable:
- Task references: "Implements INT-authenticate-user"
- Test references: "Tests INT-authenticate-user error handling"
- Review comments: "Does this satisfy INT-validate-token contract?"

### Interface Format

```markdown
### `CMP-auth-service` Interfaces

`INT-authenticate-user`: Authenticate User
- **Input**: `{ username: string, password: string }`
- **Output**: `{ token: string, expires_at: ISO8601 }`
- **Errors**:
  - `401 InvalidCredentials` - username/password mismatch
  - `429 RateLimited` - too many attempts

`INT-validate-token`: Validate Token
- **Input**: `{ token: string }`
- **Output**: `{ valid: boolean, user_id?: string }`
- **Errors**:
  - `400 MalformedToken` - token format invalid
```

### Data Models Inline

Document data shapes where they appear in inputs/outputs. Don't create a separate Data Models section - keep schemas close to their usage.

For complex shared types, define once and reference:

```markdown
**Types**

`UserSession`:
```json
{
  "user_id": "string",
  "token": "string",
  "expires_at": "ISO8601",
  "permissions": ["string"]
}
```
```

### Interface Guidelines

- Document inputs, outputs, AND errors (errors are often forgotten)
- Use concrete types, not "object" or "any"
- Include error codes/names that consuming code can handle
- Keep interfaces at contract level, not implementation

## Unit Testing Strategy

The Unit Testing section is OPTIONAL but recommended for components with complex logic.

### Testing Scope

Unit testing documents **code-level validation**. System-level testing (integration, E2E) belongs in infra.md.

| Testing Type | Where Documented |
|--------------|------------------|
| Unit tests | technical.md |
| Integration tests | infra.md |
| E2E tests | infra.md |

### What to Document

For each component with non-trivial logic:

```markdown
### `CMP-rate-limiter` Testing

- **Approach**: In-memory Redis mock for fast tests
- **Key scenarios**: Window rollover, burst handling, distributed sync
- **Mocking strategy**: Mock time provider, fake Redis client
```

### Guidelines

- Focus on testing approach, not test implementation details
- Document mocking strategy for external dependencies
- Reference which `@slug:Y.Z` requirements each component test covers

## Decision Documentation

Technical designs use **Y-statements** for decisions. This is a lightweight format that captures the essential information without ADR overhead.

Invoke skill `ct:writing-y-statements` for full Y-statement reference.

### Quick Y-Statement Template

```
In the context of <component/feature>,
facing <quality concern>,
we decided <chosen approach>
and neglected <alternative 1, alternative 2>,
to achieve <benefit>,
accepting <trade-off>.
```

### Example

```
In the context of the rate limiting component,
facing the need for distributed request counting,
we decided on Redis INCR with TTL
and neglected in-memory counters or database tracking,
to achieve accurate limits across instances,
accepting Redis as a required dependency.
```

### When Y-Statements Are Required

Both directions need justification:

- **Adding external dependency**: Document why it's worth the vendor risk, maintenance burden, and API stability concerns
- **Building internally**: Document why external alternatives were rejected (avoid NIH syndrome)

If the solution is complex and viable alternatives exist, document the choice.

### Decision Lifecycle in Technical Designs

| Status | Where it belongs |
|--------|------------------|
| Proposed | NOT in technical.md - decisions need approval first |
| Accepted | In technical.md as Y-statement |
| Superseded | DELETE immediately - don't keep stale decisions |
| Rejected | Not documented (was never accepted) |

This differs from full ADRs which track history. Technical designs are living documents for current implementation, not historical records.

## Risk Documentation

The Risks section is OPTIONAL. Use it for cross-cutting risks not tied to specific decisions.

**Include in Risks section:**
- Migration risks affecting multiple components
- Security concerns spanning the design
- Performance risks without clear mitigation
- External dependency risks (vendor lock-in, API stability)

**Don't include in Risks section:**
- Trade-offs from a specific decision (use Y-statement "accepting" clause)
- Implementation details (those belong in tasks)

### Risk Format

```markdown
## Risks

**Redis single point of failure** → Deploy Redis Sentinel for HA; design graceful degradation if cache unavailable.

**Migration data loss** → Run shadow writes for 2 weeks before cutover; maintain rollback capability.
```

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Mixing WHAT and HOW | Functional spec leakage | Keep requirements in functional.md |
| Objectives without metrics | Unverifiable success | Add measurable criteria |
| Monolithic diagrams | Unreadable, unmaintainable | Split into focused diagrams |
| Responsibilities as implementation | Too detailed, brittle | Stay at interface level |
| Proposed decisions | Unapproved choices in design | Get approval first, then document |
| Missing alternatives | Can't evaluate decision quality | Y-statements require "neglected" clause |
| Trade-offs in Risks section | Duplicates decision content | Keep trade-offs in Y-statement |
| Missing component dependencies | Incomplete picture | List all internal and external deps |
| Missing error contracts | Consumers can't handle failures | Document all error responses |
| Over-specification | Constrains developers, stale quickly | Apply assignment test: would team lead need this? |
| Under-specification | Team lead can't assign work | Include enough context to assign without follow-up |

## Agent Guidelines

1. **Explore before writing** — Read functional.md, requirements/, existing architecture docs before drafting technical design.

2. **Slug everything** — Objectives get `OBJ-*`, components get `CMP-*`, interfaces get `INT-*`. Unit testing strategy references components. E2E testing strategy goes in infra.md.

3. **Diagram first** — For complex changes, sketch architecture diagram before prose. Visual structure reveals gaps in understanding.

4. **Y-statements for decisions** — Invoke `ct:writing-y-statements` skill for the full format. Don't abbreviate or skip parts.

5. **First draft sets structure** — Subsequent agents expand existing sections. Get all appropriate headers in place on first draft to prevent content shoehorning.

6. **Ask about unknowns** — If context is unclear, ASK. Don't invent constraints or assume tech stack choices.

7. **Keep Risks focused** — Only cross-cutting concerns. Decision trade-offs go in Y-statements, not Risks.
