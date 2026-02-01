---
name: reviewing-yaml-adr
description: Use when reviewing proposed ADRs to decide whether to accept, reject, or defer. Use when an ADR has status: proposed and needs a decision.
---

## When to Use This Skill

- ADR has `status: proposed` (not draft)
- Reviewer has authority or delegation to approve decisions
- Decision timing is appropriate (Most Responsible Moment)

## Review Workflow

### Step 1: Verify Readiness

Check that the ADR meets START criteria (Definition of Ready):
- [ ] Status is `proposed` (not `draft`)
- [ ] Stakeholders identified in `owner`/`decision_makers`
- [ ] At least 2 options in `considered_options`
- [ ] Context articulates the problem clearly
- [ ] All required fields populated

If not ready → return to author with specific gaps.

### Step 2: ECADR Checklist (Definition of Done)

| Criterion | Check | Pass? |
|-----------|-------|-------|
| **Evidence** | Does `evidence` or `justification` cite validation work? | |
| **Criteria** | Are `decision_drivers` compared across options in `pros_and_cons`? | |
| **Agreement** | Are `consulted` stakeholders listed? Consensus reached? | |
| **Documentation** | Is `context` linked to source docs? Is `justification` complete? | |
| **Realization** | Does `confirmation` specify how to verify implementation? | |

### Step 3: Content Quality Questions

Answer these 7 questions:

1. **Significance**: Is this architecturally significant? (Check against ASR criteria)
2. **Viability**: Can the chosen option realistically solve the problem?
3. **Drivers**: Are decision drivers complete and non-overlapping?
4. **Prioritization**: If drivers conflict, is priority clear?
5. **Soundness**: Does the justification logically connect drivers → chosen option?
6. **Objectivity**: Are `consequences.bad` populated honestly? (No Fairy Tale)
7. **Actionability**: Is `confirmation` specific enough to verify?

### Step 4: Anti-Pattern Check

Scan for these issues:

| Anti-Pattern | Signal | Found? |
|--------------|--------|--------|
| Fairy Tale | Empty or trivial `consequences.bad` | |
| Sales Pitch | Marketing language, superlatives in justification | |
| Dummy Alternative | Options that are obviously non-viable | |
| Weak Justification | "Everyone does it", "We've always done this" | |
| Missing Links | References without URLs | |
| Low Confidence | `confidence: low` without mitigation plan | |

### Step 5: Make Decision

Based on checklist results:

**ACCEPT** (`status: accepted`) when:
- All ECADR criteria pass
- No blocking anti-patterns
- Justification is sound

**REJECT** (`status: rejected`) when:
- Fundamental flaw in reasoning
- Chosen option cannot solve the stated problem
- Critical stakeholder concerns ignored

**DEFER** (keep `status: proposed`) when:
- Missing evidence that could be gathered
- Stakeholder agreement not yet reached
- Timing not right (too early to decide)

### Step 6: Document Review Outcome

For accept/reject, update the ADR:
- Set new `status`
- Update `date_updated`
- Add reviewer to `decision_makers`

For defer, create a comment or note specifying:
- What's missing
- Who needs to act
- When to re-review

## Agent Guidelines

1. **Recommend with rationale** — Present the ECADR checklist results and anti-pattern findings, then recommend accept/reject/defer with clear reasoning. The human makes the final decision.

2. **Quote specific text** — When citing issues, quote the exact text from the ADR that demonstrates the problem.

3. **Suggest specific improvements** — For defer recommendations, specify exactly what changes would move the ADR to acceptable.

4. **Avoid review anti-patterns** — Don't rubber-stamp (Pass Through) or nitpick grammar (Copy Edit). Focus on decision quality.
