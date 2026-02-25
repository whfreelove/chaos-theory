# Feature: <capability name> (<capability-slug>)

<!--
MDG format. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

TERMINOLOGY (functional spec language → Gherkin keyword):
- "Capability" → "Feature" (one Feature per capability)
- "Requirement" → "Rule" (requirements are grouped as Rules)

PROJECT-LEVEL: Flat structure, no delta wrappers (ADDED/MODIFIED/REMOVED).
BROWNFIELD: Derive scenarios from existing test suites and code behavior.
-->

## Requirements

<!--
Rules (= requirements) group scenarios under business invariants.
Derive from existing tests and code behavior — each test implies a scenario.
-->

`@<capability-slug>:1`
### Rule: <business rule derived from code behavior>

<!--
OPTIONAL: Background for preconditions shared by ALL scenarios in this Rule.
Only add if it reduces repetition.

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
| value1      | result1  |
-->
