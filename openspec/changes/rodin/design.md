## Context

Plan mode helps agents think before acting, but nothing validates that the agent honestly articulates its uncertainties. Agents may gloss over gaps internally without documenting them. An adversarial critic catches what the agent missed or minimized, and a validator ensures the agent's documented gaps cover the critic's findings.

## Goals / Non-Goals

**Goals:**
- Force agent to demonstrate gap awareness before exiting plan mode
- Use adversarial critic subagent to find gaps agent missed
- Validate that agent's gaps covers adversarial critic subagent's findings
- Opt-in via skill invocation

**Non-Goals:**
- Automatic assessment (user/agent must invoke skill)
- Complex logic in hooks
- External state files (all metadata embedded in plan file)

**Behavior:** Default blocks ExitPlanMode until assessment passes.

**Plan mode:** Claude Code's planning state (`permission_mode == "plan"`) where the agent creates an implementation plan before taking action. Plan file path is provided in system context. In plan mode, the agent can only modify the plan file.

## Dependencies

| Tool | Purpose | Rationale |
|------|---------|-----------|
| `jq` | Parse JSON input from Claude Code hooks | Claude Code hooks receive structured JSON via stdin. jq is the standard tool for JSON parsing in shell. Alternatives (grep/sed on JSON, Python) are fragile or heavier. |
| `sed` | Text extraction and in-place editing | POSIX standard, universally available |
| `grep` | Pattern matching and file discovery | POSIX standard, universally available |
| `shasum` | SHA-256 hash computation | POSIX standard, universally available (aliased to `sha256sum` on some Linux) |
| `date` | ISO 8601 timestamp generation | POSIX standard, universally available |

### Installation checks

**jq**
```bash
command -v jq >/dev/null 2>&1 || { echo "[RODIN] Error: jq required but not installed. Install via: brew install jq (macOS) or apt install jq (Linux)"; exit 1; }
```

**Note:** Standard POSIX utilities (`cut`, `head`, `echo`, `test`, `uname`) are assumed universally available and not individually documented. Only non-universal dependencies like `jq` require explicit documentation and installation checks.

## Decisions

### Shell vs Python for hooks
Current implementation uses Bash for hook scripts. Trade-offs:

**Shell (current):**
- Pros: Native to hook execution context, no additional runtime dependency
- Cons: Platform portability issues (sed -i syntax, realpath unavailability), limited error handling, fragile parsing

**Python (future consideration):**
- Pros: Built into macOS/Linux, better error handling, portable stdlib (os.path.realpath, json module), cleaner code
- Cons: Slightly heavier invocation, another language in codebase

**Decision:** MVP uses shell with targeted Python fallbacks (e.g., `python3 -c "..."` for realpath). Full Python rewrite planned for future to resolve accumulated portability issues. Shell portability quirks documented as they're discovered.

### Hook JSON schema stability assumption
Hooks assume JSON input fields like `.permission_mode`, `.session_id`, `.tool_input.file_path`, `.tool_response.filePath` are stable API contract from Claude Code. Defensive parsing strategy:
- Check for null/missing fields before using
- Exit silently on missing required fields (PostToolUse) or fail with clear error (PreToolUse)
- Log warnings for unexpected structure where appropriate
- Use fallback chains for fields with known variations (e.g., `.tool_input.file_path // .tool_response.filePath`)

Schema changes are a platform risk outside our control. If field names change, hooks will fail safely (exit silently or block with error). No version checking for MVP - accepted as platform dependency.

