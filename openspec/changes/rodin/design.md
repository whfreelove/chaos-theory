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

**Behavior:** Default blocks ExitPlanMode until assessment passes.

## Decisions

### Skill for orchestration, hook for enforcement
- Skill `/rodin:plan-gate` handles subagent orchestration via Task tool, user interaction
- Hook only checks verdict in gate.yml

### Skill uses Task tool for subagents
All subagents are invoked via Task tool. The skill instructs; the agent orchestrates.

- **Leakage detector (haiku)**: scans plan for gap-like phrases. Fast, cheap.
- **Critic (opus)**: reads plan file, outputs findings in structured markdown. Needs depth for adversarial analysis. Key prompt elements: (1) adversarial role, (2) focus on goals mismatches, implementation blockers, unstated assumptions, unmitigated risks, (3) structured output format, (4) explicit "no issues" declaration if none found.
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

Critic findings passed directly critic to validator (by agent), no intermediate file. Note: leakage detector writes to gaps.md (agent's self-documented gaps), which is distinct from critic findings (ephemeral, not persisted).
On subagent failure (timeout, crash, unparseable output): retry once, then fail closed.

### Use actual plan mode file
The skill works with the plan file Claude Code already creates at `~/.claude/plans/<session>.md`.

### Two rodin artifacts
- `<session_id>.gaps.md`: Agent's known gaps (hidden from critic)
- `<session_id>.gate.yml`: Verdict with hashes

**Terminology:** `session_id` is the unique identifier provided by Claude Code's hook input (e.g., `db05b49a-780f-4b0b-bd53-5359177b8aba`). `slug` is the human-readable plan filename (e.g., `lucky-dreaming-badger`). The `<slug>.session` mapping file bridges them.

### Critic isolation (defense-in-depth)
Gaps.md is hidden from critic to prevent accidental priming. Critic should find gaps independently, not confirm gaps the agent already documented. This ensures critic catches what the agent missed or minimized, rather than anchoring on the agent's framing.

**Soft constraint**: Isolation is enforced via prompt instruction—skill passes plan content directly to critic via Task tool input, not a file path. Critic has no reason to access gaps.md, but technically could read filesystem. Accepted trade-off: realistic threat is accidental priming, not adversarial critic behavior.

### Session discovery via PostToolUse hook
Hooks receive `session_id` and `tool_input.file_path` from Claude Code. A PostToolUse hook on Write|Edit to plan files:
1. Only runs when `permission_mode == "plan"`
2. Extracts slug from file path (e.g., `lucky-dreaming-badger` from `~/claude/plans/lucky-dreaming-badger.md`)
3. Creates mapping: `~/.claude/plans/rodin-plan-gate/<slug>.session` → contains session_id
4. Maintains `<session_id>.gate.yml` with fresh `plan_file` path and `plan_hash`

This hook also catches edits to `<session_id>.gaps.md`, keeping `gaps_hash` fresh.

### Hash maintenance by PostToolUse hook
Hashes are computed by the PostToolUse hook (deterministic shell code), never by LLMs:
- Plan file edited → hook resets `status: pending` and updates `plan_hash`
- Gaps file edited → hook resets `status: pending` and updates `gaps_hash`

**Why reset status on any edit?** If we only updated hashes, a stale "pass" verdict would incorrectly allow exit (hash always matches since hook keeps it fresh). Resetting to pending on both plan and gaps edits ensures any change requires fresh assessment.

### Opt-in at two levels
1. Plugin installation: enables the hook
2. Skill invocation: triggers assessment

If user never runs `/rodin:plan-gate`, no gate.yml exists, hook blocks exit (assessment required once plugin installed).
If user runs skill but plan/gaps changed after, hook treats as stale verdict and blocks.

**Acknowledged trade-off:** This opt-in design has circularity: agents that exit prematurely won't invoke the skill anyway. This is intentional—forcing assessment would be intrusive and break workflows. The plugin targets agents/users who *want* gap discipline, not those who need to be forced into it. Future work could explore automated skill invocation via hooks if user opts in.

### Leakage detection (haiku subagent)
Scans plan for gap-like phrases before critic runs.
Uses keyword threshold: only acts if 3+ distinct gap-like phrases detected.
Single phrases pass through—minor slips acceptable, major ones caught by critic.
If threshold met, haiku subagent documents detected leakage as gap(s) in gaps.md with appropriate severity.

**Merge strategy**: Leakage detector appends to existing gaps.md content. Uses next available GAP-N ID (scans existing IDs, increments from highest). Never overwrites or modifies existing gaps—only adds new ones.

**Gap-like phrases** are language indicating uncertainty, unresolved decisions, or acknowledged risks. Examples:
- "unclear", "not sure", "might fail", "need to investigate"
- "TODO", "TBD", "to be determined"
- "risk of", "potential issue", "may not work"
- "assuming", "if this works", "hopefully"

### Coverage determination by validator
Validator receives gaps + critic's findings.
Determines semantic coverage via LLM judgment—not string matching.
Outputs verdict recommendation.

**Coverage rubric:**
- **PASS**: Every HIGH and MEDIUM severity finding has a corresponding gap (semantic match, not exact)
- **FAIL**: Any HIGH or MEDIUM severity finding has no corresponding gap

LOW findings are deferred by default—they don't affect verdict. Validator errs on the side of coverage (benefit of doubt).

## Artifacts Location

```
~/.claude/plans/
├── lucky-dreaming-badger.md             # Plan file (slug-named, created by Claude Code)
└── rodin-plan-gate/
    ├── lucky-dreaming-badger.session    # Mapping: contains session_id
    ├── <session_id>.gaps.md             # Agent's known gaps
    └── <session_id>.gate.yml            # Verdict with hashes
```

The slug→session_id mapping allows the skill (which knows the slug from the plan file path) to find the session_id for artifact keying. The ExitPlanMode hook receives the session_id directly.

### gaps.md format

```markdown
### GAP-1: Database rollback unclear
- **Severity**: high
- **Description**: No rollback strategy if migration fails

### GAP-2: Auth timeout handling
- **Severity**: medium
- **Description**: Unclear behavior when token expires mid-operation
```

**Empty gaps.md** = agent claims zero known gaps. All critic findings would be uncovered → assessment fails. This is intentional: claiming no gaps when critic finds issues demonstrates poor gap awareness.

### gate.yml format

```yaml
plan_file: /Users/whfreelove/.claude/plans/lucky-dreaming-badger.md
plan_hash: a1b2c3d4e5f6...
gaps_file: /Users/whfreelove/.claude/plans/rodin-plan-gate/<session_id>.gaps.md
gaps_hash: d4e5f6a1b2c3...
status: pass  # or fail or pending
reason: null  # or explanation if fail
timestamp: 2026-01-21T20:00:00Z
```

Note: `plan_hash` and `gaps_hash` are maintained by the PostToolUse hook, not the skill. The skill sets `status`, `reason`, and `timestamp` (last assessment time). Initial timestamp set on gate.yml creation; updated on each assessment.

## Skill Flow

```
/rodin:plan-gate invoked
    │
    ├─ 0. Extract slug from plan file path (LLM extracts from system message)
    │      Claude Code includes plan file path in system context when in plan mode
    │      e.g., "lucky-dreaming-badger" from ~/.claude/plans/lucky-dreaming-badger.md
    │      Missing → fail with "Must be invoked in plan mode" (hard requirement)
    │
    ├─ 1. Read session_id from <slug>.session mapping file
    │      Missing → prompt to edit plan file first (triggers PostToolUse hook)
    │
    ├─ 2. Check for ## Goals section in plan
    │      Missing → prompt agent to add success criteria
    │
    ├─ 3. Check/prompt for <session_id>.gaps.md
    │      Missing → prompt agent to write known gaps
    │
    ├─ 4. Run leakage detector (Task tool, haiku)
    │      Input: plan file content
    │      If 3+ gap-like phrases → writes them to gaps.md with severity
    │
    ├─ 5. Run critic (Task tool)
    │      Input: plan file content (NOT gaps.md)
    │      Output: findings (returned, not written)
    │
    ├─ 6. Run validator (Task tool)
    │      Input: gaps.md content + critic's findings
    │      Output: coverage verdict
    │
    └─ 7. Update gate.yml with verdict
           Set status and reason only (hashes maintained by PostToolUse hook)
           Pass → "Ready to exit plan mode"
           Fail → "Update gaps.md with uncovered findings, re-run"
```

## Hook Logic

### PostToolUse: Maintain session mapping and hashes

```bash
# PostToolUse on Write|Edit (only in plan mode)
input=$(cat)
permission_mode=$(echo "$input" | jq -r '.permission_mode')
if [ "$permission_mode" != "plan" ]; then
    exit 0  # Only run in plan mode
fi

session_id=$(echo "$input" | jq -r '.session_id')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // .tool_response.filePath')
RODIN_DIR="$HOME/.claude/plans/rodin-plan-gate"
mkdir -p "$RODIN_DIR"

# Check if this is a plan file edit
if [[ "$file_path" == "$HOME/.claude/plans/"*.md && "$file_path" != *"/rodin-plan-gate/"* ]]; then
    slug=$(basename "$file_path" .md)

    # Write/update slug→session_id mapping
    echo "$session_id" > "$RODIN_DIR/${slug}.session"

    # Update plan_hash in gate.yml (create if needed)
    gate_file="$RODIN_DIR/${session_id}.gate.yml"
    plan_hash=$(shasum -a 256 "$file_path" | cut -d' ' -f1)

    if [ -f "$gate_file" ]; then
        # Update existing gate.yml (perl -i for cross-platform portability)
        # Reset status to pending - any plan edit requires fresh assessment
        perl -i -pe "s|^plan_file:.*|plan_file: $file_path|" "$gate_file"
        perl -i -pe "s|^plan_hash:.*|plan_hash: $plan_hash|" "$gate_file"
        perl -i -pe "s|^status:.*|status: pending|" "$gate_file"
        perl -i -pe "s|^reason:.*|reason: Plan edited, re-run assessment|" "$gate_file"
    else
        # Create initial gate.yml
        cat > "$gate_file" << EOF
plan_file: $file_path
plan_hash: $plan_hash
gaps_file:
gaps_hash:
status: pending
reason: Assessment not yet run
timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF
    fi
fi

# Check if this is a gaps.md edit
if [[ "$file_path" == "$RODIN_DIR/"*".gaps.md" ]]; then
    # Extract session_id from filename (e.g., "db05b49a-...gaps.md" → "db05b49a-...")
    # Use filename session_id, not input session_id, to avoid cross-session pollution
    gaps_session_id=$(basename "$file_path" .gaps.md)
    gaps_hash=$(shasum -a 256 "$file_path" | cut -d' ' -f1)
    gate_file="$RODIN_DIR/${gaps_session_id}.gate.yml"

    if [ -f "$gate_file" ]; then
        perl -i -pe "s|^gaps_file:.*|gaps_file: $file_path|" "$gate_file"
        perl -i -pe "s|^gaps_hash:.*|gaps_hash: $gaps_hash|" "$gate_file"
        # Reset status to pending - gaps edit requires fresh assessment
        perl -i -pe "s|^status:.*|status: pending|" "$gate_file"
        perl -i -pe "s|^reason:.*|reason: Gaps edited, re-run assessment|" "$gate_file"
    fi
fi

exit 0
```

### PreToolUse: Enforce verdict on ExitPlanMode

**Why verify hashes if PostToolUse keeps them fresh?** Defense-in-depth. The hash check catches:
- Direct file edits outside Claude Code (user opens file in editor)
- PostToolUse hook failures (permissions, crashes, race conditions)
- Partial writes (tool interrupted mid-operation)

Normal operation: PostToolUse maintains hashes, so comparison always passes. Edge cases: hash mismatch blocks exit, prompting re-assessment.

```bash
# PreToolUse on ExitPlanMode
input=$(cat)
session_id=$(echo "$input" | jq -r '.session_id')
RODIN_DIR="$HOME/.claude/plans/rodin-plan-gate"
gate_file="$RODIN_DIR/${session_id}.gate.yml"

# No gate file = no assessment = BLOCK
if [ ! -f "$gate_file" ]; then
    echo "[RODIN] No assessment found. To fix: Run /rodin:plan-gate first."
    exit 1
fi

# Read plan file path (fail closed if unreadable)
plan_file=$(grep '^plan_file:' "$gate_file" | sed 's/^[^:]*: //')
if [ -z "$plan_file" ]; then
    echo "[RODIN] Gate file corrupt: missing plan_file. To fix: Re-run /rodin:plan-gate."
    exit 1
fi

# Verify plan hash (fail closed on read error)
plan_hash=$(shasum -a 256 "$plan_file" 2>&1)
if [ $? -ne 0 ]; then
    echo "[RODIN] Cannot read plan file: $plan_hash. To fix: Check file permissions."
    exit 1
fi
plan_hash=$(echo "$plan_hash" | cut -d' ' -f1)
recorded_plan_hash=$(grep '^plan_hash:' "$gate_file" | sed 's/^[^:]*: //')
if [ "$plan_hash" != "$recorded_plan_hash" ]; then
    echo "[RODIN] Plan hash mismatch. To fix: Re-run /rodin:plan-gate."
    exit 1
fi

# Verify gaps hash (fail closed if referenced but missing)
gaps_file=$(grep '^gaps_file:' "$gate_file" | sed 's/^[^:]*: //')
if [ -n "$gaps_file" ] && [ ! -f "$gaps_file" ]; then
    echo "[RODIN] Gaps file referenced but missing: $gaps_file. To fix: Re-run /rodin:plan-gate."
    exit 1
fi
if [ -n "$gaps_file" ] && [ -f "$gaps_file" ]; then
    gaps_hash=$(shasum -a 256 "$gaps_file" 2>&1)
    if [ $? -ne 0 ]; then
        echo "[RODIN] Cannot read gaps file: $gaps_hash. To fix: Check file permissions."
        exit 1
    fi
    gaps_hash=$(echo "$gaps_hash" | cut -d' ' -f1)
    recorded_gaps_hash=$(grep '^gaps_hash:' "$gate_file" | sed 's/^[^:]*: //')
    if [ "$gaps_hash" != "$recorded_gaps_hash" ]; then
        echo "[RODIN] Gaps hash mismatch. To fix: Re-run /rodin:plan-gate."
        exit 1
    fi
fi

# Check verdict
status=$(grep '^status:' "$gate_file" | sed 's/^[^:]*: //')
if [ "$status" = "pass" ]; then
    exit 0  # Allow
elif [ "$status" = "pending" ]; then
    echo "[RODIN] Assessment pending. To fix: Run /rodin:plan-gate."
    exit 1
else
    reason=$(grep '^reason:' "$gate_file" | sed 's/^[^:]*: //')
    echo "[RODIN] Assessment failed: $reason"
    echo "To fix: Update gaps.md to cover findings, then re-run /rodin:plan-gate."
    exit 1
fi
```

## Risks / Trade-offs

- **Default block may frustrate users** → Users can force-exit plan mode via native Claude Code hotkey if needed
- **Subagent latency** → Two Task calls; acceptable for plan quality (time spent planning is better than time spent on wasted work and **rework**)
- **Critic too harsh/lenient** → Prompt tuning; coverage model provides feedback
- **Plan file discovery** → Need session context to find correct file
