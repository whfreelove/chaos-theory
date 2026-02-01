## Why

<!--
State the problem in HUMAN BURDEN terms - what pain does this cause users/developers?

GOOD examples:
- "Manual task creation burns context and introduces variability across sessions"
- "Users must re-explain requirements each time, wasting effort"

BAD examples (implementation-focused):
- "We need a hook to intercept X" (mechanism, not burden)
- "The API is missing endpoint Y" (technical gap, not human cost)

Keep to 1-2 sentences. If you need more, you're leaking implementation.
-->

## What Changes

<!--
List ARTIFACTS and BEHAVIORS that will change - what the user will see/get.

FORBIDDEN verbs: implements, uses, supports, calls, invokes, leverages, utilizes
FORBIDDEN nouns: hook, algorithm, data structure, endpoint, handler, middleware

GOOD examples:
- "New plugin `finite-skill-machine`"
- "Skills can include an `fsm.json` companion file defining tasks"
- "Task dependencies use local numeric IDs"

BAD examples:
- "Implements a hook system for task injection" (HOW not WHAT)
- "Uses PostToolUse to intercept skill loading" (mechanism detail)

Mark breaking changes with **BREAKING**.
-->

## Capabilities

<!--
Group by ACTOR/ROLE, not by feature. Format: `<actor> can <outcome>`

GOOD structure:
- **Skill authors** can ship complete task workflows
- **Users** see consistent task lists regardless of model
- **Simpler models** can handle complex workflows

BAD structure:
- "FSM Hook: Intercepts skill loading" (feature-centric)
- "TaskList Integration: Creates tasks automatically" (component-centric)

Each capability should be testable: can you verify an actor achieves the outcome?
-->

### New Capabilities

<!-- Use kebab-case identifiers. Each creates specs/<name>/spec.md -->
- `<name>`: <brief description of what this capability covers>

### Modified Capabilities

<!-- Only list if spec-level REQUIREMENTS change. Use existing names from openspec/specs/. -->
- `<existing-name>`: <what requirement is changing>

## Impact

<!--
Describe USER INTERACTION changes, not technical footprint.

GOOD examples:
- "Skill authors can ship complete task workflows; users get a ready-to-execute checklist on skill load"
- "Users see consistent task lists regardless of which model runs the skill"

BAD examples:
- "Adds 3 new files to the plugin directory" (technical footprint)
- "Requires PostToolUse hook registration" (implementation detail)
-->

## Non-Goals

<!--
OPTIONAL: Explicitly scope what this change does NOT address.
Useful for preventing scope creep and clarifying boundaries.

Example:
- "Task execution order optimization (future work)"
- "Multi-skill task coordination (separate proposal)"
-->
