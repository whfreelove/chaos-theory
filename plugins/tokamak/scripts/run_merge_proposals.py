#!/usr/bin/env python3
"""
Parallel merge proposal generator for OpenSpec change→project merges.

Launches Sonnet subprocesses per artifact type to produce structured JSON
proposals instead of writing directly to project files.  The orchestrating
SKILL.md reviews proposals, auto-accepts "delegate" confidence items, and
presents "check-in" items to the user before writing anything.

Usage:
    python run_merge_proposals.py <change_dir> [--max-concurrent N] [--timeout S] [--dry-run] [--budget USD]
"""

import argparse
import asyncio
import json
import shutil
import sys
from pathlib import Path

from spec_utils import (
    build_command,
    gather_with_callback,
    resolve_project_dir,
    resolve_schema_name,
    run_one_subprocess,
)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Generate merge proposals for change→project artifact merges'
    )
    parser.add_argument('change_dir', type=Path,
                        help='Path to OpenSpec change directory')
    parser.add_argument('--max-concurrent', type=int, default=6,
                        help='Maximum parallel claude -p processes (default: 6)')
    parser.add_argument('--timeout', type=int, default=600,
                        help='Timeout per subprocess in seconds (default: 600)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print prompts and commands without launching processes')
    parser.add_argument('--budget', type=float, default=None,
                        help='Max budget per subprocess in USD')
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_merge_config(change_dir: Path) -> dict:
    """Load schema-keyed merge-rules config for a change directory.

    Resolution (same pattern as select_critics.py):
    1. Read ``schema:`` from ``.openspec.yaml``
    2. Look for ``plugin_root / merge-rules.{schema}.json``
    3. Fall back to ``plugin_root / merge-rules.chaos-theory.json``
    """
    script_dir = Path(__file__).parent.resolve()
    plugin_root = script_dir.parent

    schema_name = resolve_schema_name(change_dir)

    if schema_name:
        config_path = plugin_root / f'merge-rules.{schema_name}.json'
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)

    # Fallback to default
    fallback = plugin_root / 'merge-rules.chaos-theory.json'
    if fallback.exists():
        with open(fallback) as f:
            return json.load(f)

    raise FileNotFoundError(
        f"No merge-rules config found for schema '{schema_name}' "
        f"and no fallback at {fallback}"
    )


# ---------------------------------------------------------------------------
# Artifact pairing
# ---------------------------------------------------------------------------

def _has_substantive_content(path: Path, artifact_name: str) -> bool:
    """Check whether a change source has substantive content to merge."""
    if not path.exists():
        return False
    if path.is_dir():
        return any(path.iterdir())
    content = path.read_text().strip()
    if not content:
        return False
    # YAML section stubs (chaos-theory-lite): just "name:" or "name: {}"
    if path.suffix == '.yaml':
        stripped = content.replace(' ', '')
        if stripped in (f'{artifact_name}:', f'{artifact_name}:{{}}'):
            return False
    return True


def resolve_artifact_pairs(
    change_dir: Path,
    project_dir: Path,
    config: dict,
) -> list[dict]:
    """Identify change artifacts paired with their project counterparts.

    Iterates ``config["artifacts"]`` and checks each ``change_source``
    for substantive content.

    Returns list of dicts:
        {
            "name": "technical",
            "change_file": Path,
            "project_file": Path,
            "rules": str,
        }
    """
    pairs = []

    for artifact in config['artifacts']:
        change_file = change_dir / artifact['change_source']
        if not _has_substantive_content(change_file, artifact['name']):
            continue

        pairs.append({
            'name': artifact['name'],
            'change_file': change_file,
            'project_file': project_dir / artifact['project_target'],
            'rules': artifact['rules'],
        })

    return pairs


# ---------------------------------------------------------------------------
# System prompt and subagent prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a merge analyst generating structured proposals for merging "
    "OpenSpec change artifacts into project documentation. You have READ-ONLY "
    "access — do NOT modify any files. Analyze both artifacts and produce "
    "a JSON array of merge proposals. "
    "Output ONLY a JSON array to stdout matching the format in the prompt."
)


