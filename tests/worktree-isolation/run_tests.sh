#!/bin/bash
# Worktree Isolation Plugin - Test Suite
# Run: ./tests/worktree-isolation/run_tests.sh

set -uo pipefail
# Note: Not using set -e because we need tests to continue after failures

PLUGIN_DIR="$(cd "$(dirname "$0")/../../plugins/worktree-isolation" && pwd)"
PASS=0
FAIL=0
SKIP=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Check dependencies
check_deps() {
    if ! command -v jq &>/dev/null; then
        echo -e "${RED}Error: jq is required but not installed${NC}"
        exit 1
    fi
}

# Setup test worktree structure (git worktrees)
setup_worktree() {
    local test_dir="$(mktemp -d)"

    # Create main repo with .git directory
    mkdir -p "$test_dir/main-repo/.git/worktrees/test-worktree"

    # Create worktree with .git file pointing to main
    mkdir -p "$test_dir/worktree/src/config"
    echo "gitdir: $test_dir/main-repo/.git/worktrees/test-worktree" > "$test_dir/worktree/.git"

    # Create a non-worktree directory (regular repo)
    mkdir -p "$test_dir/regular-repo/.git/objects"

    # Create jujutsu main repo with .jj/repo directory
    mkdir -p "$test_dir/jj-main/.jj/repo"

    # Create jujutsu workspace with .jj/repo file pointing to main
    mkdir -p "$test_dir/jj-workspace/src/config"
    mkdir -p "$test_dir/jj-workspace/.jj"
    echo "$test_dir/jj-main/.jj/repo" > "$test_dir/jj-workspace/.jj/repo"

    echo "$test_dir"
}

cleanup() {
    if [[ -n "${TEST_DIR:-}" ]]; then
        rm -rf "$TEST_DIR"
    fi
}

trap cleanup EXIT

# Assertion helpers
assert_exit() {
    local expected=$1 actual=$2 name=$3
    if [[ "$actual" -eq "$expected" ]]; then
        echo -e "${GREEN}✓${NC} $name"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $name (expected exit $expected, got $actual)"
        ((FAIL++))
    fi
}

assert_output_contains() {
    local pattern=$1 output=$2 name=$3
    if [[ "$output" == *"$pattern"* ]]; then
        echo -e "${GREEN}✓${NC} $name"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $name (output missing: $pattern)"
        ((FAIL++))
    fi
}

skip_test() {
    local name=$1 reason=$2
    echo -e "${YELLOW}○${NC} $name (skipped: $reason)"
    ((SKIP++))
}

# Run a hook script with input
run_hook() {
    local script=$1 input=$2
    echo "$input" | "$PLUGIN_DIR/scripts/$script" 2>&1
}

run_hook_status() {
    local script=$1 input=$2
    echo "$input" | "$PLUGIN_DIR/scripts/$script" >/dev/null 2>&1
    echo $?
}

#############################################
# TEST SUITE: validate_file_path.sh
#############################################

