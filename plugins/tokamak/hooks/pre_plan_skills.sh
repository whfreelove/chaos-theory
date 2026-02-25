#!/bin/bash
# Hook: Gate plan-required skills behind plan mode
# Triggered: PreToolUse on Skill
# Denies listed skills when not in plan mode, directing agent to EnterPlanMode first

set -uo pipefail

deny() {
  local reason="$1"
  local system_msg="${2:-Skill invocation blocked by pre_plan_skills hook.}"
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

# Skills that require plan mode before invocation
PLAN_REQUIRED=(
  "opsx:continue"
  "openspec-continue-change"
  "opsx:ff"
  "openspec-ff-change"
)

input=$(cat)

skill=$(echo "$input" | jq -r '.tool_input.skill // empty')

# Check if skill is in the PLAN_REQUIRED list
match=false
for s in "${PLAN_REQUIRED[@]}"; do
  if [[ "$skill" == "$s" ]]; then
    match=true
    break
  fi
done

if [[ "$match" == "false" ]]; then
  exit 0  # Not a gated skill, allow
fi

permission_mode=$(echo "$input" | jq -r '.permission_mode // "default"')

if [[ "$permission_mode" == "plan" ]]; then
  exit 0  # In plan mode, allow
fi

deny \
  "$skill must be invoked from plan mode. Call EnterPlanMode first, then invoke the skill again." \
  "$skill blocked: not in plan mode. Use EnterPlanMode to enter plan mode, then retry."