CONFIDENCE_GUIDANCE = """\
## Confidence Classification

Each proposal must have a `confidence` field:

### "delegate" — mechanical, unambiguous application of merge rules
Use when:
- Capabilities — always append (new capability is always project-level)
- Requirements/scenarios — ADDED/MODIFIED/REMOVED are mechanical operations
- Components/interfaces — append new, update existing in place
- Known risks — append new, remove resolved
- Scope additions — always append
- Decisions — straightforward append with provenance tag, clearly project-level

### "check-in" — requires human judgment
Use when:
- **Objectives** — "Only add if permanent system goals. Most change objectives are transient."
- **Decisions** — scope may be change-specific rather than project-level
- **Testing strategy** — coverage entries or procedures may be superseded by implementation
- **Out of Scope items** — need triage into Out of Scope / Current Limitations / Planned Future Work
- Any content where the merge rule contains "may not", "only if", or "most are"
- Content that could be interpreted as either change-specific or project-level
- Any potential conflict with existing project content"""


def build_merge_prompt(
    pair: dict,
    change_dir: Path,
    project_dir: Path,
    change_name: str,
) -> str:
    """Build the analysis prompt for a single artifact merge subagent."""
    artifact_name = pair['name']
    parts = []

    parts.append("## Assignment\n")
    parts.append(
        f"You are analyzing the `{artifact_name}` artifact from the "
        f"`{change_name}` change to generate merge proposals. Read both the "
        f"change artifact and the existing project artifact, then produce "
        f"structured proposals for each piece of content that should be merged.\n"
    )

    # Change artifact
    parts.append("## Change Artifact (source)\n")
    parts.append(f"Read: `{pair['change_file']}`\n")

    # Project artifact
    parts.append("## Project Artifact (target)\n")
    project_file = pair['project_file']
    if project_file.is_dir() or not project_file.suffix:
        parts.append(f"Read all files under: `{project_file}/`")
        parts.append("(If the directory is empty or missing, this is a first merge.)\n")
    else:
        if project_file.exists():
            parts.append(f"Read: `{project_file}`\n")
        else:
            parts.append(
                f"File `{project_file}` does not exist yet — this is a first merge. "
                f"Treat as merging into an empty document.\n"
            )

    # Merge rules (from config)
    rules = pair.get('rules', '')
    if rules:
        parts.append("## Merge Rules\n")
        parts.append(rules)
        parts.append("")

    # Confidence guidance
    parts.append(CONFIDENCE_GUIDANCE)
    parts.append("")

    # Output format
    parts.append("## Output Format\n")
    parts.append(
        "Output a JSON array of proposals. Each proposal represents one "
        "discrete merge operation:\n\n"
        "[\n"
        "  {\n"
        '    "id": "P-1",\n'
        '    "artifact": "technical.md",\n'
        '    "section": "Decisions",\n'
        '    "action": "append",\n'
        '    "element": "DEC-env-var-over-file-flag",\n'
        '    "content": "<verbatim text to merge>",\n'
        '    "rule": "Append new decisions with [change-slug] provenance tag",\n'
        '    "confidence": "delegate",\n'
        '    "reason": "Unambiguous append of new decision record"\n'
        "  }\n"
        "]\n\n"
        "Field definitions:\n"
        '- `id`: Sequential identifier (P-1, P-2, ...)\n'
        '- `artifact`: Target project file (e.g., "technical.md", "functional.md", '
        '"requirements/<slug>/requirements.feature.md")\n'
        '- `section`: Section within the target file\n'
        '- `action`: One of "append", "update", "remove", "skip"\n'
        '- `element`: Identifier for the content element (decision ID, capability ID, '
        'risk ID, scenario tag, etc.)\n'
        '- `content`: The verbatim text to write (empty string for "remove" and "skip")\n'
        '- `rule`: Which merge rule justifies this action\n'
        '- `confidence`: "delegate" or "check-in"\n'
        '- `reason`: Why this confidence level was chosen\n\n'
        "CRITICAL: Copy all names, identifiers, slugs, tags, and code references "
        "exactly from the source. Never reconstruct from memory.\n\n"
        'Use action "skip" with confidence "check-in" for content you believe '
        "should NOT be merged but want the orchestrator to confirm (e.g., "
        "transient objectives, change-specific decisions)."
    )

    return '\n'.join(parts)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

