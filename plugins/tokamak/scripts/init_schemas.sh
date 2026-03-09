#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$SCRIPT_DIR")}"
TARGET_DIR="openspec/schemas"

MODE="interactive"
if [[ "$1" == "--force" ]]; then
  MODE="force"
elif [[ "$1" == "--auto" ]]; then
  MODE="auto"
fi

# --auto: SessionStart hook mode. Read cwd from stdin, skip if schemas exist.
if [[ "$MODE" == "auto" ]]; then
  input=$(cat)
  CWD=$(echo "$input" | jq -r '.cwd // empty')
  [[ -z "$CWD" ]] && exit 0

  # Only auto-init in projects that already have an openspec/ directory
  [ ! -d "$CWD/openspec" ] && exit 0

  if [ -d "$CWD/$TARGET_DIR/chaos-theory" ]; then
    # Schemas exist — check for version mismatch
    PLUGIN_SCHEMA="$PLUGIN_ROOT/openspec/schemas/chaos-theory/schema.yaml"
    INSTALLED_SCHEMA="$CWD/$TARGET_DIR/chaos-theory/schema.yaml"

    if [ ! -f "$PLUGIN_SCHEMA" ] || [ ! -f "$INSTALLED_SCHEMA" ]; then
      MISSING=""
      [ ! -f "$PLUGIN_SCHEMA" ] && MISSING="$PLUGIN_SCHEMA"
      [ ! -f "$INSTALLED_SCHEMA" ] && MISSING="${MISSING:+$MISSING, }$INSTALLED_SCHEMA"
      cat <<EOF
<system-reminder>
Schema version check skipped: ${MISSING} not found.
</system-reminder>
EOF
      exit 0
    fi

    PLUGIN_VER=$(grep '^version:' "$PLUGIN_SCHEMA" | awk '{print $2}')
    INSTALLED_VER=$(grep '^version:' "$INSTALLED_SCHEMA" | awk '{print $2}')

    if [ -z "$PLUGIN_VER" ] || [ -z "$INSTALLED_VER" ]; then
      UNPARSED=""
      [ -z "$PLUGIN_VER" ] && UNPARSED="$PLUGIN_SCHEMA"
      [ -z "$INSTALLED_VER" ] && UNPARSED="${UNPARSED:+$UNPARSED, }$INSTALLED_SCHEMA"
      cat <<EOF
<system-reminder>
Schema version check skipped: could not read version from ${UNPARSED}.
</system-reminder>
EOF
      exit 0
    fi

    if [ "$PLUGIN_VER" != "$INSTALLED_VER" ]; then
      cat <<EOF
<system-reminder>
Schema update available: chaos-theory v${INSTALLED_VER} → v${PLUGIN_VER}. Run '/init-schemas' to upgrade.
</system-reminder>
EOF
    fi

    exit 0
  fi

  mkdir -p "$CWD/$TARGET_DIR"
  for schema in "$PLUGIN_ROOT/openspec/schemas"/*/; do
    [ -d "$schema" ] && cp -r "${schema%/}" "$CWD/$TARGET_DIR/"
  done

  SCHEMA_NAMES=$(ls -1 "$CWD/$TARGET_DIR" | tr '\n' ', ' | sed 's/,$//')
  cat <<EOF
<system-reminder>
Initialized OpenSpec schemas at $TARGET_DIR/ ($SCHEMA_NAMES). Run '/new-change <change-name>' to start a change.
</system-reminder>
EOF
  exit 0
fi

# --force / interactive: called from skill or command line
if [[ "$MODE" == "interactive" ]] && [ -d "$TARGET_DIR" ] && [ "$(ls -A "$TARGET_DIR" 2>/dev/null)" ]; then
  echo "Existing schemas detected at $TARGET_DIR/"
  read -p "Overwrite? [y/N] " confirm
  if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Cancelled. Schemas unchanged."
    exit 0
  fi
fi

# Remove existing if present
if [ -d "$TARGET_DIR" ]; then
  rm -rf "$TARGET_DIR"
fi

# Copy all schemas
mkdir -p "$TARGET_DIR"
for schema in "$PLUGIN_ROOT/openspec/schemas"/*/; do
  [ -d "$schema" ] && cp -r "${schema%/}" "$TARGET_DIR/"
done

# Report results
for schema in "$TARGET_DIR"/*/; do
  echo "Copied schemas to $schema"
done
find "$TARGET_DIR" -type f
echo ""
echo "Next: Run '/new-change <change-name>' to start a change."
