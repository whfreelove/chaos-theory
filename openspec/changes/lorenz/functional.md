## Why

Agents have blindspots when planning—they miss gaps due to cognitive limitations, not intentional omission. An adversarial critic with fresh perspective catches gaps the agent overlooked or underestimated. By requiring the agent's documented gaps to cover the critic's findings, we surface blindspots before implementation begins.

## Capabilities

### `plan-gate-skill`

Agent can invoke `/rodin:plan-gate` to run adversarial gap analysis and receive a pass/fail verdict. The skill orchestrates independent subagents: a leakage detector that surfaces gap-like phrases already embedded in the plan text, an adversarial critic that finds gaps the agent missed, and a validator that checks whether the agent's documented gaps cover the critic's findings. Assessment is opt-in via skill invocation.

### `post-tool-hook`

Plan file metadata (session marker, content hashes, validation state) is maintained automatically on every edit in plan mode. The hook injects a session marker on first edit, recomputes plan and gaps content hashes on every subsequent edit, and converts a verdict signal written by the skill into persistent validation metadata with a timestamp. Content changes after assessment reset validation to pending.

### `pre-tool-hook`

Plan mode exit is blocked until a valid passing assessment exists for the current session. The hook discovers the plan file by grepping for the session marker, verifies that plan and gaps hashes match the recorded values (detecting any post-assessment edits), and enforces the verdict: pass allows exit, fail or pending blocks with actionable guidance, and missing metadata fails closed.

## User Impact

### Scope

- New plugin at `plugins/rodin/` containing skill and hooks
- User or agent invokes `/rodin:plan-gate` during planning to trigger assessment
- Exit from plan mode is **blocked** until assessment passes
- All metadata embedded in the plan file as HTML comments (no external artifacts):
  - `<!-- rodin:session=... -->` — links plan to current session
  - `<!-- rodin:gaps:start -->...<!-- rodin:gaps:end -->` — agent's documented gaps
  - `<!-- rodin:plan:hash=... -->` — plan content hash
  - `<!-- rodin:gaps:hash=... -->` — gaps content hash
  - `<!-- rodin:validation=... -->` — verdict with timestamp

### Out of Scope

- No GUI or visual dashboard
- No persistent gap databases or external state files
- No automatic fix suggestions
- No enforcement outside plan mode

### Current Limitations

None — greenfield implementation.

### Planned Future Work

None declared.

### Known Risks

- **Shell portability**: `sed -i` syntax differs between macOS and GNU Linux; hooks use a platform-detection helper. Full Python rewrite planned for future to resolve accumulated portability issues.
- **jq dependency**: Hooks require `jq` for JSON parsing; not universally pre-installed. Installation guidance surfaced in error messages.
- **`sed` cross-platform**: POSIX `sed` assumed for text extraction; edge cases may exist in hash computation across platforms.
- **Hash consistency**: Plan and gaps hashes depend on exact whitespace; cross-platform hash values must match for enforcement to work correctly.

## Overview

The skill orchestrates adversarial gap analysis via Task tool subagents: leakage detector (haiku) → adversarial critic (opus) → coverage validator (haiku). The critic receives plan content with the gaps block removed, preventing accidental priming. After the validator returns its verdict, the skill writes a compact JSON verdict signal as an HTML comment in the plan file.

The PostToolUse hook fires on every Write or Edit in plan mode, converting the verdict signal to persistent validation metadata and recomputing content hashes. The PreToolUse hook fires when the agent attempts to exit plan mode, discovering the plan by session marker grep and enforcing hash-verified verdict integrity before allowing exit.

All state is self-contained in the plan file. No external files, no cleanup required—state lives and dies with the plan.
