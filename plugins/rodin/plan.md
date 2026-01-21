# Plugin: ExitPlanMode Evaluation Hook

## Purpose
Prevents premature exit from plan mode by enforcing a deliberate workflow where:
1. Complexity must be assessed
2. For non-trivial work, the plan must be critiqued (not just drafted)
3. The user must explicitly approve the plan (Claude cannot self-approve)

## Plugin Configuration

### Hook Type
`PreToolUse`

### Matcher
`ExitPlanMode`

### Hook Definition

```json
{
  "type": "prompt",
  "prompt": "Before allowing ExitPlanMode, evaluate the conversation:\n\n1. COMPLEXITY CHECK: Did Claude ask the user whether this is low-effort/quick work?\n   - If NOT asked → BLOCK with reason: 'Ask user if this is low-effort work before exiting plan mode'\n   - If asked and user said YES (low effort) → ALLOW\n   - If asked and user said NO (not low effort) → Continue to step 2\n\n2. CRITIQUE CHECK: Has Claude critically reviewed this plan, or is it just a first draft?\n   - If no critique/review happened → BLOCK with reason: 'Critique the plan before exiting plan mode'\n\n3. USER APPROVAL CHECK: Has the USER explicitly stated they think this plan is ready to implement?\n   - If user has not approved → BLOCK with reason: 'User must explicitly approve the plan before exiting'\n   - If user has approved → ALLOW\n\nReturn JSON: {\"decision\": \"allow\"} or {\"decision\": \"block\", \"reason\": \"...\"}",
  "timeout": 45
}
```

## Full settings.json Structure

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "ExitPlanMode",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Before allowing ExitPlanMode, evaluate the conversation:\n\n1. COMPLEXITY CHECK: Did Claude ask the user whether this is low-effort/quick work?\n   - If NOT asked → BLOCK with reason: 'Ask user if this is low-effort work before exiting plan mode'\n   - If asked and user said YES (low effort) → ALLOW\n   - If asked and user said NO (not low effort) → Continue to step 2\n\n2. CRITIQUE CHECK: Has Claude critically reviewed this plan, or is it just a first draft?\n   - If no critique/review happened → BLOCK with reason: 'Critique the plan before exiting plan mode'\n\n3. USER APPROVAL CHECK: Has the USER explicitly stated they think this plan is ready to implement?\n   - If user has not approved → BLOCK with reason: 'User must explicitly approve the plan before exiting'\n   - If user has approved → ALLOW\n\nReturn JSON: {\"decision\": \"allow\"} or {\"decision\": \"block\", \"reason\": \"...\"}",
            "timeout": 45
          }
        ]
      }
    ]
  }
}
```

## Workflow Diagram

```
User requests work
        │
        ▼
┌───────────────────┐
│ Claude asks:      │
│ "Is this low-     │
│ effort work?"     │
└────────┬──────────┘
         │
    ┌────┴────┐
    │         │
   YES        NO
    │         │
    ▼         ▼
 ALLOW    ┌──────────────┐
          │ Claude writes │
          │ & critiques   │
          │ the plan      │
          └──────┬───────┘
                 │
                 ▼
          ┌──────────────┐
          │ User says:   │
          │ "Plan ready" │
          └──────┬───────┘
                 │
                 ▼
              ALLOW
```

## Expected Behavior

| Scenario | Hook Response |
|----------|---------------|
| No complexity question asked | BLOCK: "Ask user if this is low-effort work before exiting plan mode" |
| User confirmed low-effort work | ALLOW |
| Complex work, no critique | BLOCK: "Critique the plan before exiting plan mode" |
| Complex work, critiqued, no user approval | BLOCK: "User must explicitly approve the plan before exiting" |
| Complex work, critiqued, user approved | ALLOW |

## Verification Checklist

1. [ ] Start a new session in plan mode
2. [ ] Attempt to exit without asking about complexity → should block
3. [ ] Ask about complexity, user says "not low effort"
4. [ ] Attempt to exit without critiquing → should block
5. [ ] Write and critique plan
6. [ ] Attempt to exit without user approval → should block
7. [ ] User approves plan → exit should succeed

## Response Format

The hook must return valid JSON:

**Allow:**
```json
{"decision": "allow"}
```

**Block:**
```json
{"decision": "block", "reason": "Human-readable explanation"}
```
