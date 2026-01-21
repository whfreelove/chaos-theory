#!/bin/bash
# Worktree Isolation Plugin - Session Start Hook
# Displays isolation warning when working in any git worktree

input=$(cat)
CWD=$(echo "$input" | jq -r '.cwd // empty')

# Exit gracefully if no CWD
if [[ -z "$CWD" ]]; then
    exit 0
fi

# Find worktree root - supports both git worktrees and jujutsu workspaces
# Git worktrees: .git is a FILE containing "gitdir: /path/to/main/.git/worktrees/name"
# Jujutsu workspaces: .jj/repo is a FILE containing "/path/to/main/.jj/repo"
find_worktree_root() {
    local dir="$1"
    [[ -z "$dir" ]] && return 1
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

if [[ -n "$WORKTREE_INFO" ]]; then
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

    cat <<EOF
<system-reminder>
WORKTREE ISOLATION ACTIVE

Current worktree: $WORKTREE_BASE
Project root: $PROJECT_ROOT

**CRITICAL RESTRICTIONS:**
- You MUST NOT access any files outside: $WORKTREE_BASE/
- You MUST NOT use paths containing \`..\` that navigate to parent directories
- You MUST NOT use absolute paths pointing to project root: $PROJECT_ROOT
- You MUST NOT access other worktrees

**ALLOWED:**
- Any path within: $WORKTREE_BASE/
- Relative paths without \`..\`: \`./src/config/loader.py\`

**FORBIDDEN:**
- Parent traversal: \`../../.claude/settings.json\`
- Absolute project root: \`$PROJECT_ROOT/README.md\`
- Other worktrees or sibling directories

**ENFORCEMENT:**
PreToolUse hooks will BLOCK file operations and Bash commands that violate these restrictions.
</system-reminder>
EOF
fi

exit 0
