## Why

Agents have blindspots when planning—they miss gaps due to cognitive limitations, not intentional omission. An adversarial critic with fresh perspective catches gaps the agent overlooked or underestimated. By requiring the agent's documented gaps to cover the critic's findings, we surface blindspots before implementation begins.

## What Changes

### Skill: `/rodin:plan-gate`
Orchestrates adversarial gap analysis via Task tool subagents:
1. Verifies plan has `## Goals` section (success criteria)
2. Ensures gaps block exists in plan file (`<!-- rodin:gaps:start -->...<!-- rodin:gaps:end -->`)
3. Runs **haiku** subagent for leakage detection—scans plan for gap-like phrases (uncertainty markers, TODOs, risk language) that should be documented as explicit gaps; flags when 3+ detected
4. Runs **opus** critic subagent to find gaps in plan (isolated from gaps block)
5. Runs **haiku** validator subagent to check if gaps cover critic findings
6. Writes verdict signal to plan file (hook converts to validation metadata)

### Hook: `PostToolUse` on Write|Edit (plan mode only)
Maintains embedded metadata in plan file:
- Injects session marker on first edit (`<!-- rodin:session=<session_id> -->`)—links plan file to current session so PreToolUse can locate the correct plan at exit time
- Tracks plan and gaps content hashes (recomputes on each edit)
- Converts verdict signal to validation metadata with timestamp
- Resets validation to pending when content changes without verdict signal
- Only runs when `permission_mode == "plan"` (Claude Code's planning state where agent can only modify plan file)

### Hook: `PreToolUse` on ExitPlanMode
Enforces assessment verdict:
- Finds plan file by grepping for `<!-- rodin:session=<session_id> -->`
- No session marker found: blocks with "Run /rodin:plan-gate"
- Hash mismatch (stale verdict): blocks with re-run prompt
- Valid pass verdict: allows exit
- Valid fail verdict: blocks with reason
- Fails closed on read errors

## Capabilities

### New Capabilities
- `plan-exit-gate`: Combined skill + hooks that surface blindspots before implementation
  - **Skill (`/rodin:plan-gate`)**: orchestrates adversarial gap analysis—invokes an independent critic to find gaps the agent missed, then validates that documented gaps cover those findings. This forces the agent to demonstrate awareness of potential issues.
  - **Hook (`PostToolUse:Write|Edit`)**: maintains embedded metadata (session markers, content hashes, validation state)—tracks whether the plan has been assessed and whether it changed after assessment.
  - **Hook (`PreToolUse:ExitPlanMode`)**: enforces assessment verdict—blocks exit if no assessment exists, if assessment failed, or if plan/gaps changed since assessment. This is the enforcement mechanism that ensures blindspots are surfaced before implementation begins.

### Modified Capabilities
(none)

## Impact

- New plugin at `plugins/rodin/` with skill and hooks
- User/agent invokes `/rodin:plan-gate` during planning
- **Exit is BLOCKED** until assessment passes (this is the core enforcement mechanism)
- All metadata embedded in plan file as HTML comments (no external artifacts):
  - `<!-- rodin:session=... -->` — links plan to session
  - `<!-- rodin:gaps:start -->...<!-- rodin:gaps:end -->` — agent's documented gaps
  - `<!-- rodin:plan:hash=... -->` — plan content hash
  - `<!-- rodin:gaps:hash=... -->` — gaps content hash
  - `<!-- rodin:validation=... -->` — verdict with timestamp
