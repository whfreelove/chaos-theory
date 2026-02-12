#!/bin/bash
# Prevents agents from reading skill internals directly.
# Skills should be invoked via the Skill tool, not snooped.

INPUT=$(cat)
PATH_ARG=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // .tool_input.pattern // ""')

if [[ "$PATH_ARG" == *"SKILL.md"* ]] || [[ "$PATH_ARG" == *"fsm.json"* ]] || [[ "$PATH_ARG" == *"hooks.json"* ]]; then
  cat <<EOF
{
  "systemMessage": "Skill file access blocked. Disable finite-skill-machine plugin if developing skills.",
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Use the Skill tool to invoke skills instead of reading files directly."
  }
}
EOF
fi

exit 0
