---
name: writing-yaml-adr
description: Use when writing architectural decision records, documenting design choices, or recording technical decisions. Use when editing *.adr.yaml files or adding decisions to an ADR file.
---

## File Extension

ADR files use the `.adr.yaml` extension. For a starter template, see [template.adr.yaml](template.adr.yaml).

## Root Structure

ADR files are bare YAML lists (no root key). Each list item is one decision record.

```yaml
- id: 1
  status: accepted
  title: Use PostgreSQL for persistence
  ...

- id: 2
  status: proposed
  title: Add caching layer
  ...
```

## Required Fields

| Field | Description |
|-------|-------------|
| `id` | Incrementing integer starting from 1, no zero-padding |
| `status` | One of: draft, proposed, accepted, rejected, deprecated, superseded |
| `date_created` | YYYY-MM-DD when first recorded |
| `date_updated` | YYYY-MM-DD when last modified |
| `title` | Short phrase describing problem and solution |
| `owner` | Single person accountable for the decision |
| `context` | Problem statement (2-3 sentences, articulate as question) |
| `decision_drivers` | Map of forces/concerns influencing the decision |
| `considered_options` | Map of approaches evaluated |
| `decision_outcome` | Chosen option with justification and consequences |

## ID Management

- Start from 1, increment by 1
- No zero-padding (use `1`, not `001`)
- Never reuse IDs, even for rejected/superseded decisions

## Status Lifecycle

```
draft → proposed (ready for decision)
proposed → accepted
proposed → rejected
accepted → deprecated
accepted → superseded (set superseded_by to replacement ID)
```

Use `draft` for early-stage exploration before stakeholders are ready to decide. Promote to `proposed` when the decision is ready for formal review.

When changing status to `superseded`, set `superseded_by` to the ID of the replacing ADR.

## When to Create a Draft

Use the **ASR Test** (Architecturally Significant Requirement) to identify decision-worthy issues. Create a draft ADR if ANY criterion scores YES:

| Criterion | Question |
|-----------|----------|
| **Business Impact** | High business value or risk? |
| **Stakeholder Concern** | Important to sponsors, compliance, or key stakeholders? |
| **QoS Deviation** | Runtime qualities (performance, security, reliability) differ from current architecture? |
| **External Dependencies** | Unpredictable, unreliable, or uncontrollable external behavior? |
| **Cross-Cutting** | System-wide impact across multiple components? |
| **First-of-a-Kind** | Novel for the team's experience? |
| **Historical Trouble** | Past project difficulties in similar contexts? |

