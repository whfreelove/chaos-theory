#!/bin/bash
# Worktree Isolation Plugin - File Path Validator
# Validates file operation paths for Read, Write, Edit, MultiEdit, Glob, Grep, LS, NotebookEdit, NotebookRead

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

# Extract tool and parameters
TOOL=$(echo "$input" | jq -r '.tool // empty')
PARAMS=$(echo "$input" | jq -r '.parameters // {}')

# Get path based on tool type
PATH_TO_CHECK=""
IS_SEARCH_TOOL=false
case "$TOOL" in
"Read" | "Write" | "Edit" | "MultiEdit")
  PATH_TO_CHECK=$(echo "$PARAMS" | jq -r '.file_path // empty')
  ;;
"NotebookEdit" | "NotebookRead")
  PATH_TO_CHECK=$(echo "$PARAMS" | jq -r '.notebook_path // empty')
  ;;
"Glob" | "Grep" | "LS" | "Search")
  PATH_TO_CHECK=$(echo "$PARAMS" | jq -r '.path // empty')
  IS_SEARCH_TOOL=true
  ;;
esac

# For search tools without explicit path, they default to CWD
# We need to validate CWD is within worktree bounds
if [[ -z "$PATH_TO_CHECK" ]]; then
  if [[ "$IS_SEARCH_TOOL" == true ]]; then
    # Search tools without path use CWD - validate it's in worktree
    if [[ "$CWD" != "$WORKTREE_BASE"* ]]; then
      cat <<EOF
<system-reminder>
ERROR: Search operation denied (worktree isolation)

Tool: $TOOL
Working directory: $CWD

Search tools must operate within the worktree: $WORKTREE_BASE/

You cannot search from parent directories, home, or root.
</system-reminder>
EOF
      exit 1
    fi
  fi
  # File-based tools with no path - allow (will fail naturally)
  exit 0
fi

# Allow access to .claude/plans (global plan files used by Claude Code)
if [[ "$PATH_TO_CHECK" == *".claude/plans"* ]]; then
  exit 0
fi

# Block explicit escape attempts via ~ or absolute paths outside worktree
if [[ "$PATH_TO_CHECK" == "~"* ]]; then
  EXPANDED_PATH="${PATH_TO_CHECK/#\~/$HOME}"
  if [[ "$EXPANDED_PATH" != "$WORKTREE_BASE"* ]]; then
    cat <<EOF
<system-reminder>
ERROR: Path access denied (worktree isolation)

Attempted path: $PATH_TO_CHECK (expands to $EXPANDED_PATH)

Home directory paths (~) outside the worktree are not allowed.
You must stay within: $WORKTREE_BASE/
</system-reminder>
EOF
    exit 1
  fi
fi

# Block root-level absolute paths that could escape
if [[ "$PATH_TO_CHECK" == /* && "$PATH_TO_CHECK" != "$WORKTREE_BASE"* ]]; then
  cat <<EOF
<system-reminder>
ERROR: Path access denied (worktree isolation)

Attempted path: $PATH_TO_CHECK

Absolute paths must be within the worktree: $WORKTREE_BASE/

You cannot access:
- Project root: $PROJECT_ROOT/
- Home directory: $HOME/
- System paths: /etc, /tmp, /var, etc.
</system-reminder>
EOF
  exit 1
fi

# Resolve to absolute path
if [[ "$PATH_TO_CHECK" = /* ]]; then
  ABS_PATH="$PATH_TO_CHECK"
else
  # Try realpath first for proper normalization
  ABS_PATH="$(cd "$CWD" && realpath "$PATH_TO_CHECK" 2>/dev/null)"

  # If realpath fails and path contains .., fail closed
  if [[ -z "$ABS_PATH" ]]; then
    if [[ "$PATH_TO_CHECK" == *".."* ]]; then
      echo "ERROR: Cannot resolve path with parent traversal (..) - blocking for safety"
      exit 1
    fi
    # Simple concatenation for non-traversal paths that don't exist yet
    ABS_PATH="$CWD/$PATH_TO_CHECK"
  fi
fi

# Check if path escapes worktree
if [[ "$ABS_PATH" != "$WORKTREE_BASE"* ]]; then
  cat <<EOF
<system-reminder>
ERROR: Path access denied (worktree isolation)

Attempted path: $PATH_TO_CHECK
Resolved to: $ABS_PATH

You are working in a git worktree and cannot access files outside: $WORKTREE_BASE/

FORBIDDEN patterns:
- Parent directory traversal: ../../../file
- Absolute paths to project root: $PROJECT_ROOT/

If you need a file, it must exist within the current worktree.
</system-reminder>
EOF
  exit 1
fi

exit 0
