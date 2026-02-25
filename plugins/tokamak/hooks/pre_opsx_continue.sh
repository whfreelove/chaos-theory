#!/bin/bash
# Hook: Gate opsx:continue behind plan mode
# Triggered: PreToolUse on Skill
# Denies opsx:continue when not in plan mode, directing agent to EnterPlanMode first

set -uo pipefail

deny() {
  local reason="$1"
  local system_msg="${2:-Skill invocation blocked by pre_opsx_continue hook.}"
  jq -n --arg reason "$reason" --arg msg "$system_msg" '{
    systemMessage: $msg,
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: $reason
    }
  }'
  exit 0
}

input=$(cat)

skill=$(echo "$input" | jq -r '.tool_input.skill // empty')

# Only gate opsx:continue (both short and long forms)
case "$skill" in
  opsx:continue|openspec-continue-change)
    ;;
  *)
    exit 0  # Not our concern, allow
    ;;
esac

permission_mode=$(echo "$input" | jq -r '.permission_mode // "default"')

if [[ "$permission_mode" == "plan" ]]; then
  exit 0  # In plan mode, allow
fi

deny \
  "opsx:continue must be invoked from plan mode. Call EnterPlanMode first, then invoke Skill(opsx:continue) again. The skill handles planning once loaded." \
  "opsx:continue blocked: not in plan mode. Use EnterPlanMode to enter plan mode, then retry."
