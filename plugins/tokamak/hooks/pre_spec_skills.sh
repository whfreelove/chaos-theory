#!/bin/bash
# Hook: Validate spec skill prerequisites before rendering
# Triggered: PreToolUse on Skill
# Denies if args are missing, change dir is invalid, or triage policy is malformed

set -uo pipefail

deny() {
  local reason="$1"
  local system_msg="${2:-Skill invocation blocked by pre_spec_skills hook.}"
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
  # --- Redirects: deny with actionable message pointing to tokamak equivalents ---
  openspec-apply-change|opsx:apply)
    deny \
      "Use tokamak:implement-change instead of ${skill}. Call: Skill(tokamak:implement-change, args: \"<change-name>\")" \
      "${skill} blocked: use tokamak:implement-change for lifecycle-managed implementation."
    ;;
  openspec-sync-specs|opsx:sync)
    deny \
      "Use tokamak:merge-change instead of ${skill}. Call: Skill(tokamak:merge-change, args: \"<change-name>\")" \
      "${skill} blocked: use tokamak:merge-change for lifecycle-managed merging."
    ;;
  openspec-archive-change|opsx:archive)
    deny \
      "Use tokamak:archive-change instead of ${skill}. Call: Skill(tokamak:archive-change, args: \"<change-name>\")" \
      "${skill} blocked: use tokamak:archive-change for lifecycle-managed archiving."
    ;;
  openspec-bulk-archive-change|opsx:bulk-archive)
    deny \
      "Use tokamak:archive-change instead of ${skill} (archive changes individually for lifecycle tracking). Call: Skill(tokamak:archive-change, args: \"<change-name>\")" \
      "${skill} blocked: archive changes individually via tokamak:archive-change."
    ;;
  # --- Gated skill types ---
  critique-specs|tokamak:critique-specs|\
  critique-specs-brownfield|tokamak:critique-specs-brownfield)
    skill_type="critique"
    ;;
  resolve-gaps|tokamak:resolve-gaps|\
  resolve-gaps-brownfield|tokamak:resolve-gaps-brownfield)
    skill_type="resolve"
    ;;
  sculpt-specs|tokamak:sculpt-specs)
    skill_type="sculpt"
    ;;
  ratify-specs|tokamak:ratify-specs)
    skill_type="ratify"
    ;;
  implement-change|tokamak:implement-change)
    skill_type="implement"
    ;;
  merge-change|tokamak:merge-change)
    skill_type="merge"
    ;;
  archive-change|tokamak:archive-change)
    skill_type="archive"
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
change_name="${args%% *}"
change_dir="openspec/changes/${change_name}"
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
    "No .openspec.yaml in ${change_dir}. Create the change first: Skill(tokamak:new-change, args: \"${change_name}\")" \
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

# --- Status gating: check lifecycle state ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"
status_script="${PLUGIN_ROOT}/scripts/change_status.sh"

case "$skill_type" in
  critique)
    if ! current=$("$status_script" check "$change_dir" specs-status "reviewing"); then
      if [[ "$current" == "draft" ]]; then
        deny \
          "Cannot run ${skill} when specs-status is 'draft'. Use sculpt-specs to refine design first, then promote to reviewing. Call: Skill(tokamak:sculpt-specs, args: \"${args}\")" \
          "${skill} blocked: specs-status is 'draft'. Use sculpt-specs to promote to reviewing."
      else
        deny \
          "Cannot run ${skill} when specs-status is '${current}'. To critique, the change must be in 'reviewing' state." \
          "${skill} blocked: specs-status is '${current}', requires 'reviewing'."
      fi
    fi
    ;;
  resolve)
    if ! current=$("$status_script" check "$change_dir" specs-status "reviewing"); then
      if [[ "$current" == "draft" ]]; then
        deny \
          "Cannot run ${skill} when specs-status is 'draft'. Use sculpt-specs to refine design first, then promote to reviewing. Call: Skill(tokamak:sculpt-specs, args: \"${args}\")" \
          "${skill} blocked: specs-status is 'draft'. Use sculpt-specs to promote to reviewing."
      else
        deny \
          "Cannot run ${skill} when specs-status is '${current}'. To resolve gaps, the change must be in 'reviewing' state." \
          "${skill} blocked: specs-status is '${current}', requires 'reviewing'."
      fi
    fi
    ;;
  sculpt)
    if ! current=$("$status_script" check "$change_dir" specs-status "draft"); then
      deny \
        "Cannot sculpt specs when specs-status is '${current}'. Sculpting requires 'draft' state." \
        "${skill} blocked: specs-status is '${current}', requires 'draft'."
    fi
    ;;
  ratify)
    if ! current=$("$status_script" check "$change_dir" specs-status "reviewing"); then
      if [[ -z "$current" ]]; then
        deny \
          "Cannot ratify specs without a review first. Run a critique round first: Skill(tokamak:critique-specs, args: \"${args}\")" \
          "${skill} blocked: specs-status not set, run critique-specs first."
      else
        deny \
          "Cannot ratify specs when specs-status is '${current}'. Required: 'reviewing'. Run Skill(tokamak:critique-specs, args: \"${args}\") first." \
          "${skill} blocked: specs-status is '${current}', requires 'reviewing'."
      fi
    fi
    ;;
  implement)
    if ! current=$("$status_script" check "$change_dir" code-status "ready|in-progress"); then
      if [[ -z "$current" || "$current" == "waiting" ]]; then
        deny \
          "Cannot implement when code-status is '${current:-waiting}'. Specs must be ratified first. Run: Skill(tokamak:ratify-specs, args: \"${args}\")" \
          "${skill} blocked: code-status is '${current:-waiting}', requires 'ready' or 'in-progress'."
      else
        deny \
          "Cannot implement when code-status is '${current}'. Implementation is already complete." \
          "${skill} blocked: code-status is '${current}', requires 'ready' or 'in-progress'."
      fi
    fi
    ;;
  merge)
    if ! current=$("$status_script" check "$change_dir" specs-status "ratified|merging"); then
      deny \
        "Cannot merge change when specs-status is '${current}'. Specs must be ratified first. Run: Skill(tokamak:ratify-specs, args: \"${change_name}\")" \
        "${skill} blocked: specs-status is '${current}', requires 'ratified' or 'merging'."
    fi
    ;;
  archive)
    # Archive requires BOTH tracks to be in terminal state
    if ! specs_current=$("$status_script" check "$change_dir" specs-status "merged"); then
      deny \
        "Cannot archive when specs-status is '${specs_current}'. Specs must be merged first. Run: Skill(tokamak:merge-change, args: \"${change_name}\")" \
        "${skill} blocked: specs-status is '${specs_current}', requires 'merged'."
    fi
    if ! code_current=$("$status_script" check "$change_dir" code-status "implemented|n/a"); then
      deny \
        "Cannot archive when code-status is '${code_current}'. Implementation must be complete first. Run: Skill(tokamak:implement-change, args: \"${args}\")" \
        "${skill} blocked: code-status is '${code_current}', requires 'implemented' or 'n/a'."
    fi
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
