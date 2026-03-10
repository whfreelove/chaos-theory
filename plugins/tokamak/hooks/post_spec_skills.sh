#!/bin/bash
# FSM Hook: Remove invoked skills from required state
# Triggered: PostToolUse on Skill
# Action: Remove the invoked skill name from state file

set -euo pipefail

input=$(cat)

# Get session ID for state file naming
session_id=$(echo "$input" | jq -r '.session_id // "default"')
state_file="/tmp/fsm_ct_${session_id}.txt"

# If no state file exists, nothing to do
if [[ ! -f "$state_file" ]]; then
  echo '{"continue": true}'
  exit 0
fi

# Extract invoked skill name from tool input
skill=$(echo "$input" | jq -r '.tool_input.skill // empty')

if [[ -z "$skill" ]]; then
  echo '{"continue": true}'
  exit 0
fi

# Remove the skill from state file (exact match, one occurrence)
# Use a temp file to avoid read/write conflicts
temp_file=$(mktemp)
removed=false

while IFS= read -r line || [[ -n "$line" ]]; do
  if [[ "$line" == "$skill" && "$removed" == false ]]; then
    removed=true
    echo "FSM: Satisfied requirement for skill '$skill'" >&2
  else
    echo "$line" >> "$temp_file"
  fi
done < "$state_file"

# Replace state file with filtered content
mv "$temp_file" "$state_file"

# If state file is now empty, remove it
if [[ ! -s "$state_file" ]]; then
  rm -f "$state_file"
  echo "FSM: All required skills satisfied, writes unblocked" >&2
fi

# --- Status transitions based on completed skill ---
args=$(echo "$input" | jq -r '.tool_input.args // empty')

if [[ -n "$args" ]]; then
  change_name="${args%% *}"
  change_dir="openspec/changes/${change_name}"
  openspec_yaml="${change_dir}/.openspec.yaml"

  if [[ -d "$change_dir" && -f "$openspec_yaml" ]]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"
    status_script="${PLUGIN_ROOT}/scripts/change_status.sh"

    case "$skill" in
      opsx:continue|openspec-continue-change)
        # specs-status: new -> draft (artifact creation moves out of new)
        current=$("$status_script" read "$change_dir" specs-status)
        if [[ "$current" == "new" ]]; then
          "$status_script" write "$change_dir" specs-status draft
          echo "Status: specs-status transitioned new → draft" >&2
        fi
        ;;
      implement-change|tokamak:implement-change)
        # code-status: ready -> in-progress (only if currently ready)
        current=$("$status_script" read "$change_dir" code-status)
        if [[ "$current" == "ready" ]]; then
          "$status_script" write "$change_dir" code-status in-progress
          echo "Status: code-status transitioned ready → in-progress" >&2
        fi
        ;;
      merge-change|tokamak:merge-change)
        # specs-status: ratified -> merging (only if currently ratified)
        current=$("$status_script" read "$change_dir" specs-status)
        if [[ "$current" == "ratified" ]]; then
          "$status_script" write "$change_dir" specs-status merging
          echo "Status: specs-status transitioned ratified → merging" >&2
        fi
        ;;
    esac
  fi
fi

echo '{"continue": true}'
