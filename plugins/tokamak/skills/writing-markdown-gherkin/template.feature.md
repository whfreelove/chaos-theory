# Feature: <feature name>

<!--
MDG (Markdown-Gherkin) template. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

Structure: Feature > Rule > Scenario
- Feature: top-level grouping (one per file)
- Rule: business rule or requirement being specified
- Scenario: concrete example demonstrating the rule
-->

## Rule: <business rule or requirement>

<!--
OPTIONAL: Background for preconditions shared by ALL scenarios in this Rule.
Only add if it reduces repetition. Omit if scenarios have different preconditions.

### Background

- Given <common precondition>
-->

### Scenario: <short behavior title>

- Given <initial state>
- When <action being tested>
- Then <expected outcome>

<!--
OPTIONAL: Scenario Outline for variations of same behavior.

### Scenario Outline: <parameterized behavior>

- Given <state with "<placeholder>">
- When <action with "<placeholder>">
- Then <outcome with "<placeholder>">

#### Examples

| placeholder | expected |
|-------------|----------|
| value1      | result1  |
| value2      | result2  |
-->
