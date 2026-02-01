#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"
TARGET_DIR="openspec/schemas"

FORCE=false
if [[ "$1" == "--force" ]]; then
    FORCE=true
fi

# Check for existing schemas (skip if --force)
if [ "$FORCE" = false ] && [ -d "$TARGET_DIR" ] && [ "$(ls -A "$TARGET_DIR" 2>/dev/null)" ]; then
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

# Copy schemas
mkdir -p "$TARGET_DIR"
cp -r "$PLUGIN_ROOT/openspec/schemas/chaos-theory" "$TARGET_DIR/"

# Report results
echo "Copied schemas to $TARGET_DIR/chaos-theory/"
find "$TARGET_DIR" -type f
echo ""
echo "Next: Run /opsx:new to start a new change."
