#!/usr/bin/env python3
"""
Parallel resolver orchestrator for OpenSpec gap resolution.

Launches claude -p processes in parallel, one per file group, to resolve gaps
with isolated write access. Three phases:
  1. Primary resolve: each resolver writes only its assigned file
  2. Propagation: each file checks if cross-file changes require updates
  3. Collation: single process updates gaps.md and resolved.md

Usage:
    python run_resolvers.py <change_dir> [--max-concurrent N] [--timeout S] [--dry-run]
"""

import argparse
import asyncio
import json
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Run per-file gap resolvers in parallel via claude -p'
    )
    parser.add_argument('change_dir', type=Path,
                        help='Path to OpenSpec change directory')
    parser.add_argument('--max-concurrent', type=int, default=6,
                        help='Maximum parallel claude -p processes (default: 6)')
    parser.add_argument('--timeout', type=int, default=600,
                        help='Timeout per resolver in seconds (default: 600)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print prompts and commands without launching processes')
    parser.add_argument('--budget', type=float, default=None,
                        help='Max budget per resolver in USD')
    return parser.parse_args(argv)


from spec_utils import (
    build_command,
    clear_gap_field,
    gather_with_callback,
    load_schema_artifacts,
    lookup_artifact,
    move_gap_to_resolved,
    parse_gaps,
    read_gap_entries,
    resolve_project_dir,
    resolve_skill_content,
    run_one_subprocess,
    try_parse_json,
    write_gap_field,
)