**Core decisions** requiring early drafts (don't defer):
- Architectural style selection
- Technology stack choices
- Integration approaches
- Regulatory/compliance requirements

Premature drafts are fine—that's what drafts are for. Late drafts are the problem (decisions already made without documentation).

## When to Promote to Proposal

Promote from `draft` to `proposed` when the **START** criteria are met:

- [ ] **S**takeholders identified and available
- [ ] **T**ime has come—problem is both important AND urgent (Most Responsible Moment)
- [ ] **A**lternatives exist—at least 2 options understood with pros/cons
- [ ] **R**equirements clear—context sufficiently analyzed
- [ ] **T**emplate ready—all required fields populated

Do not promote prematurely. A draft can remain in draft status indefinitely until the decision timing is right.

## Stakeholder Fields (RACI-inspired)

| Field | Required | Description |
|-------|----------|-------------|
| `owner` | Yes | Single person ultimately accountable |
| `decision_makers` | No | People who made/approved the decision |
| `consulted` | No | SMEs with two-way communication |
| `informed` | No | Stakeholders notified (one-way) |

## Context Section

- 2-3 sentences describing the situation
- Articulate the problem as a question
- Link to relevant issues, RFCs, or documentation

```yaml
context: >-
  Our API response times exceed 500ms under load.
  How can we reduce latency while maintaining data consistency?
  See issue #423 for performance metrics.
```

## Decision Drivers

Map with kebab-case keys. Each value is a multiline explanation.

```yaml
decision_drivers:
  response-time: >-
    API must respond within 200ms for 95th percentile
    to meet SLA requirements.
  data-consistency: >-
    Financial transactions require strong consistency
    guarantees to prevent data loss.
```

## Considered Options

Map with kebab-case keys. Describe each approach without judgment.

```yaml
considered_options:
  redis-cache: >-
    Add Redis cache layer with 5-minute TTL.
    Requires new infrastructure and cache invalidation logic.
  database-indexes: >-
    Optimize existing queries with targeted indexes.
    No new infrastructure but limited improvement potential.
```

## Decision Outcome

```yaml
decision_outcome:
  chosen_option: redis-cache  # key from considered_options
  justification: >-
    Redis cache provides 10x latency improvement while
    database indexes only achieve 2x. The infrastructure
    cost is justified by the SLA requirements.
  consequences:
    good:
      - Response times under 50ms for cached queries
      - Reduced database load
    bad:
      - Cache invalidation complexity
      - Additional infrastructure to maintain
  confirmation: >-
    Verify p95 latency under 200ms in staging load tests
    before production deployment.
```

## Pros and Cons (Recommended)

Detailed analysis of each option. Reference keys from `considered_options`.

```yaml
pros_and_cons:
  - option: redis-cache
    pros:
      - 10x latency improvement
      - Horizontal scaling support
    cons:
      - Infrastructure complexity
      - Cache invalidation challenges
  - option: database-indexes
    pros:
      - No new infrastructure
      - Simpler deployment
    cons:
      - Limited improvement (2x)
      - May not meet SLA
```

## Confidence Level (Optional)

Disclose uncertainty to aid review. Honest doubt is better than false certainty.

```yaml
confidence: medium  # low | medium | high
confidence_note: >-
  Based on spike results but no production validation yet.
  Team has limited experience with this technology.
```

| Level | When to use |
|-------|-------------|
| `low` | Limited exploration, significant unknowns remain |
| `medium` | Reasonable analysis done, some validation needed |
| `high` | Thorough analysis, production-validated or team expertise |

## Evidence (Optional)

Document validation work that supports the decision—spikes, PoCs, benchmarks, peer reviews.

```yaml
evidence:
  - type: spike
    description: >-
      Built prototype demonstrating 10x latency improvement
      under simulated load conditions.
    link: https://github.com/org/repo/pull/456
  - type: peer-review
    description: >-
      Validated approach with senior engineer who has
      production experience with this technology.
```

Valid evidence types: `spike`, `poc`, `peer-review`, `benchmark`, `production-data`

## Multiline Strings

Use `>-` (folded block scalar) for multiline prose to flow as paragraphs:

```yaml
context: >-
  First line of context.
  Second line continues the thought.

# NOT this:
context: First line. Second line.
```

## Common Mistakes

| Bad | Good | Why |
|-----|------|-----|
| `id: 001` | `id: 1` | No zero-padding |
| `id: "1"` | `id: 1` | ID is integer, not string |
| Root key `decisions:` | Bare list `- id: 1` | No root key needed |
| `status: Accepted` | `status: accepted` | Lowercase status values |
| Missing `superseded_by` when superseded | Set `superseded_by: 3` | Always link to replacement |
| `owner: [Alice, Bob]` | `owner: Alice` | Single owner only |
| `context: "text"` | `context: >-` (multiline) | Use folded block scalar for prose |

## Writing Strong Justifications

The `justification` field is the heart of the ADR. Strong justifications enable future readers to understand *why* a decision was made, not just *what* was decided.

**Strong justifications include:**
- Prior success on similar projects ("We used this approach in Project X with good results")
- Proof-of-concept or spike results ("Spike showed 10x improvement, see PR #456")
- Market availability of skills ("Our team has 3 engineers with Redis experience")
- Quantitative comparisons ("Option A costs $X/month vs Option B at $Y/month")
- Alignment with stated drivers ("This satisfies the 200ms SLA requirement")

**Weak justifications to avoid (anti-patterns):**
- Popularity: "Everyone uses it" / "It's industry standard"
- Tradition: "We've always done it this way"
- Authority without reasoning: "The architect said so"
- No alternatives considered: Choosing the only option evaluated
- Vague benefits: "It's better" / "It's more modern"

A strong justification references the decision drivers and explains why the chosen option satisfies them better than alternatives.

## Anti-Patterns to Avoid

Common ADR anti-patterns that undermine decision quality:

| Anti-Pattern | Description | Fix |
|--------------|-------------|-----|
| **Fairy Tale** | Only lists benefits, no drawbacks | Always populate `consequences.bad` |
| **Sales Pitch** | Marketing language, exaggeration | Use neutral, factual descriptions |
| **Dummy Alternative** | Fake options to favor preferred choice | Include genuinely viable alternatives |
| **Mega-ADR** | Multi-page detailed specification | Keep ADRs focused; split if needed |
| **Tunnel Vision** | Ignores ops/maintenance perspectives | Include operational consequences |
| **Missing Context** | Decision without background | Explain the triggering situation |
| **Premature Decision** | Decided before alternatives explored | Wait for START criteria |
| **Orphan ADR** | No links to related docs/issues | Link context to source materials |

## Agent Guidelines

When AI agents draft or edit ADRs, follow these rules:

1. **Ask, don't assume** — Use `AskUserQuestion` for anything not explicit in linked documentation. Do not infer stakeholder intent, business context, or technical constraints.

2. **Link all references** — Any documentation referenced in context, drivers, or justification must include a link. Unlinked references are not verifiable.

3. **External sources require human approval** — Do NOT independently cite external sources (articles, benchmarks, vendor docs). External sources must be:
   - Provided by the user, OR
   - Explicitly approved by the user before inclusion

4. **Disclose confidence levels** — When drafting, use the optional `confidence` field to indicate certainty. Honest doubt aids review.

5. **Preserve existing content** — When editing an ADR, preserve decisions and rationale unless explicitly asked to change them.

## Validating YAML ADR Files

Use these shell commands to validate ADR file syntax before committing.

**Ruby** (requires Ruby with bundled Psych):

```bash
ruby -ryaml -e "YAML.safe_load(File.read('path/to/file.adr.yaml'), permitted_classes: [Date]); puts 'Valid'"
```

**Python** (requires PyYAML: `pip install pyyaml`):

```bash
python3 -c "import yaml; yaml.safe_load(open('path/to/file.adr.yaml')); print('Valid')"
```

**Notes:**
- Ruby's `safe_load` requires `permitted_classes: [Date]` because ADR files contain date fields
- Both commands exit with code 0 on success, non-zero on parse errors
- For batch validation of multiple files:

```bash
# Ruby - validate all ADR files in directory
for f in *.adr.yaml; do ruby -ryaml -e "YAML.safe_load(File.read('$f'), permitted_classes: [Date])" && echo "$f: valid"; done

# Python - validate all ADR files in directory
for f in *.adr.yaml; do python3 -c "import yaml; yaml.safe_load(open('$f'))" && echo "$f: valid"; done
```
