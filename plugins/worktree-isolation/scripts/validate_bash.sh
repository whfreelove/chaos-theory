#!/bin/bash
# Worktree Isolation Plugin - Bash Command Validator
# Validates Bash commands to prevent escaping worktree boundaries

input=$(cat)
CWD=$(echo "$input" | jq -r '.cwd // empty')

# Fail closed if we can't parse input
if [[ -z "$CWD" ]]; then
  echo "ERROR: Could not determine working directory from hook input"
  exit 1
fi

# Find worktree root - supports both git worktrees and jujutsu workspaces
# Git worktrees: .git is a FILE containing "gitdir: /path/to/main/.git/worktrees/name"
# Jujutsu workspaces: .jj/repo is a FILE containing "/path/to/main/.jj/repo"
find_worktree_root() {
  local dir="$1"
  while [[ "$dir" != "/" ]]; do
    # Check for git worktree (.git file, not directory)
    if [[ -f "$dir/.git" ]]; then
      echo "git:$dir"
      return 0
    fi
    # Check for jujutsu workspace (.jj/repo file, not directory)
    if [[ -f "$dir/.jj/repo" ]]; then
      echo "jj:$dir"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  return 1
}

WORKTREE_INFO=$(find_worktree_root "$CWD")

# Not a worktree/workspace, allow everything
if [[ -z "$WORKTREE_INFO" ]]; then
  exit 0
fi

# Extract worktree type and base
WORKTREE_TYPE="${WORKTREE_INFO%%:*}"
WORKTREE_BASE="${WORKTREE_INFO#*:}"

# Extract project root based on worktree type
if [[ "$WORKTREE_TYPE" == "git" ]]; then
  GITDIR=$(grep "^gitdir:" "$WORKTREE_BASE/.git" | cut -d' ' -f2-)
  PROJECT_ROOT=$(echo "$GITDIR" | sed 's|/.git/worktrees/.*||')
elif [[ "$WORKTREE_TYPE" == "jj" ]]; then
  MAIN_REPO=$(cat "$WORKTREE_BASE/.jj/repo")
  PROJECT_ROOT=$(echo "$MAIN_REPO" | sed 's|/.jj/repo$||')
fi

# Extract Bash command
PARAMS=$(echo "$input" | jq -r '.parameters // {}')
BASH_CMD=$(echo "$PARAMS" | jq -r '.command // empty')

if [[ -z "$BASH_CMD" ]]; then
  exit 0
fi

# Check for forbidden patterns
VIOLATION=""

# Check for parent directory traversal (..)
# Catches: ../ or .." or .. followed by space or end of string
DOTDOT_PATTERN='\.\.(/|"|[[:space:]]|$)'
if [[ "$BASH_CMD" =~ $DOTDOT_PATTERN ]]; then
  VIOLATION="Parent directory traversal (..) detected in command"
fi

# Check for absolute paths to project root
if [[ "$BASH_CMD" =~ $PROJECT_ROOT && "$BASH_CMD" != *"$WORKTREE_BASE"* ]]; then
  VIOLATION="Absolute path to project root detected: $PROJECT_ROOT"
fi

# Check for tilde expansion that could escape worktree
TILDE_PATTERN='~/'
if [[ "$BASH_CMD" =~ $TILDE_PATTERN ]]; then
  # Expand tilde to check where the path resolves
  EXPANDED_CHECK=$(echo "$BASH_CMD" | sed "s|~/|$HOME/|g")
  # Block if expanded path is NOT within the worktree
  if [[ "$EXPANDED_CHECK" != *"$WORKTREE_BASE"* ]]; then
    VIOLATION="Tilde path (~/) that expands outside worktree detected"
  fi
fi

# Check for common file access commands with parent traversal
if [[ "$BASH_CMD" =~ (cat|less|head|tail|grep|find|ls|cp|mv|rm|touch|mkdir|vim|nano|emacs)[[:space:]]+.*\.\. ]]; then
  VIOLATION="File access command with parent directory traversal detected"
fi

# If violation found, block it
if [[ -n "$VIOLATION" ]]; then
  cat <<EOF
<system-reminder>
ERROR: Bash command blocked (worktree isolation)

Command: $BASH_CMD
Violation: $VIOLATION

You are working in a git worktree and cannot execute commands that access files outside: $WORKTREE_BASE/

FORBIDDEN patterns in Bash commands:
- Parent traversal: cd .., cat ../../file, ls ../..
- Absolute paths to project root: cat $PROJECT_ROOT/file
- Tilde paths outside worktree: cat ~/path/to/project/file

ALLOWED:
- Commands operating within worktree: ls ./src, cat config/loader.py

If you need to run this command, ensure all paths stay within: $WORKTREE_BASE/
</system-reminder>
EOF
  exit 1
fi

exit 0
