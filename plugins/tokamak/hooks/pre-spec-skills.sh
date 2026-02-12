#!/bin/bash
# Hook: Validate spec skill prerequisites before rendering
# Triggered: PreToolUse on Skill
# Denies if args are missing, change dir is invalid, or triage policy is malformed

set -uo pipefail

deny() {
  local reason="$1"
  local system_msg="${2:-Skill invocation blocked by pre-spec-skills hook.}"
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

# Determine skill type for skill-specific validation
skill_type=""
case "$skill" in
  critique-specs|tokamak:critique-specs|\
  critique-specs-brownfield|tokamak:critique-specs-brownfield)
    skill_type="critique"
    ;;
  resolve-gaps|tokamak:resolve-gaps|\
  resolve-gaps-brownfield|tokamak:resolve-gaps-brownfield)
    skill_type="resolve"
    ;;
  *)
    exit 0  # Not a gated skill, allow
    ;;
esac

args=$(echo "$input" | jq -r '.tool_input.args // empty')

# --- Validation: args provided ---
if [[ -z "$args" ]]; then
  available=$(ls -1 openspec/changes/ 2>/dev/null | sed 's/^/  - /' || true)
  deny \
    "${skill} requires a change directory argument. Call: Skill(tokamak:${skill}, args: \"<change-name>\"). Available changes:
${available:-  (none found)}" \
    "${skill} blocked: missing change directory argument."
fi

# --- Validation: directory exists ---
change_dir="openspec/changes/${args}"
if [[ ! -d "$change_dir" ]]; then
  available=$(ls -1 openspec/changes/ 2>/dev/null | sed 's/^/  - /' || true)
  deny \
    "Change directory not found: ${change_dir}. Call: Skill(tokamak:${skill}, args: \"<change-name>\") with one of:
${available:-  (none found)}" \
    "${skill} blocked: ${change_dir} does not exist."
fi

# --- Validation: .openspec.yaml exists ---
openspec_yaml="${change_dir}/.openspec.yaml"
if [[ ! -f "$openspec_yaml" ]]; then
  deny \
    "No .openspec.yaml in ${change_dir}. Create the change first: Skill(tokamak:new-change, args: \"${args}\")" \
    "${skill} blocked: missing .openspec.yaml in ${change_dir}."
fi

# --- Validation: schema is chaos-theory* ---
first_line=$(head -1 "$openspec_yaml")
case "$first_line" in
  schema:\ chaos-theory*)
    ;;  # Valid
  *)
    deny \
      "${change_dir} uses schema '${first_line}' but ${skill} requires a chaos-theory schema. Edit ${openspec_yaml} line 1 to: schema: chaos-theory" \
      "${skill} blocked: incompatible schema in ${change_dir}."
    ;;
esac

# --- Skill-specific: resolve-gaps triage policy ---
if [[ "$skill_type" == "resolve" ]]; then
  triage_policy="${change_dir}/.triage-policy.json"

  if [[ ! -f "$triage_policy" ]]; then
    deny \
      "No .triage-policy.json in ${change_dir}. Create the change with triage policy: Skill(tokamak:new-change, args: \"${args}\")" \
      "${skill} blocked: missing .triage-policy.json in ${change_dir}."
  fi

  # Validate JSON syntax
  if ! jq empty "$triage_policy" 2>/dev/null; then
    deny \
      ".triage-policy.json is not valid JSON. Fix syntax errors in: ${triage_policy}" \
      "${skill} blocked: malformed JSON in ${triage_policy}."
  fi

  # Validate required structure
  validation_errors=$(jq -r '
    def valid_actions: ["check-in", "delegate", "defer-release", "defer-resolution"];
    def valid_authorities: ["user", "agent"];
    [
      (["high", "medium", "low"][] as $level |
        if has($level) then
          (
            if (.[$level] | type) != "object" then
              "\($level): must be an object"
            else
              (
                if (.[$level] | has("authority") | not) then
                  "\($level): missing authority field"
                elif ([.[$level].authority] | inside(valid_authorities) | not) then
                  "\($level): authority must be user or agent, got \(.[$level].authority)"
                else
                  empty
                end
              ),
              (
                if (.[$level] | has("actions") | not) then
                  "\($level): missing actions field"
                elif (.[$level].actions | type) != "array" then
                  "\($level): actions must be an array"
                elif (.[$level].actions | length) == 0 then
                  "\($level): actions must be non-empty"
                else
                  (.[$level].actions[] as $a |
                    if ([$a] | inside(valid_actions) | not) then
                      "\($level): invalid action \($a)"
                    else
                      empty
                    end
                  )
                end
              )
            end
          )
        else
          "\($level): missing required key"
        end
      )
    ] | if length > 0 then join("; ") else empty end
  ' "$triage_policy" 2>/dev/null)

  if [[ -n "$validation_errors" ]]; then
    deny \
      "Validation errors in ${triage_policy}: ${validation_errors}. Edit ${triage_policy} to match expected schema: {\"high\": {\"authority\": \"user\"|\"agent\", \"actions\": [\"check-in\",\"delegate\",\"defer-release\",\"defer-resolution\"]}, \"medium\": {...}, \"low\": {...}}" \
      "${skill} blocked: invalid .triage-policy.json in ${change_dir}."
  fi
fi

exit 0
