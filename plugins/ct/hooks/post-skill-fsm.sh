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

echo '{"continue": true}'
