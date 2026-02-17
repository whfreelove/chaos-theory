#!/bin/bash
# Utility: Read, write, and check status fields in .openspec.yaml
# Usage:
#   change_status.sh read  <change-dir> <field>
#   change_status.sh write <change-dir> <field> <value>
#   change_status.sh check <change-dir> <field> <allowed-pattern>
#
# Exit codes:
#   read:  0 always (prints value, empty if missing)
#   write: 0 on success, 1 on error
#   check: 0 if value matches pattern, 1 if not (prints current value)

set -uo pipefail

usage() {
  echo "Usage: $0 {read|write|check} <change-dir> <field> [value|pattern]" >&2
  exit 1
}

[[ $# -lt 3 ]] && usage

action="$1"
change_dir="$2"
field="$3"
openspec_yaml="${change_dir}/.openspec.yaml"

case "$action" in
  read)
    if [[ ! -f "$openspec_yaml" ]]; then
      echo ""
      exit 0
    fi
    # Extract value after "field: " (empty if not found)
    value=$(grep "^${field}:" "$openspec_yaml" 2>/dev/null | head -1 | sed "s/^${field}: *//" || true)
    echo "$value"
    ;;

  write)
    [[ $# -lt 4 ]] && usage
    value="$4"

    if [[ ! -f "$openspec_yaml" ]]; then
      echo "Error: ${openspec_yaml} not found" >&2
      exit 1
    fi

    if grep -q "^${field}:" "$openspec_yaml" 2>/dev/null; then
      # Update existing field (portable: no sed -i)
      temp=$(mktemp)
      sed "s/^${field}:.*/${field}: ${value}/" "$openspec_yaml" > "$temp" && mv "$temp" "$openspec_yaml"
    else
      # Append new field
      echo "${field}: ${value}" >> "$openspec_yaml"
    fi
    ;;

  check)
    [[ $# -lt 4 ]] && usage
    pattern="$4"

    if [[ ! -f "$openspec_yaml" ]]; then
      echo ""
      exit 1
    fi

    current=$(grep "^${field}:" "$openspec_yaml" 2>/dev/null | head -1 | sed "s/^${field}: *//" || true)

    # Empty value = permissive (legacy changes without status fields)
    if [[ -z "$current" ]]; then
      exit 0
    fi

    # Check if current value matches allowed pattern (extended regex)
    if echo "$current" | grep -qE "^(${pattern})$"; then
      exit 0
    else
      echo "$current"
      exit 1
    fi
    ;;

  *)
    usage
    ;;
esac
