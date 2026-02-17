#!/bin/bash
# FSM Hook: Block writes to openspec/changes/* if skills not invoked
# Triggered: PreToolUse on Write, Edit, NotebookEdit
# Action: If state file exists and non-empty, block with error

set -euo pipefail

input=$(cat)

# Get the file path being written
tool=$(echo "$input" | jq -r '.tool // empty')
file_path=""

case "$tool" in
  "Write"|"Edit")
    file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')
    ;;
  "NotebookEdit")
    file_path=$(echo "$input" | jq -r '.tool_input.notebook_path // empty')
    ;;
esac

# Only check writes to openspec/changes/
if [[ "$file_path" != *"openspec/changes/"* ]]; then
  exit 0
fi

# Get session ID for state file
session_id=$(echo "$input" | jq -r '.session_id // "default"')
state_file="/tmp/fsm_ct_${session_id}.txt"

# If no state file or empty, allow write
if [[ ! -f "$state_file" ]] || [[ ! -s "$state_file" ]]; then
  exit 0
fi

# Read pending skills
pending_skills=$(cat "$state_file" | sort -u)
skill_count=$(echo "$pending_skills" | wc -l | tr -d ' ')

# Format skill list for display
skill_list=$(echo "$pending_skills" | sed 's/^/  - /')

# Block the write with informative error
cat <<EOF
<system-reminder>
BLOCKED: Required skill(s) not invoked

You are attempting to write to: $file_path

Before writing OpenSpec change artifacts, you must invoke the following skill(s):
$skill_list

These skills were specified by \`openspec instructions\` via FSM:use_skill directives.

To proceed:
1. Invoke each required skill using the Skill tool
2. Follow the skill's guidance
3. Then retry this write

This ensures change artifacts follow the project's specification standards.
</system-reminder>
EOF

exit 1