def run_group_gaps(change_dir: Path) -> dict:
    """Call group_gaps.py and parse its JSON output."""
    script = Path(__file__).parent / 'group_gaps.py'
    result = subprocess.run(
        [sys.executable, str(script), str(change_dir)],
        capture_output=True, text=True,
    )
    if result.stderr:
        print(result.stderr, end='', file=sys.stderr)
    if result.returncode != 0:
        print(f"ERROR: group_gaps.py exited with code {result.returncode}",
              file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def run_resolve_artifacts(change_dir: Path) -> dict:
    """Call resolve_artifacts.py and parse its JSON output."""
    script = Path(__file__).parent / 'resolve_artifacts.py'
    result = subprocess.run(
        [sys.executable, str(script), str(change_dir)],
        capture_output=True, text=True,
    )
    if result.stderr:
        print(result.stderr, end='', file=sys.stderr)
    if result.returncode != 0:
        print(f"ERROR: resolve_artifacts.py exited with code {result.returncode}",
              file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


COMMON_RESOLVER_SKILLS = [
    'tokamak:managing-spec-gaps',
]


def build_resolve_prompt(
    assigned_file: str,
    gap_ids: list[str],
    gap_entries: str,
    change_dir: Path,
    artifact_files: list[str],
    project_dir: Path | None,
) -> str:
    """Build prompt for a primary resolver."""
    parts = []

    parts.append("## Assignment\n")
    parts.append(f"You are resolving these gaps by modifying `{assigned_file}`:")
    for gid in gap_ids:
        parts.append(f"- {gid}")
    parts.append("")

    # File purpose from schema
    schema_artifacts = load_schema_artifacts(change_dir)
    artifact_config = lookup_artifact(schema_artifacts, assigned_file)
    if artifact_config:
        parts.append("## File Purpose\n")
        parts.append(
            f"The following instruction guided the original creation of `{assigned_file}`. "
            "Use it to understand what content belongs in this file:\n"
        )
        parts.append(artifact_config['instruction'])
        parts.append("")

    parts.append("## Gap Details\n")
    parts.append(gap_entries)
    parts.append("")

    parts.append("## Artifact Files (read-only context)\n")
    parts.append(f"Read these files from `{change_dir}/` for context:")
    for f in artifact_files:
        if f != assigned_file:
            parts.append(f"- `{change_dir}/{f}` (read-only)")
    parts.append(f"- `{change_dir}/{assigned_file}` (READ and WRITE)")
    parts.append("")

    if project_dir:
        parts.append("## Project Reference Files (read-only context)\n")
        parts.append(f"Read from `{project_dir}/` for consistency checks:")
        for f in ['functional.md', 'technical.md', 'infra.md']:
            pf = project_dir / f
            if pf.exists():
                parts.append(f"- `{project_dir}/{f}`")
        req_dir = project_dir / 'requirements'
        if req_dir.is_dir():
            for rf in sorted(req_dir.rglob('*.feature.md')):
                parts.append(f"- `{rf}`")
        parts.append("")

    # Skills guidance — schema-driven per-file skills + common skills
    skill_names = list(COMMON_RESOLVER_SKILLS)
    if artifact_config:
        for s in artifact_config['skills']:
            if s not in skill_names:
                skill_names.append(s)

    parts.append("## Skills Guidance\n")
    for skill_name in skill_names:
        content = resolve_skill_content(skill_name)
        if content:
            parts.append(f"### {skill_name}\n")
            parts.append(content)
            parts.append("")

    parts.append("## Instructions\n")
    parts.append(
        "As an experienced software architect, resolve each assigned gap by "
        "modifying the assigned file.\n"
        "1. For each gap, read the Decision field and merge it into the artifact\n"
        "2. Ensure the modification is consistent with all other artifacts\n"
        "3. Check for cascading impacts within the assigned file\n"
        "4. Do NOT modify any file other than the assigned file\n"
    )

    return '\n'.join(parts)


RESOLVE_SYSTEM_PROMPT = (
    "You MUST only write to the assigned file specified in the prompt. "
    "Output a JSON resolution report to stdout after completing all modifications.\n\n"
    "## Placement Assessment\n\n"
    "Before resolving each gap, assess whether the gap's Decision content belongs "
    "in this file using the File Purpose section from the prompt:\n"
    "- `natural`: Decision content directly serves this file's purpose\n"
    "- `forced`: Content doesn't naturally fit but could be restructured to fit\n"
    "- `mismatch`: Content belongs in a different artifact entirely\n\n"
    "If placement_fit is `forced` or `mismatch`:\n"
    "- Do NOT modify the file\n"
    "- Use action: \"placement-rejected\"\n"
    "- In outcome: explain what file the content likely belongs in and why\n\n"
    "## Resolution Report Format\n\n"
    "Resolution report format (JSON list):\n"
    "[\n"
    '  {\n'
    '    "gap": "GAP-197",\n'
    '    "action": "resolved",\n'
    '    "placement_fit": "natural",\n'
    '    "decision": "...",\n'
    '    "outcome": "Description of what changed in the file",\n'
    '    "changes_summary": "file.md section: description of change",\n'
    '    "diff": "+12/-3 file.md"\n'
    '  }\n'
    "]\n\n"
    "For each resolved gap, include a 'diff' field with per-file line counts:\n"
    "Count both lines added and lines removed in the assigned file.\n"
    'Example: "+12/-3 infra.md" or "+24/-7 requirements/dep-mapping/requirements.feature.md"\n\n'
    "For placement-rejected gaps:\n"
    "[\n"
    '  {\n'
    '    "gap": "GAP-42",\n'
    '    "action": "placement-rejected",\n'
    '    "placement_fit": "mismatch",\n'
    '    "decision": "...",\n'
    '    "outcome": "Decision describes X. This belongs in Y, not Z."\n'
    '  }\n'
    "]\n\n"
    "If a gap cannot be resolved in the assigned file for other reasons, "
    "use action: \"skipped\" with an explanation in the outcome field."
)


def build_propagation_prompt(
    assigned_file: str,
    primary_reports: list[dict],
    change_dir: Path,
    project_dir: Path | None,
) -> str:
    """Build prompt for propagation phase resolver."""
    parts = []

    parts.append("## Propagation Check\n")
    parts.append(
        f"Review the resolution reports below and check if `{assigned_file}` "
        f"needs updates based on cross-file changes.\n"
    )

    # File purpose from schema
    schema_artifacts = load_schema_artifacts(change_dir)
    artifact_config = lookup_artifact(schema_artifacts, assigned_file)
    if artifact_config:
        parts.append("## File Purpose\n")
        parts.append(
            f"The following instruction guided the original creation of `{assigned_file}`. "
            "Use it to understand what content belongs in this file:\n"
        )
        parts.append(artifact_config['instruction'])
        parts.append("")

    parts.append("## Primary Resolution Reports\n")
    for report in primary_reports:
        parts.append(f"### {report['file']}\n")
        parts.append("```json")
        parts.append(json.dumps(report['report'], indent=2))
        parts.append("```\n")

    parts.append("## Files\n")
    parts.append(f"- `{change_dir}/{assigned_file}` (READ and WRITE)")
    parts.append("")

    if project_dir:
        parts.append("## Project Reference (read-only)\n")
        for f in ['functional.md', 'technical.md', 'infra.md']:
            pf = project_dir / f
            if pf.exists():
                parts.append(f"- `{project_dir}/{f}`")
        parts.append("")

    # Skills guidance — schema-driven per-file skills
    skill_names = list(COMMON_RESOLVER_SKILLS)
    if artifact_config:
        for s in artifact_config['skills']:
            if s not in skill_names:
                skill_names.append(s)

    if skill_names:
        parts.append("## Skills Guidance\n")
        for skill_name in skill_names:
            content = resolve_skill_content(skill_name)
            if content:
                parts.append(f"### {skill_name}\n")
                parts.append(content)
                parts.append("")

    parts.append("## Instructions\n")
    parts.append(
        "Check if your file needs updates based on the cross-file changes "
        "described in the resolution reports above.\n"
        "- If a new requirement was added, check coverage tables and checklists\n"
        "- If a capability was rewritten, check references to it\n"
        "- If a decision was recorded, check consistency\n"
        "- Only make changes that are necessary for consistency\n"
    )

    return '\n'.join(parts)


PROPAGATION_SYSTEM_PROMPT = (
    "You MUST only write to the assigned file specified in the prompt. "
    "Output a JSON list of additional resolution entries to stdout.\n\n"
    "Format: [{\"gap\": \"GAP-XX\", \"action\": \"propagated\", "
    "\"outcome\": \"description\", \"changes_summary\": \"file section: change\"}]\n\n"
    "If no propagation is needed, output: []"
)




async def run_primary_phase(
    grouping: dict,
    change_dir: Path,
    artifact_files: list[str],
    project_dir: Path | None,
    max_concurrent: int,
    timeout: int,
    budget: float | None,
    dry_run: bool,
    on_complete: callable = None,
) -> list[dict]:
    """Phase 1: Primary resolution — one resolver per file group."""
    groups = grouping.get('groups', {})
    gap_lifecycle = grouping.get('gap_lifecycle', [])

    if not groups and not gap_lifecycle:
        print("No gaps to resolve (no file groups or lifecycle gaps).",
              file=sys.stderr)
        return []

    if dry_run:
        for assigned_file, gap_ids in groups.items():
            gap_entries = read_gap_entries(change_dir, gap_ids)
            prompt = build_resolve_prompt(
                assigned_file, gap_ids, gap_entries,
                change_dir, artifact_files, project_dir,
            )
            cmd = build_command(
                change_dir, project_dir,
                RESOLVE_SYSTEM_PROMPT, 'opus', budget,
                tools='Read,Edit,Write',
            )
            print(f"\n{'=' * 60}", file=sys.stderr)
            print(f"RESOLVER: {assigned_file} ({len(gap_ids)} gaps)",
                  file=sys.stderr)
            print(f"GAPS: {', '.join(gap_ids)}", file=sys.stderr)
            print(f"CMD: {cmd[:6]}...", file=sys.stderr)
            print(f"PROMPT:\n{prompt}", file=sys.stderr)
        return []

    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = []

    for assigned_file, gap_ids in groups.items():
        gap_entries = read_gap_entries(change_dir, gap_ids)
        prompt = build_resolve_prompt(
            assigned_file, gap_ids, gap_entries,
            change_dir, artifact_files, project_dir,
        )
        cmd = build_command(
            change_dir, project_dir,
            RESOLVE_SYSTEM_PROMPT, 'opus', budget,
            tools='Read,Edit,Write',
        )
        tasks.append(run_one_subprocess(
            f"resolve:{assigned_file}", cmd, prompt, timeout, semaphore,
        ))

    results = await gather_with_callback(tasks, on_complete)

    # Attach file info to results
    file_list = list(groups.keys())
    for i, result in enumerate(results):
        result['file'] = file_list[i]

    succeeded = sum(1 for r in results if r['status'] == 'success')
    failed = len(results) - succeeded
    print(f"\n--- Primary phase: {succeeded}/{len(results)} resolvers succeeded ---",
          file=sys.stderr)
    if failed > 0:
        for r in results:
            if r['status'] != 'success':
                print(f"  FAILED: {r['name']}: {r.get('error', 'unknown')}",
                      file=sys.stderr)

    return list(results)


async def run_propagation_phase(
    primary_results: list[dict],
    change_dir: Path,
    project_dir: Path | None,
    max_concurrent: int,
    timeout: int,
    budget: float | None,
    dry_run: bool,
    on_complete: callable = None,
) -> list[dict]:
    """Phase 2: Propagation — each file checks for cross-file updates."""
    # Only propagate to files that had successful primary resolvers
    successful = [r for r in primary_results if r['status'] == 'success']
    if len(successful) < 2:
        # No cross-file propagation needed with 0 or 1 files
        print("(skipped — single file, no cross-file propagation needed)",
              file=sys.stderr)
        return []

    # Build report summaries for each successful resolver
    report_summaries = [
        {'file': r['file'], 'report': r['report']}
        for r in successful
    ]

    if dry_run:
        for result in successful:
            prompt = build_propagation_prompt(
                result['file'], report_summaries,
                change_dir, project_dir,
            )
            cmd = build_command(
                change_dir, project_dir,
                PROPAGATION_SYSTEM_PROMPT, 'sonnet', budget,
                tools='Read,Edit,Write',
            )
            print(f"\n{'=' * 60}", file=sys.stderr)
            print(f"PROPAGATION: {result['file']}", file=sys.stderr)
            print(f"CMD: {cmd[:6]}...", file=sys.stderr)
            print(f"PROMPT:\n{prompt}", file=sys.stderr)
        return []

    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = []

    for result in successful:
        prompt = build_propagation_prompt(
            result['file'], report_summaries,
            change_dir, project_dir,
        )
        cmd = build_command(
            change_dir, project_dir,
            PROPAGATION_SYSTEM_PROMPT, 'sonnet', budget,
            tools='Read,Edit,Write',
        )
        tasks.append(run_one_subprocess(
            f"propagate:{result['file']}", cmd, prompt, timeout, semaphore,
        ))

    results = await gather_with_callback(tasks, on_complete)

    for i, result in enumerate(results):
        result['file'] = successful[i]['file']

    succeeded = sum(1 for r in results if r['status'] == 'success')
    print(f"\n--- Propagation phase: {succeeded}/{len(results)} succeeded ---",
          file=sys.stderr)

    return list(results)


def collate_reports(
    primary_results: list[dict],
    propagation_results: list[dict],
    gap_lifecycle: list[str],
    change_dir: Path,
    dry_run: bool = False,
) -> dict:
    """Phase 3: Deterministic collation — update gaps.md and resolved.md.

    Processes resolver JSON reports directly using spec_utils primitives
    instead of delegating to an LLM subprocess.
    """
    # Merge all report entries
    all_entries: list[dict] = []

    for r in primary_results:
        if r['status'] == 'success':
            for entry in r.get('report', []):
                entry['phase'] = 'primary'
                entry['source_file'] = r['file']
                all_entries.append(entry)

    for r in propagation_results:
        if r['status'] == 'success':
            for entry in r.get('report', []):
                entry['phase'] = 'propagation'
                entry['source_file'] = r['file']
                all_entries.append(entry)

    for gap_id in gap_lifecycle:
        all_entries.append({
            'gap': gap_id,
            'action': 'lifecycle',
            'phase': 'lifecycle',
            'outcome': 'Gap lifecycle change (supersession/deprecation)',
        })

    if not all_entries:
        print("No resolution reports to collate.", file=sys.stderr)
        return {'resolved': 0, 'skipped': 0, 'placement_rejected': 0, 'conflicts': []}

    # Group by gap_id for conflict detection
    gap_reports: dict[str, list[dict]] = {}
    for entry in all_entries:
        gap_id = entry.get('gap', '')
        if gap_id:
            gap_reports.setdefault(gap_id, []).append(entry)

    # Detect conflicts: same gap with different non-propagated actions
    conflicts: list[dict] = []
    for gap_id, entries in gap_reports.items():
        actions = {e.get('action') for e in entries}
        # propagated alongside resolved is expected, not a conflict
        non_propagated = actions - {'propagated'}
        if len(non_propagated) > 1:
            conflicts.append({
                'gap': gap_id,
                'issue': f"Multiple actions: {', '.join(sorted(actions))}",
            })

    if dry_run:
        entry_count = len(all_entries)
        conflict_count = len(conflicts)
        print(f"\n{'=' * 60}", file=sys.stderr)
        print("COLLATION (deterministic)", file=sys.stderr)
        print(f"ENTRIES: {entry_count}", file=sys.stderr)
        print(f"CONFLICTS: {conflict_count}", file=sys.stderr)
        for gap_id in gap_reports:
            actions = [e.get('action') for e in gap_reports[gap_id]]
            print(f"  {gap_id}: {', '.join(actions)}", file=sys.stderr)
        return {'resolved': 0, 'skipped': 0, 'placement_rejected': 0, 'conflicts': conflicts}

    # Process entries
    resolved_count = 0
    skipped_count = 0
    placement_rejected_count = 0
    already_moved: set[str] = set()
    conflicted_ids = {c['gap'] for c in conflicts}

    for gap_id, entries in gap_reports.items():
        if gap_id in conflicted_ids:
            print(f"[CONFLICT] {gap_id}: skipping due to conflicting actions",
                  file=sys.stderr)
            continue

        for entry in entries:
            action = entry.get('action', '')
            outcome = entry.get('outcome', '')
            diff = entry.get('diff', '')

            if diff and outcome:
                outcome = f"{outcome} [diff: {diff}]"

            if action == 'resolved':
                if gap_id not in already_moved:
                    try:
                        move_gap_to_resolved(change_dir, gap_id, 'resolved', outcome)
                        already_moved.add(gap_id)
                        resolved_count += 1
                        print(f"[RESOLVED] {gap_id} → resolved.md",
                              file=sys.stderr)
                    except ValueError as e:
                        print(f"[WARN] Could not move {gap_id}: {e}", file=sys.stderr)

            elif action == 'propagated':
                if gap_id not in already_moved:
                    try:
                        move_gap_to_resolved(change_dir, gap_id, 'resolved', outcome)
                        already_moved.add(gap_id)
                        resolved_count += 1
                        print(f"[RESOLVED] {gap_id} → resolved.md",
                              file=sys.stderr)
                    except ValueError as e:
                        print(f"[WARN] Could not move {gap_id}: {e}", file=sys.stderr)

            elif action == 'placement-rejected':
                placement_fit = entry.get('placement_fit', 'unknown')
                source_file = entry.get('source_file', 'unknown')

                try:
                    gaps_content = (change_dir / 'gaps.md').read_text()
                    existing_gaps = parse_gaps(gaps_content)
                    gap_data = next((g for g in existing_gaps if g['id'] == gap_id), None)

                    if gap_data and gap_data.get('placement_result'):
                        # Second rejection — circuit break
                        prior = gap_data['placement_result']
                        prior_file = prior.split('—')[0].strip() if '—' in prior else 'unknown'
                        write_gap_field(
                            change_dir, gap_id, 'Placement-result',
                            f"Circuit break: rejected from {prior_file} and {source_file}, "
                            "escalating to user check-in",
                        )
                        write_gap_field(change_dir, gap_id, 'Triage', 'check-in')
                        clear_gap_field(change_dir, gap_id, 'Decision')
                    else:
                        # First rejection
                        write_gap_field(
                            change_dir, gap_id, 'Placement-result',
                            f"{placement_fit} — {outcome}",
                        )

                    placement_rejected_count += 1
                    print(f"[PLACEMENT-REJECTED] {gap_id} → placement-result updated",
                          file=sys.stderr)
                except (ValueError, StopIteration) as e:
                    print(f"[WARN] placement-rejected for {gap_id}: {e}",
                          file=sys.stderr)

            elif action == 'lifecycle':
                if gap_id not in already_moved:
                    try:
                        move_gap_to_resolved(change_dir, gap_id, 'resolved', outcome)
                        already_moved.add(gap_id)
                        resolved_count += 1
                        print(f"[LIFECYCLE] {gap_id} → resolved.md",
                              file=sys.stderr)
                    except ValueError as e:
                        print(f"[WARN] Could not move {gap_id}: {e}", file=sys.stderr)

            elif action == 'skipped':
                skipped_count += 1
                print(f"[SKIPPED] {gap_id}", file=sys.stderr)

    print(f"\n--- Collation: {resolved_count} resolved, {skipped_count} skipped, "
          f"{placement_rejected_count} placement-rejected, "
          f"{len(conflicts)} conflicts ---", file=sys.stderr)

    return {
        'resolved': resolved_count,
        'skipped': skipped_count,
        'placement_rejected': placement_rejected_count,
        'conflicts': conflicts,
    }


async def run_all_phases(
    change_dir: Path,
    max_concurrent: int,
    timeout: int,
    budget: float | None,
    dry_run: bool,
    on_complete: callable = None,
) -> dict:
    """Orchestrate all three resolution phases."""
    # Get gap grouping
    grouping = run_group_gaps(change_dir)

    ungrouped = grouping.get('ungrouped', [])
    if ungrouped:
        print(f"WARNING: {len(ungrouped)} gaps missing Primary-file: "
              f"{', '.join(ungrouped)}", file=sys.stderr)

    # Get artifact files for context
    artifacts_data = run_resolve_artifacts(change_dir)
    artifact_files = artifacts_data.get('files', [])

    project_dir = resolve_project_dir(change_dir)

    # Phase 1: Primary resolve
    print("\n=== Phase 1: Primary Resolution ===", file=sys.stderr)
    primary_results = await run_primary_phase(
        grouping, change_dir, artifact_files, project_dir,
        max_concurrent, timeout, budget, dry_run,
        on_complete=on_complete,
    )

    # Phase 2: Propagation
    print("\n=== Phase 2: Propagation ===", file=sys.stderr)
    propagation_results = await run_propagation_phase(
        primary_results, change_dir, project_dir,
        max_concurrent, timeout, budget, dry_run,
    )

    # Phase 3: Collation (deterministic — no subprocess needed)
    print("\n=== Phase 3: Collation ===", file=sys.stderr)
    gap_lifecycle = grouping.get('gap_lifecycle', [])
    collation = collate_reports(
        primary_results, propagation_results, gap_lifecycle,
        change_dir, dry_run=dry_run,
    )

    # Build final summary
    summary = {
        'grouping': grouping,
        'primary': {
            'total': len(primary_results),
            'succeeded': sum(1 for r in primary_results if r['status'] == 'success'),
            'failed': sum(1 for r in primary_results if r['status'] != 'success'),
            'results': [
                {'name': r['name'], 'file': r.get('file', ''),
                 'status': r['status'], 'report': r.get('report', [])}
                for r in primary_results
            ],
        },
        'propagation': {
            'total': len(propagation_results),
            'succeeded': sum(1 for r in propagation_results if r['status'] == 'success'),
            'results': [
                {'name': r['name'], 'file': r.get('file', ''),
                 'status': r['status'], 'report': r.get('report', [])}
                for r in propagation_results
            ],
        },
        'collation': collation,
    }

    return summary


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

    result = asyncio.run(run_all_phases(
        change_dir, args.max_concurrent, args.timeout,
        args.budget, args.dry_run,
    ))

    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
