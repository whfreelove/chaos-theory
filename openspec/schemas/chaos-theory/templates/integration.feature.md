# Feature: <integration concern> (integration)

<!--
OPTIONAL FILE - only create when capabilities interact in ways not captured
by single-capability requirements.

MDG format. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

PURPOSE: Cross-capability integration test scenarios.
- Tests interactions BETWEEN capabilities
- Does NOT duplicate single-capability requirements
- References involved capabilities with @capability-slug tags
-->

## Integration Scenarios

<!--
Rules group related integration behaviors.
Tag with involved capabilities: @capability-a @capability-b
-->

`@integration:1` `@<capability-a>` `@<capability-b>`
### Rule: <integration behavior these capabilities must satisfy together>

`@integration:1.1`
#### Scenario: <short behavior title - no "verify", "should", "and">

- Given <initial state involving multiple capabilities>
- When <action triggering cross-capability interaction>
- Then <expected outcome observable across capabilities>

<!--
GUIDELINES:
- Only include scenarios spanning multiple capabilities
- Don't duplicate scenarios from individual requirements files
- Focus on integration boundaries and handoffs
- Tag all involved capabilities for traceability
-->
