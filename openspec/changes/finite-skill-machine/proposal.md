## Why

Skills can define multi-step workflows, but getting tasks into the TaskList requires the agent to interpret definitions and create each task manually. This burns context, introduces variability, and limits what simpler/faster models can handle. Task hydration should be automatic and consistent.

## What Changes

- New plugin `finite-skill-machine`
- Skills can include an `fsm.json` companion file defining tasks
- When a skill loads, FSM reads the companion file and hydrates the TaskList automatically
- Task dependencies use local numeric IDs (translated to actual IDs at hydration)

## Capabilities

### New Capabilities

- `task-hydration-skill`: Automatic task creation from skill-defined workflows

### Modified Capabilities

(none)

## Impact

- **Skill authors** can ship complete task workflows; users get a ready-to-execute checklist on skill load
- **Users** see consistent task lists regardless of which model runs the skill
- **Simpler models** can handle complex workflows since task setup is automatic
