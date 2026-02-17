#!/bin/bash
# FSM Hook: Capture required skills from openspec instructions output
# Triggered: PostToolUse on Bash
# Action: Parse stdout for FSM:use_skill:`X` patterns, append to state file

set -euo pipefail

input=$(cat)

# Extract command from tool input
command=$(echo "$input" | jq -r '.tool_input.command // empty')

# Only process if command contains "openspec instructions"
if [[ "$command" != *"openspec instructions"* && "$command" != *"openspec "* ]]; then
  echo '{"continue": true}'
  exit 0
fi

# Get session ID for state file naming
session_id=$(echo "$input" | jq -r '.session_id // "default"')
state_file="/tmp/fsm_ct_${session_id}.txt"

# Extract stdout from tool result
stdout=$(echo "$input" | jq -r '.tool_result.stdout // empty')

if [[ -z "$stdout" ]]; then
  echo '{"continue": true}'
  exit 0
fi

# Parse FSM:use_skill:`skill-name` patterns from stdout
# Pattern matches: FSM:use_skill:`tokamak:writing-functional-specs`
# Captures: tokamak:writing-functional-specs
skills=$(echo "$stdout" | grep -oE 'FSM:use_skill:`[^`]+`' | sed 's/FSM:use_skill:`//g; s/`$//g' || true)

if [[ -n "$skills" ]]; then
  # Append each skill to state file (accumulate, don't reset)
  echo "$skills" >> "$state_file"

  # Log for debugging (to stderr so it doesn't interfere with JSON output)
  skill_count=$(echo "$skills" | wc -l | tr -d ' ')
  echo "FSM: Captured $skill_count required skill(s) -> $state_file" >&2
fi

echo '{"continue": true}'