test_file_path_validation() {
    echo ""
    echo "=== validate_file_path.sh ==="
    echo ""

    local script="validate_file_path.sh"

    # Test: Valid relative path within worktree
    local input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Read","parameters":{"file_path":"./src/config/loader.py"}}'
    local status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" "Valid relative path allowed"

    # Test: Parent traversal blocked
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Read","parameters":{"file_path":"../../main-repo/file.txt"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "Parent traversal (..) blocked"

    # Test: Absolute path to project root blocked
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Write","parameters":{"file_path":"'"$TEST_DIR/main-repo"'/README.md"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "Absolute path outside worktree blocked"

    # Test: Absolute path within worktree allowed
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Edit","parameters":{"file_path":"'"$TEST_DIR/worktree"'/src/file.py"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" "Absolute path within worktree allowed"

    # Test: Empty path allowed (no path to validate)
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Read","parameters":{}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" "Empty path allowed"

    # Test: Not in worktree - allows everything
    input='{"cwd":"'"$TEST_DIR/regular-repo"'","tool":"Read","parameters":{"file_path":"../../etc/passwd"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" "Non-worktree allows all paths"

    # Test: Missing CWD fails closed
    input='{"tool":"Read","parameters":{"file_path":"./file.py"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "Missing CWD fails closed"

    # Test: Glob tool with path
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Glob","parameters":{"path":"../../"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "Glob with parent traversal blocked"

    # Test: Grep tool with path (use absolute path within worktree)
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Grep","parameters":{"path":"'"$TEST_DIR/worktree/src"'"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" "Grep within worktree allowed"

    # Test: MultiEdit tool
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"MultiEdit","parameters":{"file_path":"../outside.py"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "MultiEdit parent traversal blocked"

    # Test: NotebookEdit tool
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"NotebookEdit","parameters":{"notebook_path":"./notebook.ipynb"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" "NotebookEdit within worktree allowed"

    # Test: LS tool
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"LS","parameters":{"path":"../../"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "LS parent traversal blocked"

    # Test: Error message contains useful info
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Read","parameters":{"file_path":"'"$TEST_DIR/main-repo"'/secret.txt"}}'
    local output=$(run_hook "$script" "$input")
    assert_output_contains "Path access denied" "$output" "Error message contains 'Path access denied'"
    assert_output_contains "worktree isolation" "$output" "Error message mentions isolation"

    # Test: Search tool with valid path within worktree
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Search","parameters":{"path":"'"$TEST_DIR/worktree/src"'"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" "Search within worktree allowed"

    # Test: Search tool with parent traversal blocked
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Search","parameters":{"path":"../../"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "Search with parent traversal blocked"

    # Test: Search tool with absolute path outside worktree blocked
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Search","parameters":{"path":"'"$TEST_DIR/main-repo"'"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "Search with absolute path outside worktree blocked"

    # Test: Search tool without path (defaults to CWD in worktree) - allowed
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Search","parameters":{}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" "Search without path in worktree CWD allowed"

    # Test: Glob without path (defaults to CWD in worktree) - allowed
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Glob","parameters":{"pattern":"*.py"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" "Glob without path in worktree CWD allowed"

    # Test: Grep without path (defaults to CWD in worktree) - allowed
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Grep","parameters":{"pattern":"TODO"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" "Grep without path in worktree CWD allowed"

    # Test: Tilde path to home directory blocked
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Read","parameters":{"file_path":"~/.bashrc"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "Tilde path (~/.bashrc) blocked"

    # Test: Tilde path error message
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Read","parameters":{"file_path":"~/.ssh/config"}}'
    output=$(run_hook "$script" "$input")
    assert_output_contains "Home directory paths" "$output" "Tilde error mentions home directory"

    # Test: Tilde with username blocked
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Read","parameters":{"file_path":"~/Documents/secret.txt"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "Tilde path (~/Documents) blocked"

    # Test: Root path blocked with clear message
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Read","parameters":{"file_path":"/etc/passwd"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "Root path (/etc/passwd) blocked"

    # Test: Absolute path error message lists forbidden areas
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Read","parameters":{"file_path":"/tmp/secret"}}'
    output=$(run_hook "$script" "$input")
    assert_output_contains "Absolute paths must be within the worktree" "$output" "Absolute path error is clear"

    # Test: Home directory absolute path blocked
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Read","parameters":{"file_path":"'"$HOME"'/.gitconfig"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "Home directory absolute path blocked"

    # Test: Var path blocked
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Write","parameters":{"file_path":"/var/log/app.log"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "Var path (/var/log) blocked"

    # Test: Search tool from main repo (outside worktree) with worktree file blocked
    # Note: This simulates an agent somehow having CWD outside the worktree
    input='{"cwd":"'"$TEST_DIR/main-repo"'","tool":"Search","parameters":{}}'
    status=$(run_hook_status "$script" "$input")
    # main-repo has .git directory (not file), so it's not a worktree - should allow
    assert_exit 0 "$status" "Search from non-worktree CWD allowed (no isolation)"

    # Test: .claude/plans absolute path allowed (plan mode files)
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Write","parameters":{"file_path":"'"$HOME"'/.claude/plans/test-plan.md"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" ".claude/plans absolute path allowed"

    # Test: .claude/plans tilde path allowed
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Read","parameters":{"file_path":"~/.claude/plans/test-plan.md"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" ".claude/plans tilde path allowed"

    # Test: .claude/plans Edit allowed
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Edit","parameters":{"file_path":"'"$HOME"'/.claude/plans/some-plan.md"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" ".claude/plans Edit allowed"

    # Test: .claude/plans directory path (no trailing slash) allowed
    input='{"cwd":"'"$TEST_DIR/worktree"'","tool":"Read","parameters":{"file_path":"'"$HOME"'/.claude/plans"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" ".claude/plans directory path allowed"
}

#############################################
# TEST SUITE: validate_bash.sh
#############################################

test_bash_validation() {
    echo ""
    echo "=== validate_bash.sh ==="
    echo ""

    local script="validate_bash.sh"

    # Test: Safe command without paths
    local input='{"cwd":"'"$TEST_DIR/worktree"'","parameters":{"command":"git status"}}'
    local status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" "git status allowed"

    # Test: Safe command with worktree-relative path
    input='{"cwd":"'"$TEST_DIR/worktree"'","parameters":{"command":"ls ./src"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" "ls ./src allowed"

    # Test: cd .. blocked
    input='{"cwd":"'"$TEST_DIR/worktree"'","parameters":{"command":"cd .."}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "cd .. blocked"

    # Test: cd .. with continuation blocked
    input='{"cwd":"'"$TEST_DIR/worktree"'","parameters":{"command":"cd .. && ls"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "cd .. && ls blocked"

    # Test: cat with parent traversal blocked
    input='{"cwd":"'"$TEST_DIR/worktree"'","parameters":{"command":"cat ../../README.md"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "cat ../../file blocked"

    # Test: ls with parent traversal blocked
    input='{"cwd":"'"$TEST_DIR/worktree"'","parameters":{"command":"ls ../.."}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "ls ../.. blocked"

    # Test: Tilde path blocked (expands outside worktree)
    input='{"cwd":"'"$TEST_DIR/worktree"'","parameters":{"command":"cat ~/.bashrc"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "cat ~/.bashrc blocked"

    # Test: Absolute path to project root blocked
    input='{"cwd":"'"$TEST_DIR/worktree"'","parameters":{"command":"cat '"$TEST_DIR/main-repo"'/file.txt"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "Absolute path to main repo blocked"

    # Test: Empty command allowed
    input='{"cwd":"'"$TEST_DIR/worktree"'","parameters":{}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" "Empty command allowed"

    # Test: npm test allowed (no file paths)
    input='{"cwd":"'"$TEST_DIR/worktree"'","parameters":{"command":"npm test"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" "npm test allowed"

    # Test: Not in worktree - allows everything
    input='{"cwd":"'"$TEST_DIR/regular-repo"'","parameters":{"command":"cd .. && cat /etc/passwd"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" "Non-worktree allows all commands"

    # Test: Missing CWD fails closed
    input='{"parameters":{"command":"ls"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "Missing CWD fails closed"

    # Test: grep with parent path blocked
    input='{"cwd":"'"$TEST_DIR/worktree"'","parameters":{"command":"grep -r pattern ../.."}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "grep with .. blocked"

    # Test: find with parent path blocked
    input='{"cwd":"'"$TEST_DIR/worktree"'","parameters":{"command":"find .. -name \"*.py\""}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "find .. blocked"

    # Test: Error message contains command
    input='{"cwd":"'"$TEST_DIR/worktree"'","parameters":{"command":"cd .."}}'
    local output=$(run_hook "$script" "$input")
    assert_output_contains "Bash command blocked" "$output" "Error mentions 'Bash command blocked'"
    assert_output_contains "cd .." "$output" "Error shows the blocked command"
}

#############################################
# TEST SUITE: worktree_session_start.sh
#############################################

test_session_start() {
    echo ""
    echo "=== worktree_session_start.sh ==="
    echo ""

    local script="worktree_session_start.sh"

    # Test: Shows warning when in worktree
    local input='{"cwd":"'"$TEST_DIR/worktree"'"}'
    local output=$(run_hook "$script" "$input")
    local status=$?
    assert_exit 0 "$status" "Session start succeeds in worktree"
    assert_output_contains "WORKTREE ISOLATION ACTIVE" "$output" "Shows isolation warning"
    assert_output_contains "$TEST_DIR/worktree" "$output" "Shows worktree path"
    assert_output_contains "$TEST_DIR/main-repo" "$output" "Shows project root path"

    # Test: Silent when not in worktree
    input='{"cwd":"'"$TEST_DIR/regular-repo"'"}'
    output=$(run_hook "$script" "$input")
    status=$?
    assert_exit 0 "$status" "Session start succeeds in regular repo"
    if [[ -z "$output" ]]; then
        echo -e "${GREEN}✓${NC} No output for non-worktree"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} Should be silent for non-worktree (got: $output)"
        ((FAIL++))
    fi

    # Test: Silent when CWD missing (graceful handling)
    input='{}'
    output=$(run_hook "$script" "$input")
    status=$?
    assert_exit 0 "$status" "Session start handles missing CWD gracefully"
}

#############################################
# TEST SUITE: Jujutsu Workspace Support
#############################################

test_jj_workspace() {
    echo ""
    echo "=== Jujutsu Workspace Support ==="
    echo ""

    local script="validate_file_path.sh"

    # Test: jj workspace detected and file within workspace allowed
    local input='{"cwd":"'"$TEST_DIR/jj-workspace"'","tool":"Read","parameters":{"file_path":"./src/config/file.py"}}'
    local status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" "jj workspace: relative path allowed"

    # Test: jj workspace blocks absolute path to main repo
    input='{"cwd":"'"$TEST_DIR/jj-workspace"'","tool":"Read","parameters":{"file_path":"'"$TEST_DIR/jj-main"'/README.md"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "jj workspace: absolute path to main blocked"

    # Test: jj workspace blocks parent traversal
    input='{"cwd":"'"$TEST_DIR/jj-workspace"'","tool":"Read","parameters":{"file_path":"../../jj-main/file.txt"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "jj workspace: parent traversal blocked"

    # Test: jj workspace allows .claude/plans
    input='{"cwd":"'"$TEST_DIR/jj-workspace"'","tool":"Read","parameters":{"file_path":"'"$HOME"'/.claude/plans/test-plan.md"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" "jj workspace: .claude/plans allowed"

    # Test: jj workspace allows absolute path within workspace
    input='{"cwd":"'"$TEST_DIR/jj-workspace"'","tool":"Edit","parameters":{"file_path":"'"$TEST_DIR/jj-workspace"'/src/file.py"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" "jj workspace: absolute path within workspace allowed"

    # Test: jj main repo (not workspace) allows everything
    input='{"cwd":"'"$TEST_DIR/jj-main"'","tool":"Read","parameters":{"file_path":"../../etc/passwd"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" "jj main repo: no isolation (not a workspace)"

    # Test: jj workspace session start shows warning
    script="worktree_session_start.sh"
    input='{"cwd":"'"$TEST_DIR/jj-workspace"'"}'
    local output=$(run_hook "$script" "$input")
    status=$?
    assert_exit 0 "$status" "jj workspace: session start succeeds"
    assert_output_contains "WORKTREE ISOLATION ACTIVE" "$output" "jj workspace: shows isolation warning"
    assert_output_contains "$TEST_DIR/jj-workspace" "$output" "jj workspace: shows workspace path"
    assert_output_contains "$TEST_DIR/jj-main" "$output" "jj workspace: shows main repo path"

    # Test: jj workspace bash validation
    script="validate_bash.sh"
    input='{"cwd":"'"$TEST_DIR/jj-workspace"'","parameters":{"command":"cd .."}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 1 "$status" "jj workspace: cd .. blocked in bash"

    input='{"cwd":"'"$TEST_DIR/jj-workspace"'","parameters":{"command":"ls ./src"}}'
    status=$(run_hook_status "$script" "$input")
    assert_exit 0 "$status" "jj workspace: safe bash command allowed"
}

#############################################
# MAIN
#############################################

main() {
    echo "========================================"
    echo "Worktree Isolation Plugin - Test Suite"
    echo "========================================"

    check_deps

    TEST_DIR=$(setup_worktree)
    echo "Test directory: $TEST_DIR"

    # Make scripts executable
    chmod +x "$PLUGIN_DIR/scripts/"*.sh

    # Run test suites
    test_file_path_validation
    test_bash_validation
    test_session_start
    test_jj_workspace

    # Summary
    echo ""
    echo "========================================"
    echo "Results: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}, ${YELLOW}$SKIP skipped${NC}"
    echo "========================================"

    exit $FAIL
}

main "$@"
