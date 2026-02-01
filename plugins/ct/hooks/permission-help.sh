#!/bin/bash
# PermissionRequest hook: Auto-allow ct plugin scripts
# Verifies scripts are actually within the plugin directory before allowing

# Read JSON input from stdin
INPUT=$(cat)

# Extract tool_input.command from JSON
COMMAND=$(echo "$INPUT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('tool_input', {}).get('command', ''))" 2>/dev/null)

# Extract script path from command (handles both python3 and direct execution)
SCRIPT_PATH=$(echo "$COMMAND" | grep -oE '[^ ]+(select_critics\.py|next_gap\.sh|init-schemas\.sh)' | head -1)

if [[ -n "$SCRIPT_PATH" ]]; then
  # Resolve to absolute path
  REAL_PATH=$(realpath "$SCRIPT_PATH" 2>/dev/null)
  PLUGIN_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/scripts"

  # Verify script is within plugin's scripts directory
  if [[ -n "$REAL_PATH" && "$REAL_PATH" == "${PLUGIN_SCRIPTS}/"* ]]; then
    # Safe to allow - script is within our plugin
    cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow"
    }
  }
}
EOF
    exit 0
  fi
fi

# No decision = continue with normal permission prompt
exit 0