### Embedded metadata architecture
All rodin state lives in the plan file as HTML comments. No external files (gate.yml, gaps.md, session mappings). Benefits:
- Plan file is self-contained artifact
- No cleanup needed—state dies with plan file
- Agent can write gaps in plan mode (it's the plan file)
- Session discovery via grep for session marker

### Skill for orchestration, hook for enforcement
- Skill `/rodin:plan-gate` handles subagent orchestration via Task tool, user interaction
- Hook extracts embedded metadata and verifies verdict

### Skill uses Task tool for subagents
All subagents are invoked via Task tool. The skill instructs; the agent orchestrates.

- **Leakage detector (haiku)**: scans plan for gap-like phrases. Fast, cheap.
- **Critic (opus)**: receives plan content (excluding gaps block) via Task tool input, outputs findings in structured markdown. Needs depth for adversarial analysis. No file access—content passed directly to prevent gaps block leakage. Key prompt elements: (1) adversarial role, (2) focus on goals mismatches, implementation blockers, unstated assumptions, unmitigated risks, (3) structured output format, (4) explicit "no issues" declaration if none found.
- **Validator (haiku)**: receives gaps + critic's findings, determines coverage. Mechanical comparison.

**Critic output format:**
```markdown
### FINDING-1: <title>
- **Severity**: high|medium|low
- **Description**: <explanation of the gap/issue>

### FINDING-2: <title>
...
```

Critic assigns severity based on impact: HIGH = blocks implementation, MEDIUM = degrades functionality, LOW = minor issue. If critic finds no issues, it must explicitly declare `### NO ISSUES FOUND` rather than returning empty output.

**Validator output format:**
```markdown
### VERDICT: PASS
**Reason**: All HIGH and MEDIUM findings covered by documented gaps.

### VERDICT: FAIL
**Reason**: <list of uncovered findings>
```

Critic findings returned via Task tool to the orchestrating agent, who then passes them to validator via Task tool prompt. This is explicit agent orchestration—the agent reads the critic's output and includes it in the validator's input prompt. No automatic handoff or intermediate file.
On subagent failure (timeout, crash, unparseable output): retry once, then fail closed.

**Parseable output detection (for retry decisions):**
- **Critic**: Output is parseable if it matches either:
  - `/^### FINDING-\d+:/m` (one or more findings), or
  - `/^### NO ISSUES FOUND$/m` (explicit no-issues declaration)
  - If neither pattern matches, output is unparseable → retry
- **Validator**: Output is parseable if it matches:
  - `/^### VERDICT: (PASS|FAIL)$/m`
  - If pattern doesn't match, output is unparseable → retry

These regex patterns are the minimum required to determine parseability. Full output parsing extracts additional fields (severity, reason) but parseability check only verifies the structural markers exist.

### Use actual plan mode file
The skill works with the plan file Claude Code already creates at `~/.claude/plans/<slug>.md`.

### Critic isolation (defense-in-depth)
Gaps block is hidden from critic to prevent accidental priming. Critic should find gaps independently, not confirm gaps the agent already documented. This ensures critic catches what the agent missed or minimized, rather than anchoring on the agent's framing.

**Soft constraint**: Skill extracts plan content (excluding `<!-- rodin:gaps:start -->` to `<!-- rodin:gaps:end -->`) and passes only that content to critic via Task tool input. However, critic subagent has full tool access and could read the plan file directly. If it does, gaps block is visible. This is actually *weaker* isolation than a separate gaps.md file (which the critic would have to know to look for). Accepted trade-off: the benefits of embedded architecture (no external state, plan mode compatibility) outweigh the slightly weaker isolation. Realistic threat remains accidental priming via prompt, not adversarial critic behavior.

### Hash maintenance by PostToolUse hook
Hashes are computed by the PostToolUse hook (deterministic shell code), never by LLMs:
- Plan content = file content excluding all `<!-- rodin:* -->` blocks (after sed extraction removes single-line rodin comments AND multi-line gaps blocks)
- Gaps content = content between `<!-- rodin:gaps:start -->` and `<!-- rodin:gaps:end -->` (markers excluded)
- On any edit, hook recomputes hashes and resets validation to require fresh assessment

**Hash computation reference fixture** (for verification):
```
# Input file content (before rodin markers):
## Goals
- Ship the feature

## Implementation
- Step 1

# Expected plan hash (SHA-256 of content above):
# echo "## Goals\n- Ship the feature\n\n## Implementation\n- Step 1" | shasum -a 256
# → e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```
Note: Actual hash depends on exact whitespace. Test fixtures in `tests/fixtures/plans/` provide authoritative reference values.

### Opt-in at two levels
1. Plugin installation: enables the hook
2. Skill invocation: triggers assessment

If user never runs `/rodin:plan-gate`, no session marker exists, hook blocks exit (assessment required once plugin installed).
If user runs skill but plan/gaps changed after, hook detects hash mismatch and blocks.

**Acknowledged trade-off:** This opt-in design has circularity: agents that exit prematurely won't invoke the skill anyway. This is intentional—forcing assessment would be intrusive and break workflows. The plugin targets agents/users who *want* gap discipline, not those who need to be forced into it.

### Leakage detection (haiku subagent)
Scans plan for gap-like phrases before critic runs.
Uses keyword threshold: only acts if 3+ distinct gap-like phrases detected.
Single phrases pass through—minor slips acceptable, major ones caught by critic.
If threshold met, haiku subagent appends detected leakage to gaps block with MEDIUM severity. (Leakage is inherently ambiguous—not HIGH because it doesn't block implementation, not LOW because it's worth documenting.)

**Merge strategy**: Leakage detector appends to existing gaps block. Uses next available GAP-N ID:
1. Scan gaps block for `/^### GAP-(\d+):/` pattern (anchored to avoid matching references in text)
2. Take max ID found, increment by 1
3. If no existing GAPs, start at GAP-1
4. Append new gaps before `<!-- rodin:gaps:end -->` marker

Never overwrites or modifies existing gaps—only adds new ones. Haiku subagent writes directly via Edit tool (triggers PostToolUse to update hashes).

**Error handling**: Retry-once-then-fail-closed pattern (matches subagent retry pattern from GAP-7):
- If regex fails to find gap markers: treat as no existing gaps (start at GAP-1)
- If Edit tool fails during append: retry once, then fail with clear error message
- If concurrent edit modifies gaps block during merge: detected by hash mismatch on next hook run
- If gaps block has malformed structure: fail closed with error, require user intervention

**Gap-like phrases** are language indicating uncertainty, unresolved decisions, or acknowledged risks. Examples:
- "unclear", "not sure", "might fail", "need to investigate"
- "TODO", "TBD", "to be determined"
- "risk of", "potential issue", "may not work"
- "assuming", "if this works", "hopefully"

### Coverage determination by validator
Validator receives gaps block content + critic's findings.
Determines semantic coverage via LLM judgment—not string matching.
Outputs verdict recommendation.

**Coverage rubric:**
- **PASS**: Every HIGH and MEDIUM severity finding has a corresponding gap (semantic match, not exact)
- **FAIL**: Any HIGH or MEDIUM severity finding has no corresponding gap

LOW findings are deferred by default—they don't affect verdict. Validator errs on the side of coverage (benefit of doubt).

## Embedded Metadata Format

All rodin state is embedded in the plan file as HTML comments (won't render in most viewers):

```markdown
# My Plan

## Goals
- Ship the feature

## Implementation
- Step 1...

<!-- rodin:gaps:start -->
### GAP-1: Database rollback unclear
- **Severity**: high
- **Description**: No rollback strategy if migration fails

### GAP-2: Auth timeout handling
- **Severity**: medium
- **Description**: Unclear behavior when token expires mid-operation
<!-- rodin:gaps:end -->

<!-- rodin:session=db05b49a-780f-4b0b-bd53-5359177b8aba -->
<!-- rodin:plan:hash=a1b2c3d4e5f6... -->
<!-- rodin:gaps:hash=d4e5f6a1b2c3... -->
<!-- rodin:validation={"status":"pass","reason":"All findings covered","ts":"2026-01-23T20:00:00Z"} -->
```

**Comment placement:**
- Block delimiters (`rodin:gaps:start/end`) inline where gaps content lives
- Single-line metadata (session, hashes, validation) at **end of file**

**Empty gaps block** = agent claims zero known gaps. If critic also finds no issues (`### NO ISSUES FOUND`), assessment passes—both agent and critic agree the plan has no gaps. If critic finds issues, assessment fails—agent was wrong about having no gaps. This balanced approach prevents catch-22 where agents must invent gaps defensively.

**Deleted rodin comments** = fail closed. Treat as no assessment.

## Skill Flow

```
/rodin:plan-gate invoked
    │
    ├─ 0. Get plan file path from system context (LLM extracts from system message)
    │      Claude Code includes plan file path in system context when in plan mode
    │      Missing → fail with "Must be invoked in plan mode" (hard requirement)
    │
    ├─ 1. Check for ## Goals section in plan
    │      Missing → fail with "Plan must have ## Goals section. Add success criteria and re-run."
    │      (Fail fast: agent re-invokes after adding Goals)
    │
    ├─ 2. Check for gaps block (<!-- rodin:gaps:start --> ... <!-- rodin:gaps:end -->)
    │      Missing → fail with "Plan must have gaps block. Add <!-- rodin:gaps:start/end --> markers and re-run."
    │      (Fail fast: agent re-invokes after adding gaps block)
    │
    ├─ 3. Run leakage detector (Task tool, haiku)
    │      Input: plan content (excluding rodin blocks)
    │      If 3+ gap-like phrases → appends them to gaps block with severity
    │
    ├─ 4. Run critic (Task tool, opus)
    │      Input: plan content (excluding rodin blocks, especially gaps)
    │      Output: findings (returned, not written)
    │
    ├─ 5. Run validator (Task tool, haiku)
    │      Input: gaps block content + critic's findings
    │      Output: coverage verdict
    │
    └─ 6. Write verdict signal to plan file (compact JSON, no whitespace)
           <!-- rodin:verdict:signal={"status":"pass","reason":"All findings covered"} -->
           or
           <!-- rodin:verdict:signal={"status":"fail","reason":"Uncovered findings X, Y, Z"} -->
           PostToolUse hook converts signal to validation metadata with timestamp
           Pass → "Ready to exit plan mode"
           Fail → "Update gaps to cover findings, re-run"
```

## Hook Logic

### PostToolUse: Maintain embedded metadata

**Error handling strategy: fail-open for liveness.** PostToolUse exits silently (exit 0) on malformed JSON, missing fields, or schema errors. This is intentional—PostToolUse's job is metadata maintenance, not enforcement. If PostToolUse fails to update metadata, PreToolUse will catch the missing/stale metadata at exit time and block appropriately. This separation ensures agent workflow isn't disrupted by transient hook issues while still maintaining enforcement guarantees.

```bash
#!/bin/bash
# PostToolUse on Write|Edit (only in plan mode)
# Error handling: fail-open (exit 0 on errors) - PreToolUse enforces at exit time

# Dependency check
command -v jq >/dev/null 2>&1 || { echo "[RODIN] Error: jq required but not installed. Install via: brew install jq (macOS) or apt install jq (Linux)"; exit 1; }

input=$(cat)
# Validate JSON input (fail silently on malformed input)
if ! echo "$input" | jq -e . >/dev/null 2>&1; then
    exit 0  # Malformed JSON, skip silently
fi

# Defensive parsing: extract with null checks and fallback chains
permission_mode=$(echo "$input" | jq -r '.permission_mode // empty')
if [ -z "$permission_mode" ] || [ "$permission_mode" != "plan" ]; then
    exit 0  # Only run in plan mode (or missing field)
fi

session_id=$(echo "$input" | jq -r '.session_id // empty')
# Fallback chain for file path (handles Write vs Edit tool schema differences)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // .tool_response.filePath // empty')

# Guard against schema changes: exit silently if required fields missing
if [ -z "$session_id" ] || [ -z "$file_path" ]; then
    exit 0  # Missing required fields, skip silently (schema may have changed)
fi

# Only process plan files (not other files)
if [[ "$file_path" != "$HOME/.claude/plans/"*.md ]]; then
    exit 0
fi

# Canonicalize path and verify it's under plans directory (prevent directory traversal)
# Use Python os.path.realpath for portability (realpath not available on macOS by default)
canonical_path=$(python3 -c "import os; print(os.path.realpath('$file_path'))" 2>/dev/null) || exit 0
if [[ "$canonical_path" != "$HOME/.claude/plans/"* ]]; then
    exit 0  # Path traversal attempt, skip silently
fi

# Ensure session marker exists (inject at end if missing)
if ! grep -q "<!-- rodin:session=" "$file_path"; then
    echo "" >> "$file_path"
    echo "<!-- rodin:session=$session_id -->" >> "$file_path"
fi

# Extract plan content (everything outside <!-- rodin:* --> blocks)
# This sed removes: single-line rodin comments AND multi-line gaps blocks
plan_content=$(sed -E '
    /<!-- rodin:gaps:start -->/,/<!-- rodin:gaps:end -->/d
    /<!-- rodin:[^>]+ -->/d
' "$file_path")

# Compute plan hash
plan_hash=$(echo "$plan_content" | shasum -a 256 | cut -d' ' -f1)

# Extract gaps content (between start/end markers)
gaps_content=$(sed -n '/<!-- rodin:gaps:start -->/,/<!-- rodin:gaps:end -->/{
    /<!-- rodin:gaps:start -->/d
    /<!-- rodin:gaps:end -->/d
    p
}' "$file_path")

# Compute gaps hash (empty string if no gaps block)
if [ -n "$gaps_content" ]; then
    gaps_hash=$(echo "$gaps_content" | shasum -a 256 | cut -d' ' -f1)
else
    gaps_hash=$(echo "" | shasum -a 256 | cut -d' ' -f1)
fi

# Platform-portable sed -i helper
sed_inplace() {
    if [[ "$(uname -s)" == "Darwin" ]]; then
        sed -i '' "$@"
    else
        sed -i "$@"
    fi
}

# Update or inject hash comments (at end of file)
# Remove existing hash comments first
sed_inplace '/<!-- rodin:plan:hash=/d' "$file_path"
sed_inplace '/<!-- rodin:gaps:hash=/d' "$file_path"

echo "<!-- rodin:plan:hash=$plan_hash -->" >> "$file_path"
echo "<!-- rodin:gaps:hash=$gaps_hash -->" >> "$file_path"

# Check for verdict signal and convert to validation (JSON format)
if grep -q "<!-- rodin:verdict:signal=" "$file_path"; then
    # Extract signal JSON: <!-- rodin:verdict:signal={"status":"...","reason":"..."} -->
    # Use sed instead of grep to handle nested braces in reason field (e.g., "reason": "{retries, timeouts}")
    signal_json=$(sed -n 's/.*<!-- rodin:verdict:signal=\({.*}\).*/\1/p' "$file_path")
    timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    # Add timestamp to signal JSON
    validation_json=$(echo "$signal_json" | jq -c --arg ts "$timestamp" '. + {ts: $ts}')

    # Remove signal, remove old validation, add new validation
    sed_inplace '/<!-- rodin:verdict:signal=/d' "$file_path"
    sed_inplace '/<!-- rodin:validation=/d' "$file_path"
    echo "<!-- rodin:validation=$validation_json -->" >> "$file_path"
else
    # No signal - reset validation to pending (content changed)
    sed_inplace '/<!-- rodin:validation=/d' "$file_path"
    pending_json='{"status":"pending","reason":"Content changed, re-run assessment","ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}'
    echo "<!-- rodin:validation=$pending_json -->" >> "$file_path"
fi

exit 0
```

**Verdict signal conversion timing**: The PostToolUse hook converts verdict signal to validation metadata atomically within a single hook execution. Edge case: if the hook fails between reading the signal and writing validation metadata (e.g., disk full, permissions error), the system fails closed—PreToolUse will find no valid pass verdict and block exit. This is rare and acceptable; user re-runs assessment to recover.

### PreToolUse: Enforce verdict on ExitPlanMode

```bash
#!/bin/bash
# PreToolUse on ExitPlanMode

# Dependency check
command -v jq >/dev/null 2>&1 || { echo "[RODIN] Error: jq required but not installed. Install via: brew install jq (macOS) or apt install jq (Linux)"; exit 1; }

input=$(cat)
# Validate JSON input
if ! echo "$input" | jq -e . >/dev/null 2>&1; then
    echo "[RODIN] Internal error: malformed JSON input. Hook may need update for new schema."
    exit 1
fi

# Defensive parsing: extract with explicit null/empty check
session_id=$(echo "$input" | jq -r '.session_id // empty')

# Guard against schema changes: fail with clear error if required field missing
if [ -z "$session_id" ]; then
    echo "[RODIN] Internal error: session_id not found in hook input. Schema may have changed - hook update needed."
    exit 1
fi

# Find plan file by session marker
plan_file=$(grep -l "<!-- rodin:session=$session_id -->" "$HOME/.claude/plans/"*.md 2>/dev/null | head -1)

# No plan file with session marker = no assessment
if [ -z "$plan_file" ]; then
    echo "[RODIN] No assessment found for this session. To fix: Run /rodin:plan-gate first."
    exit 1
fi

# Extract current plan content and compute hash
plan_content=$(sed -E '
    /<!-- rodin:gaps:start -->/,/<!-- rodin:gaps:end -->/d
    /<!-- rodin:[^>]+ -->/d
' "$plan_file")
current_plan_hash=$(echo "$plan_content" | shasum -a 256 | cut -d' ' -f1)

# Extract recorded plan hash
recorded_plan_hash=$(grep -o '<!-- rodin:plan:hash=[^>]*' "$plan_file" | sed 's/<!-- rodin:plan:hash=//' | sed 's/ -->//')

if [ "$current_plan_hash" != "$recorded_plan_hash" ]; then
    echo "[RODIN] Plan content changed since assessment. To fix: Re-run /rodin:plan-gate."
    exit 1
fi

# Extract current gaps content and compute hash
gaps_content=$(sed -n '/<!-- rodin:gaps:start -->/,/<!-- rodin:gaps:end -->/{
    /<!-- rodin:gaps:start -->/d
    /<!-- rodin:gaps:end -->/d
    p
}' "$plan_file")
if [ -n "$gaps_content" ]; then
    current_gaps_hash=$(echo "$gaps_content" | shasum -a 256 | cut -d' ' -f1)
else
    current_gaps_hash=$(echo "" | shasum -a 256 | cut -d' ' -f1)
fi

# Extract recorded gaps hash
recorded_gaps_hash=$(grep -o '<!-- rodin:gaps:hash=[^>]*' "$plan_file" | sed 's/<!-- rodin:gaps:hash=//' | sed 's/ -->//')

if [ "$current_gaps_hash" != "$recorded_gaps_hash" ]; then
    echo "[RODIN] Gaps changed since assessment. To fix: Re-run /rodin:plan-gate."
    exit 1
fi

# Extract validation JSON and parse with jq
# Format: <!-- rodin:validation={"status":"...","reason":"...","ts":"..."} -->
# Use sed instead of grep to handle nested braces in reason field
validation_json=$(sed -n 's/.*<!-- rodin:validation=\({.*}\).*/\1/p' "$plan_file")
if [ -z "$validation_json" ]; then
    echo "[RODIN] No validation metadata found. To fix: Run /rodin:plan-gate."
    exit 1
fi

status=$(echo "$validation_json" | jq -r '.status')
reason=$(echo "$validation_json" | jq -r '.reason')

# Validate status is expected value (fail closed on malformed)
case "$status" in
    pass)
        exit 0  # Allow exit
        ;;
    pending)
        echo "[RODIN] Assessment pending. To fix: Run /rodin:plan-gate."
        exit 1
        ;;
    fail)
        echo "[RODIN] Assessment failed: $reason"
        echo "To fix: Update gaps to cover findings, then re-run /rodin:plan-gate."
        exit 1
        ;;
    *)
        echo "[RODIN] Internal error: unexpected validation status '$status'. To fix: Re-run /rodin:plan-gate."
        exit 1
        ;;
esac
```

## Test Infrastructure

Hook testing follows the worktree-isolation plugin pattern:

### Test Harness
```
plugins/rodin/tests/
  run_tests.sh           # Main test runner
  test_post_tool_use.sh  # PostToolUse hook tests
  test_pre_tool_use.sh   # PreToolUse hook tests
  test_skill_flow.sh     # Skill orchestration tests
  fixtures/
    plans/
      valid_plan.md           # Plan with valid rodin metadata (pass verdict)
      no_session.md           # Plan without session marker
      stale_plan_hash.md      # Plan with outdated plan hash
      stale_gaps_hash.md      # Plan with outdated gaps hash
      no_goals.md             # Plan without Goals section
      no_gaps_block.md        # Plan without gaps block markers
      empty_gaps_block.md     # Plan with empty gaps block
      pending_verdict.md      # Plan with validation=pending
      fail_verdict.md         # Plan with validation=fail
      deleted_metadata.md     # Plan with rodin comments removed
      malformed_markers.md    # Plan with unclosed/invalid markers
      hash_reference.md       # Minimal plan with known hash value for verification
    inputs/
      plan_mode_edit.json     # Hook input: permission_mode=plan, valid paths
      non_plan_mode.json      # Hook input: permission_mode != plan
      non_plan_file.json      # Hook input: file outside ~/.claude/plans/
      null_fields.json        # Hook input: missing session_id or file_path
      exit_plan_mode.json     # Hook input: ExitPlanMode with session_id
```

### Test Pattern
```bash
# Fixture-based testing with JSON input mocking
test_post_tool_use_injects_session() {
    local input='{"permission_mode":"plan","session_id":"test-123","tool_input":{"file_path":"fixtures/no_session.md"}}'
    echo "$input" | ../hooks/post_tool_use.sh
    grep -q "<!-- rodin:session=test-123 -->" fixtures/no_session.md || fail "Session marker not injected"
}
```

### Assertion Helpers
- `assert_file_contains <file> <pattern>` - Verify pattern in file
- `assert_exit_code <expected> <command>` - Verify exit status
- `assert_output_contains <pattern> <command>` - Verify stdout/stderr
- `assert_content_excludes <content_var> <pattern>` - Verify pattern NOT present in content (for critic isolation testing)

### Subagent Mocking
Skill tests use fixture files for predetermined responses:
```
plugins/rodin/tests/fixtures/
  subagents/
    leakage_none.json      # Leakage detector: no gap-like phrases
    leakage_found.json     # Leakage detector: 3+ phrases detected
    critic_pass.json       # Critic: NO ISSUES FOUND
    critic_findings.json   # Critic: multiple findings
    critic_malformed.json  # Critic: unparseable output (for retry testing)
    critic_timeout.json    # Critic: simulated timeout response
    validator_pass.json    # Validator: VERDICT PASS
    validator_fail.json    # Validator: VERDICT FAIL
    validator_malformed.json # Validator: unparseable output
```

Test harness intercepts Task tool calls and returns fixture content based on test scenario. Skill logic (parsing, orchestration, verdict signal writing) tested without real LLM calls.

**Retry testing**: Use `MOCK_TASK_SEQUENCE` to return failure fixture first, success fixture second:
```bash
export MOCK_TASK_SEQUENCE="critic_malformed.json,critic_findings.json"
```

### Leakage Detection Testing

Testing leakage detector behavior (REQ-PEG-004 scenarios) requires verifying that detected gaps are correctly appended to the gaps block. Approach:

1. **Setup**: Create plan fixture with gap-like phrases in content, empty or populated gaps block
2. **Mock**: Configure mock Task tool to return `leakage_found.json` with detected phrases
3. **Execute**: Run skill flow through leakage detection phase (mocked Edit tool writes to plan file)
4. **Assert**: Use `assert_file_contains` to verify gaps block content:
   ```bash
   test_leakage_detection_appends_gaps() {
       cp fixtures/plans/with_gap_phrases.md "$TEST_PLAN"
       export MOCK_TASK_RESPONSES="leakage_found.json,critic_pass.json,validator_pass.json"

       run_skill_flow "$TEST_PLAN"

       # Verify detected gaps were appended with correct format
       assert_file_contains "$TEST_PLAN" "### GAP-1:"
       assert_file_contains "$TEST_PLAN" "**Severity**: medium"
       # Verify original content preserved
       assert_file_contains "$TEST_PLAN" "<!-- rodin:gaps:start -->"
   }
   ```

This approach tests the full leakage-to-gaps-block flow without real LLM calls, verifying both detection and merge behavior.

### Skill Test Infrastructure

Skill tests verify orchestration logic without real LLM calls:

**Approach**: The skill is a markdown file with instructions. Testing verifies:
1. Plan structure validation (Goals, gaps block present)
2. Content extraction excludes rodin blocks
3. Subagent invocation sequence (leakage → critic → validator)
4. Verdict signal written correctly based on validator output

**Test Pattern**:
```bash
# Skill tests use a mock Task tool wrapper
test_skill_flow_critic_finds_issues() {
    # Set up: plan with goals and gaps block
    cp fixtures/plans/valid_plan.md "$TEST_PLAN"

    # Mock Task tool to return critic findings then validator fail
    export MOCK_TASK_RESPONSES="critic_findings.json,validator_fail.json"

    # Run skill (simulated via test harness)
    run_skill_flow "$TEST_PLAN"

    # Verify verdict signal written
    assert_file_contains "$TEST_PLAN" "rodin:verdict:signal=fail"
}
```

**Mock Task Tool**: Test harness provides `mock_task` function that:
1. Records invocation arguments (model, prompt content)
2. Returns predetermined fixture response
3. Allows assertion on invocation order and arguments

**Skill-Specific Assertions**:
- `assert_task_invoked <model> <prompt_pattern>` - Verify Task tool called with expected model and prompt
- `assert_invocation_order <model1> <model2> ...` - Verify subagents invoked in correct sequence
- `assert_verdict_signal <status> <reason_pattern>` - Verify verdict signal content

### Test Naming Convention
Test functions follow `test_<requirement>_<scenario>` pattern to map directly to spec scenarios:
```bash
# From spec.md: Requirement "Goals section validation" → Scenario "Missing goals"
test_goals_section_validation_missing_goals() { ... }

# From spec.md: Requirement "Leakage detection" → Scenario "Below threshold"
test_leakage_detection_below_threshold() { ... }
```

Coverage verification: compare test function names against spec scenario names. Missing test = coverage gap.

### Integration Test Pattern

Cross-hook integration tests verify state transitions across multiple hook invocations:

```bash
# Integration test: full assessment workflow
test_integration_assessment_workflow() {
    # Initial edit triggers PostToolUse
    echo '{"permission_mode":"plan","session_id":"test-123","tool_input":{"file_path":"$TEST_PLAN"}}' | ../hooks/post_tool_use.sh
    assert_file_contains "$TEST_PLAN" "rodin:session=test-123"
    assert_file_contains "$TEST_PLAN" "rodin:plan:hash="

    # Simulate skill verdict signal (JSON format)
    echo '<!-- rodin:verdict:signal={"status":"pass","reason":"All covered"} -->' >> "$TEST_PLAN"
    echo '{"permission_mode":"plan","session_id":"test-123","tool_input":{"file_path":"$TEST_PLAN"}}' | ../hooks/post_tool_use.sh
    assert_file_contains "$TEST_PLAN" "rodin:validation=pass"

    # Verify PreToolUse allows exit
    echo '{"session_id":"test-123"}' | ../hooks/pre_tool_use.sh
    assert_exit_code 0 "Pre-hook should allow exit with pass validation"
}
```

Integration tests use orchestrator script that chains hook invocations with state verification between each step.

### Platform Portability Testing

Hooks use `sed_inplace` helper for cross-platform sed compatibility. Testing on both macOS and Linux recommended:
- **Local**: Test on developer platform (typically macOS)
- **CI**: Run tests in Linux container to verify `sed -i` (no quotes) works
- **Manual verification**: `uname -s` detection path tested by temporarily overriding

### E2E Testing (Future Work)

Current test infrastructure uses integration tests with mocked Task tool. True E2E tests require a Claude Code test harness that can:
- Orchestrate real PreToolUse → skill → PostToolUse sequences
- Simulate actual Claude Code environment (plan mode context, session IDs)
- Verify internal state (plan file contents, gaps block, validation metadata)

**MVP approach**: Integration tests with mocked Task tool are sufficient. Scenarios requiring internal state verification (e.g., "gaps block contains detected concerns") use file assertions after mocked subagent responses. This tests orchestration logic without requiring real LLM calls.

**Future enhancement**: When Claude Code provides a test harness or plugin testing framework, add true E2E tests that exercise the full workflow with actual tool invocations.

## Risks / Trade-offs

- **Default block may frustrate users** → Users can force-exit plan mode via native Claude Code hotkey if needed
- **Subagent latency** → Two Task calls; acceptable for plan quality (time spent planning is better than time spent on wasted work and **rework**)
- **Critic too harsh/lenient** → Prompt tuning; coverage model provides feedback
- **Comment extraction fragility** → sed patterns must handle edge cases; fail closed on parse errors
- **Plan file pollution** → HTML comments at end of file; won't render in most viewers