async def run_merge_proposals(
    change_dir: Path,
    project_dir: Path,
    pairs: list[dict],
    change_name: str,
    max_concurrent: int,
    timeout: int,
    budget: float | None,
    dry_run: bool,
) -> dict:
    """Launch parallel Sonnet subagents and collect merge proposals."""

    if dry_run:
        for pair in pairs:
            prompt = build_merge_prompt(pair, change_dir, project_dir, change_name)
            cmd = build_command(
                change_dir, project_dir,
                SYSTEM_PROMPT, 'sonnet', budget,
                tools='Read',
            )
            print(f"\n{'=' * 60}", file=sys.stderr)
            print(f"MERGE: {pair['name']} → {pair['project_file'].name}", file=sys.stderr)
            print(f"CHANGE: {pair['change_file']}", file=sys.stderr)
            print(f"PROJECT: {pair['project_file']}", file=sys.stderr)
            print(f"CMD: {cmd[:6]}...", file=sys.stderr)
            print(f"PROMPT:\n{prompt}", file=sys.stderr)
        return {
            'change': change_name,
            'project': project_dir.name,
            'artifacts_analyzed': 0,
            'proposals': [],
            'failures': [],
            'dry_run': True,
        }

    semaphore = asyncio.Semaphore(max_concurrent)
    completed = 0
    total = len(pairs)

    def on_complete():
        nonlocal completed
        completed += 1
        print(f"[PROGRESS] {completed}/{total} artifacts complete", file=sys.stderr)

    tasks = []
    names = []

    for pair in pairs:
        prompt = build_merge_prompt(pair, change_dir, project_dir, change_name)
        cmd = build_command(
            change_dir, project_dir,
            SYSTEM_PROMPT, 'sonnet', budget,
            tools='Read',
        )
        tasks.append(run_one_subprocess(
            f"merge:{pair['name']}", cmd, prompt, timeout, semaphore,
        ))
        names.append(pair['name'])

    results = await gather_with_callback(tasks, on_complete)

    all_proposals = []
    failures = []
    proposal_counter = 0

    for i, result in enumerate(results):
        name = names[i]
        if result['status'] == 'success':
            proposals = result.get('report', [])
            # Re-number proposal IDs to be globally unique
            for p in proposals:
                proposal_counter += 1
                p['id'] = f'P-{proposal_counter}'
            all_proposals.extend(proposals)
            print(f"[MERGE] {name}: {len(proposals)} proposals", file=sys.stderr)
        else:
            failures.append({
                'name': f'merge:{name}',
                'error': result.get('error', 'unknown'),
            })
            print(f"[MERGE] {name}: FAILED — {result.get('error', 'unknown')}",
                  file=sys.stderr)

    return {
        'change': change_name,
        'project': project_dir.name,
        'artifacts_analyzed': total - len(failures),
        'proposals': all_proposals,
        'failures': failures,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None):
    args = parse_args(argv)
    change_dir = args.change_dir.resolve()

    if not change_dir.exists():
        print(f"ERROR: Change directory not found: {change_dir}",
              file=sys.stderr)
        sys.exit(1)

    if not args.dry_run and not shutil.which('claude'):
        print("ERROR: claude CLI not found in PATH", file=sys.stderr)
        sys.exit(1)

    # Extract sections from spec.yaml if present (chaos-theory-lite schema)
    if (change_dir / 'spec.yaml').exists():
        from split_spec import split_spec
        extracted = split_spec(change_dir)
        if extracted:
            print(f"Extracted {len(extracted)} sections from spec.yaml",
                  file=sys.stderr)

    # Resolve project directory
    project_dir = resolve_project_dir(change_dir)
    if not project_dir:
        print("ERROR: Could not resolve project directory from .openspec.yaml",
              file=sys.stderr)
        sys.exit(1)

    # Load schema-keyed merge config
    try:
        config = load_merge_config(change_dir)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # Find artifact pairs with substantive content
    pairs = resolve_artifact_pairs(change_dir, project_dir, config)
    if not pairs:
        print("No artifacts with substantive content found.", file=sys.stderr)
        result = {
            'change': change_dir.name,
            'project': project_dir.name,
            'artifacts_analyzed': 0,
            'proposals': [],
            'failures': [],
        }
        print(json.dumps(result, indent=2))
        return

    change_name = change_dir.name
    print(f"\n=== Generating merge proposals for {change_name} ===",
          file=sys.stderr)
    print(f"Project: {project_dir.name}", file=sys.stderr)
    print(f"Artifacts: {', '.join(p['name'] for p in pairs)}", file=sys.stderr)

    result = asyncio.run(run_merge_proposals(
        change_dir, project_dir, pairs, change_name,
        args.max_concurrent, args.timeout, args.budget, args.dry_run,
    ))

    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
