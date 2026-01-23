## Why

Agents gloss over uncertainties when planning—acknowledging gaps internally but not articulating them explicitly. An adversarial critic catches gaps the agent missed or minimized. By requiring the agent's documented gaps to cover the critic's findings, we force honest gap articulation before implementation begins.

## What Changes

### Skill: `/rodin:plan-gate`
Orchestrates adversarial gap analysis via Task tool subagents:
1. Verifies plan has `## Goals` section (success criteria)
2. Ensures `<session_id>.gaps.md` exists with agent's known gaps
3. Runs **haiku** subagent for leakage detection (flags 3+ gap-like phrases)
4. Runs **opus** critic subagent to find gaps in plan (isolated from gaps.md)
5. Runs **haiku** validator subagent to check if gaps cover critic findings
6. Writes verdict to `<session_id>.gate.yml`

### Hook: `PostToolUse` on Write|Edit (plan mode only)
Maintains session mapping and hashes:
- Creates `<slug>.session` → session_id mapping when plan file edited
- Updates `plan_hash` in gate.yml on plan edits
- Updates `gaps_hash` in gate.yml on gaps.md edits
- Only runs when `permission_mode == "plan"`

### Hook: `PreToolUse` on ExitPlanMode
Enforces assessment verdict:
- Default blocks exit, prompting `/rodin:plan-gate`
- Hash mismatch (stale verdict): blocks with re-run prompt
- Valid pass verdict: allows exit
- Valid fail verdict: blocks with reason
- Fails closed on FS errors (permissions, disk full)

## Capabilities

### New Capabilities
- `plan-exit-gate`: Combined skill + hooks
  - Skill (`/rodin:plan-gate`): orchestrates adversarial gap analysis
  - Hook (`PostToolUse:Write|Edit`): maintains session mapping and hashes
  - Hook (`PreToolUse:ExitPlanMode`): enforces assessment verdict

### Modified Capabilities
(none)

## Impact

- New plugin at `plugins/rodin/` with skill and hooks
- User/agent invokes `/rodin:plan-gate` during planning
- Artifacts in `~/.claude/plans/rodin-plan-gate/`:
  - `<slug>.session` — session_id mapping (slug from plan filename)
  - `<session_id>.gaps.md` — Agent's documented gaps
  - `<session_id>.gate.yml` — Verdict with hashes
