# Feature: <capability name> (<capability-slug>)

<!--
DO NOT REMOVE THIS HEADER - it documents terminology mapping for editors.

MDG format. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

TERMINOLOGY (proposal language → Gherkin keyword):
- "Capability" → "Feature" (one Feature per capability)
- "Requirement" → "Rule" (requirements are grouped as Rules)

We use Gherkin syntax, so headers say "Feature" and "Rule".
-->

## ADDED Requirements

<!--
Rules (= requirements) group scenarios under business invariants.
-->

`@<capability-slug>:1`
### Rule: <business rule this capability must satisfy>

<!--
OPTIONAL: Background for preconditions shared by ALL scenarios in this Rule.
Only add if it reduces repetition. Omit if scenarios have different preconditions.

#### Background
- Given <common precondition>
-->

`@<capability-slug>:1.1`
#### Scenario: <short behavior title - no "verify", "should", "and">

- Given <initial state>
- When <action being tested>
- Then <expected outcome>

<!--
OPTIONAL: Scenario Outline for variations of same behavior.

#### Scenario Outline: <parameterized behavior>
- Given <state with "<placeholder>">
- When <action with "<placeholder>">
- Then <outcome with "<placeholder>">

##### Examples
| placeholder | expected |
|-------------|----------|
| value1 | result1 |
-->

## MODIFIED Requirements

<!--
Contains full updated MDG content for changed rules.
Copy existing rule, paste here, modify.
-->

## REMOVED Requirements

<!--
List of removed rule IDs with nested reason.
Migration details do NOT go here - they belong in design.md or tasks.md.
-->

- `@<slug>:Y`
  - **Reason**: <why this rule is being removed>

## RENAMED Requirements

<!--
List of renamed rule IDs with nested reason.
-->

- `@<old-slug>:Y` → `@<new-slug>:Y`
  - **Reason**: <why this rule is being renamed>
