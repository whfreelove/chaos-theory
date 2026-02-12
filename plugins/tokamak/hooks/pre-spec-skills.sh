#!/bin/bash
# Hook: Validate spec skill args before rendering
# Triggered: PreToolUse on Skill
# Action: Block if $0 arg is missing or not a valid chaos-theory change
# Action: Block resolve-gaps skills if .triage-policy.json is missing or malformed

set -euo pipefail

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

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

args=$(echo "$input" | jq -r '.tool_input.args // empty')

# Check: args provided
if [[ -z "$args" ]]; then
  cat <<EOF
BLOCKED: ${skill} requires a change directory argument.

Usage: Skill(tokamak:${skill}, args: "<change-name>")

Available changes:
EOF
  ls -1 openspec/changes/ 2>/dev/null | sed 's/^/  - /'
  exit 1
fi

# Check: directory exists
change_dir="openspec/changes/${args}"
if [[ ! -d "$change_dir" ]]; then
  cat <<EOF
BLOCKED: Change directory not found: ${change_dir}

Available changes:
EOF
  ls -1 openspec/changes/ 2>/dev/null | sed 's/^/  - /'
  exit 1
fi

# Check: .openspec.yaml exists
openspec_yaml="${change_dir}/.openspec.yaml"
if [[ ! -f "$openspec_yaml" ]]; then
  cat <<EOF
BLOCKED: No .openspec.yaml found in ${change_dir}

${skill} requires an OpenSpec change with a chaos-theory schema.
EOF
  exit 1
fi

# Check: schema is chaos-theory*
first_line=$(head -1 "$openspec_yaml")
case "$first_line" in
  schema:\ chaos-theory*)
    ;;  # Valid chaos-theory schema
  *)
    cat <<EOF
BLOCKED: ${change_dir} uses a non-chaos-theory schema.

Found: ${first_line}
Expected: schema: chaos-theory*

${skill} only supports chaos-theory schema changes.
EOF
    exit 1
    ;;
esac

# --- Skill-specific validation: resolve-gaps triage policy ---
if [[ "$skill_type" == "resolve" ]]; then
  triage_policy="${change_dir}/.triage-policy.json"

  if [[ ! -f "$triage_policy" ]]; then
    cat <<EOF
BLOCKED: No .triage-policy.json in ${change_dir}.

Run tokamak:new-change to create a change with triage policy initialized.
EOF
    exit 1
  fi

  # Validate JSON structure
  if ! jq empty "$triage_policy" 2>/dev/null; then
    cat <<EOF
BLOCKED: .triage-policy.json is not valid JSON.

Fix the JSON syntax in: ${triage_policy}
EOF
    exit 1
  fi

  # Validate required keys and values
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
    ] | if length > 0 then join("\n") else empty end
  ' "$triage_policy" 2>/dev/null)

  if [[ -n "$validation_errors" ]]; then
    cat <<EOF
BLOCKED: .triage-policy.json has validation errors:

${validation_errors}

Expected schema:
{
  "high":   { "authority": "user"|"agent", "actions": ["check-in", "delegate", "defer-release", "defer-resolution"] },
  "medium": { "authority": "user"|"agent", "actions": [...] },
  "low":    { "authority": "user"|"agent", "actions": [...] }
}

Valid authorities: user, agent
Valid actions: check-in, delegate, defer-release, defer-resolution
EOF
    exit 1
  fi
fi

exit 0
