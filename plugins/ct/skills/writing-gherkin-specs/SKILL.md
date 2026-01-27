---
name: writing-gherkin-specs
description: Use when writing BDD specs, feature files, or acceptance tests in Given-When-Then format. Use when writing requirements with behavioral scenarios.
---

## Spec Writing

### Cardinal Rule

**One Scenario = One Behavior**. Each When-Then pair denotes one distinct behavior. Multiple When-Then pairs = multiple scenarios.

### Scenario Structure

- **Given-When-Then order is mandatory** (no repeats)
- Given: establishes initial state (not actions)
- When: performs the action being tested
- Then: verifies outcome
- And/But: continues the current step type

### Step Phrasing

1. **Third-person only**: "the user clicks" NOT "I click"
2. **Present tense for all steps**: "is displayed", "enters", "shows" (avoid past/future)
3. **Subject-predicate format**: Complete action phrases, never fragments
4. **Declarative over imperative**: State WHAT happens, not HOW it happens step-by-step

### Scenario Titles

- Short one-liners describing the behavior
- Avoid: "verify", "assert", "should"
- Avoid: conjunctions ("and", "or", "because") suggesting multiple behaviors
- Focus on WHAT not WHY

### Data Handling

- Use Scenario Outlines for variations of same behavior
- No "Or" steps exist - use Examples tables instead
- Hide implementation details; expose only behavior-relevant data
- Write defensively - avoid hard-coded values that may change
- Keep examples focused on equivalence classes

### Brevity

- <10 steps per scenario
- 80-120 characters per step
- If too long, make steps more declarative or split behaviors

### Formatting

- Capitalize Gherkin keywords (Given, When, Then, And, But)
- Capitalize first word of titles only
- No periods/commas at step end
- Proper spelling and grammar
- Single spaces, evenly spaced table pipes

### Example Transformation

**BAD** (procedure-driven):

```gherkin
## Feature

### Scenario: Image search from the search bar

- GIVEN the user opens a web browser
- AND the user navigates to "google.com"
- WHEN the user enters "panda" into the search bar
- THEN links for "panda" are shown
- WHEN the user clicks "Images"
- THEN images for "panda" are shown
```

**GOOD** (behavior-driven):

```gherkin
## Feature

### Scenario: Search from the search bar

- GIVEN a web browser is at the Google home page
- WHEN the user enters "panda" into the search bar
- THEN links related to "panda" are shown

### Scenario: Image search

- GIVEN Google search results for "panda" are shown
- WHEN the user clicks the "Images" link
- THEN images related to "panda" are shown
```
