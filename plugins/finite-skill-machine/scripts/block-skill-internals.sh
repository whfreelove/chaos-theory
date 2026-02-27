#!/bin/bash
# Prevents agents from reading skill internals directly.
# Skills should be invoked via the Skill tool, not snooped.

[[ -n "${FSM_BYPASS:-}" ]] && exit 0

INPUT=$(cat)
PATH_ARG=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // .tool_input.pattern // ""')

if [[ "$PATH_ARG" == *"SKILL.md"* ]] || [[ "$PATH_ARG" == *"fsm.json"* ]] || [[ "$PATH_ARG" == *"hooks.json"* ]]; then
  cat <<EOF
{
  "systemMessage": "Access to skill internals is blocked. To allow access for this session, run: export FSM_BYPASS=1",
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Skill-internal file is protected. Set FSM_BYPASS=1 to bypass."
  }
}
EOF
fi

exit 0
