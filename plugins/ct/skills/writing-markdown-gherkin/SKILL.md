---
name: writing-markdown-gherkin
description: Use when writing BDD specs, feature files, or acceptance tests in Given-When-Then format. Use when editing *.feature.md files or writing requirements with behavioral scenarios.
---

## File Extension

MDG files use the `.feature.md` extension. If you're editing Gherkin-style Markdown without this extension, suggest renaming to `*.feature.md`.

For a starter template, see [template.feature.md](template.feature.md).

## MDG Structure

Markdown-Gherkin (MDG) uses Gherkin keywords as headers with nesting relationships:

```
Feature
├── Rule
│   ├── Background (optional, shared Given steps)
│   ├── Scenario
│   └── Scenario Outline
│       └── Examples
```

**Feature** uses `#` and must be the first line of the file. One Feature per `.feature.md` file.

**Containment rules:**
- Feature contains Rules
- Rules contain Background, Scenarios, and Scenario Outlines
- Scenario Outlines contain Examples

Header levels for contained elements are flexible - implementations may insert intermediate headers. What matters is that contained elements use deeper header levels than their containers.

## Tags

Tags categorize and filter Features, Rules, and Scenarios. Place tags on the line preceding the header, wrapped in backticks.

Common uses:
- `@wip` - work in progress
- `@slow` - long-running tests
- `@smoke` - critical path tests
- `@skip` - temporarily disabled

```markdown
`@smoke`
# Feature: User authentication

`@wip`
## Rule: Password validation

`@slow`
### Scenario: Brute force protection
```

Multiple tags can appear on the same line: `` `@smoke` `@critical` ``

## Normative Language

Requirements use **SHALL** or **MUST** for mandatory behavior. Avoid weak language:

| Avoid | Use Instead |
|-------|-------------|
| should | SHALL |
| may, might | MUST (if required) or omit (if optional) |
| can | is able to / SHALL support |
| will | SHALL |

Example: "The system SHALL reject invalid input" not "The system should reject invalid input"

## Cardinal Rule

**One Scenario = One Behavior**. Each When-Then pair denotes one distinct behavior. Multiple When-Then pairs = multiple scenarios.

## Scenario Structure

- **Given-When-Then order is mandatory** (no repeats)
- Given: establishes initial state (not actions)
- When: performs the action being tested
- Then: verifies outcome
- And/But: continues the current step type

## Background

Background contains Given steps executed before each scenario within its scope. Use it to reduce repetition of common preconditions.

```markdown
## Rule: User must be authenticated

### Background

- Given an authenticated user session

### Scenario: Access protected resource

- When the user requests the dashboard
- Then the dashboard is displayed

### Scenario: Access admin settings

- When the user opens admin settings
- Then the settings page is displayed
```

## Scenario Outline

Scenario Outlines run the same scenario multiple times with different data. Use `<placeholder>` syntax in steps and provide an Examples table.

```markdown
### Scenario Outline: File validation

- Given a file named "<filename>"
- When the validator runs
- Then the result is "<outcome>"

#### Examples

| filename | outcome |
|----------|---------|
| valid.json | accepted |
| malformed.json | rejected |
| empty.json | rejected |
```

Each row in the Examples table executes the scenario once with substituted values.

## Step Phrasing

1. **Third-person only**: "the user clicks" NOT "I click"
2. **Present tense for all steps**: "is displayed", "enters", "shows" (avoid past/future)
3. **Subject-predicate format**: Complete action phrases, never fragments
4. **Declarative over imperative**: State WHAT happens, not HOW it happens step-by-step

## Scenario Titles

- Short one-liners describing the behavior
- Avoid: "verify", "assert", "should"
- Avoid: conjunctions ("and", "or", "because") suggesting multiple behaviors
- Focus on WHAT not WHY

## Data Handling

- Use Scenario Outlines for variations of same behavior
- No "Or" steps exist - use Examples tables instead
- Hide implementation details; expose only behavior-relevant data
- Write defensively - avoid hard-coded values that may change
- Keep examples focused on equivalence classes

## Brevity

- <10 steps per scenario
- 80-120 characters per step
- If too long, make steps more declarative or split behaviors

## Formatting

- Capitalize Gherkin keywords (Given, When, Then, And, But)
- Capitalize first word of titles only
- No periods/commas at step end
- Proper spelling and grammar
- Single spaces, evenly spaced table pipes

## Example Transformation

**BAD** (procedure-driven, multi-behavior, flat structure):

```markdown
## Feature

### Scenario: Image search from the search bar

- Given the user opens a web browser
- And the user navigates to "google.com"
- When the user enters "panda" into the search bar
- Then links for "panda" are shown
- When the user clicks "Images"
- Then images for "panda" are shown
```

**GOOD** (behavior-driven with proper hierarchy and Background):

```markdown
# Feature: Google search

## Rule: Search bar returns relevant results

### Background

- Given the user is on the Google home page

### Scenario: Text search

- When the user enters "panda" into the search bar
- Then links related to "panda" are shown

### Scenario: Image search from results

- Given search results for "panda" are displayed
- When the user clicks the "Images" link
- Then images related to "panda" are shown
```
