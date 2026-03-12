#!/usr/bin/env python3
"""
Parallel critic orchestrator for OpenSpec workflow.

Launches claude -p processes in parallel to run critics deterministically.
Replaces unreliable "launch N Task calls in a single message" approach.

Usage:
    python run_critics.py <change_dir> [--max-concurrent N] [--timeout S] [--dry-run]
    python run_critics.py <change_dir> --show-prompt [--critic Name]
    python run_critics.py <change_dir> --show-team-guidance
"""

import argparse
import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


from spec_utils import (
    gather_with_callback,
    load_schema_artifacts,
    resolve_project_dir,
)


ACCURACY_CRITICS = frozenset({
    "Capability Accuracy",
    "Requirement Accuracy",
    "Architecture Accuracy",
    "Decision Plausibility",
    "Infrastructure Accuracy",
    "Error UX",
})


def _load_skillbook(sb_path: Path, strip_headings: bool = False) -> str:
    """Read skillbook JSON, return skills content as formatted text.

    Uses ACE's canonical formatter when available; falls back to simple
    concatenation for environments without ace-framework.
    Handles both dict (ACE-native) and list (legacy) skill formats.
    """
    if not sb_path.exists():
        return ''
    # Read JSON once — reused by both ACE path and manual reader
    try:
        with open(sb_path) as f:
            sb_data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return ''
    # Manual reader: handles both dict and list formats, plus section_order
    skills = sb_data.get('skills', {})
    if isinstance(skills, list):
        return '\n\n'.join(s['content'] for s in skills if 'content' in s) or ''
    if not isinstance(skills, dict):
        return ''
    sections = sb_data.get('sections', {})
    if not sections:
        # No sections defined — flat concatenation (backward compat)
        return '\n\n'.join(
            s['content'] for s in skills.values()
            if isinstance(s, dict) and 'content' in s
        ) or ''
    # Section-aware rendering (explicit order if provided, else dict order)
    section_order = sb_data.get('section_order')
    if isinstance(section_order, list):
        ordered = list(dict.fromkeys(section_order))  # dedupe, preserve order
        # Append any sections not listed in section_order
        for name in sections:
            if name not in ordered:
                ordered.append(name)
    else:
        ordered = list(sections.keys())
    parts = []
    rendered_ids = set()
    for section_name in ordered:
        skill_ids = sections.get(section_name)
        if not skill_ids:
            continue
        heading = section_name.replace('-', ' ').replace('_', ' ').title()
        section_parts = []
        for sid in skill_ids:
            skill = skills.get(sid)
            if isinstance(skill, dict) and 'content' in skill:
                section_parts.append(skill['content'])
                rendered_ids.add(sid)
        if section_parts:
            if not strip_headings:
                parts.append(f"## {heading}\n")
            parts.append('\n\n'.join(section_parts))
    # Fallback: skills not in any section
    for sid, skill in skills.items():
        if sid not in rendered_ids and isinstance(skill, dict) and 'content' in skill:
            parts.append(skill['content'])
    return '\n\n'.join(parts) or ''


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Run OpenSpec critics in parallel via claude -p'
    )
    parser.add_argument('change_dir', type=Path, nargs='?', default=None,
                        help='Path to OpenSpec change directory')
    parser.add_argument('--max-concurrent', type=int, default=6,
                        help='Maximum parallel claude -p processes (default: 6)')
    parser.add_argument('--timeout', type=int, default=600,
                        help='Timeout per critic in seconds (default: 600)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print prompts and commands without launching processes')
    parser.add_argument('--budget', type=float, default=None,
                        help='Max budget per critic in USD')
    parser.add_argument('--type', default='critics', dest='config_type',
                        help='Config type to load (default: critics). '
                             'Resolves <type>.<schema>.json')
    parser.add_argument('--show-prompt', action='store_true',
                        help='Print assembled prompts to stdout and exit')
    parser.add_argument('--show-team-guidance', action='store_true',
                        help='Print rendered team coordination guidance and exit')
    parser.add_argument('--critic', default=None,
                        help='Filter to a single critic by name '
                             '(use with --show-prompt or --dry-run)')
    return parser.parse_args(argv)


def select_critics(change_dir: Path, config_type: str = 'critics') -> dict:
    """Call select_critics.py and parse its JSON output."""
    script = Path(__file__).parent / 'select_critics.py'
    cmd = [sys.executable, str(script), str(change_dir)]
    if config_type != 'critics':
        cmd.extend(['--type', config_type])
    result = subprocess.run(
        cmd,
        capture_output=True, text=True,
    )
    if result.stderr:
        print(result.stderr, end='', file=sys.stderr)
    if result.returncode != 0:
        print(f"ERROR: select_critics.py exited with code {result.returncode}",
              file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def is_accuracy_critic(name: str) -> bool:
    return name in ACCURACY_CRITICS


def build_prompt(critic: dict, change_dir: Path,
                 project_dir: Path | None,
                 skillbook_context: str = '',
                 team_context: str = '') -> str:
    """Construct the evaluation prompt for a single critic."""
    parts = []

    # Artifact evaluation guidance (shared per file type)
    seen_artifacts = set()
    for f in critic['files']:
        stem = Path(f.replace('.feature', '')).stem  # integration.feature.md → integration
        if stem in seen_artifacts:
            continue
        seen_artifacts.add(stem)
        artifact_sb = ACE_DIR / 'artifacts' / f'{stem}.json'
        artifact_ctx = _load_skillbook(artifact_sb, strip_headings=True)
        if artifact_ctx:
            parts.append(f"## Artifact Guidance: {stem}\n")
            parts.append(artifact_ctx)
            parts.append("")

    parts.append("## Evaluation Criteria\n")
    parts.append(skillbook_context)
    parts.append("")

    if team_context:
        parts.append("## Team Coordination Guidance\n")
        parts.append(team_context)
        parts.append("")

    # Files to evaluate (relative to change_dir)
    parts.append("## Files to evaluate\n")
    parts.append(f"Read these files from `{change_dir}/`:")
    for f in critic['files']:
        parts.append(f"- `{change_dir}/{f}`")
    parts.append("")

    # Schema artifact instructions (for critics that reference FILE PURPOSE)
    if 'FILE PURPOSE' in skillbook_context:
        schema_artifacts = load_schema_artifacts(change_dir)
        if schema_artifacts:
            parts.append("## File Purpose Instructions\n")
            parts.append(
                "The following instructions from schema.yaml define what content "
                "belongs in each artifact file:\n"
            )
            for generates, config in schema_artifacts.items():
                parts.append(f"### `{generates}`\n")
                parts.append(config['instruction'])
                parts.append("")

    # Project reference files
    if critic.get('project_files') and project_dir:
        parts.append("## Project Reference Files (read-only context)\n")
        parts.append(
            "The following files are from the living project documentation. "
            "Use them as reference to identify conflicts, but do NOT modify them."
        )
        parts.append(f"\nRead from `{project_dir}/`:")
        for f in critic['project_files']:
            parts.append(f"- `{project_dir}/{f}`")
        parts.append("")

    # Accuracy critic: codebase exploration instructions
    if is_accuracy_critic(critic['name']):
        project_root = change_dir.parent.parent.parent
        parts.append("## Codebase Exploration\n")
        parts.append(
            f"You have access to Read, Glob, and Grep tools. "
            f"The project root is `{project_root}`. "
            f"Use these tools to explore the actual codebase and cross-reference "
            f"against the documentation."
        )
        parts.append("")

    # Existing gaps
    parts.append("## Existing Gaps (do not duplicate)\n")
    parts.append("Read these files to check for already-documented gaps:")
    parts.append(f"- `{change_dir}/gaps.md`")
    parts.append(f"- `{change_dir}/resolved.md`")
    parts.append("")
    parts.append("Do not submit gaps already covered in gaps.md or resolved.md.")
    parts.append("One quality gap is more valuable than ten covered or nitpick gaps.")

    return "\n".join(parts)


def build_command(critic: dict, change_dir: Path,
                  project_dir: Path | None,
                  output_template: str,
                  budget: float | None) -> list[str]:
    """Build the claude -p command for a single critic."""
    claude = shutil.which('claude')
    if not claude:
        print("ERROR: claude CLI not found in PATH", file=sys.stderr)
        sys.exit(1)

    cmd = [claude, '-p']

    cmd.extend(['--model', critic['model']])

    # Tool set: accuracy critics get exploration tools
    if is_accuracy_critic(critic['name']):
        cmd.extend(['--tools', 'Read,Glob,Grep'])
    else:
        cmd.extend(['--tools', 'Read'])

    cmd.extend(['--permission-mode', 'bypassPermissions'])
    cmd.append('--no-session-persistence')
    cmd.extend(['--output-format', 'json'])

    # Grant filesystem access
    cmd.extend(['--add-dir', str(change_dir)])
    if project_dir:
        cmd.extend(['--add-dir', str(project_dir)])
    if is_accuracy_critic(critic['name']):
        project_root = change_dir.parent.parent.parent
        cmd.extend(['--add-dir', str(project_root)])

    if output_template:
        cmd.extend(['--append-system-prompt', output_template])

    if budget is not None:
        cmd.extend(['--max-budget-usd', str(budget)])

    effort = critic.get('effort')
    if effort:
        cmd.extend(['--effort', effort])

    # Prompt is passed via stdin (avoids shell argument length limits)
    return cmd


async def run_one_critic(
    critic: dict,
    cmd: list[str],
    prompt: str,
    timeout: int,
    semaphore: asyncio.Semaphore,
) -> dict:
    """Launch a single claude -p process and collect output."""
    async with semaphore:
        name = critic['name']
        print(f"[RUNNING] {name} ({critic['model']})", file=sys.stderr)

        env = {k: v for k, v in os.environ.items() if k != 'CLAUDECODE'}

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=prompt.encode()),
                timeout=timeout,
            )

            stdout_text = stdout.decode().strip()
            stderr_text = stderr.decode().strip()

            # Parse JSON output for text and usage telemetry
            output_text = stdout_text
            usage = {}
            try:
                parsed = json.loads(stdout_text)
                output_text = parsed.get('result', stdout_text)
                model_usage = parsed.get('modelUsage', {})
                usage = {
                    'inputTokens': sum(
                        u.get('inputTokens', 0) for u in model_usage.values()
                    ),
                    'outputTokens': sum(
                        u.get('outputTokens', 0) for u in model_usage.values()
                    ),
                    'cacheReadInputTokens': sum(
                        u.get('cacheReadInputTokens', 0)
                        for u in model_usage.values()
                    ),
                    'num_turns': parsed.get('num_turns', 0),
                }
            except (json.JSONDecodeError, AttributeError):
                pass  # Fall back to raw stdout

            if proc.returncode == 0:
                print(f"[SUCCESS] {name}", file=sys.stderr)
                result = {
                    'name': name,
                    'model': critic['model'],
                    'status': 'success',
                    'output': output_text,
                }
                if usage:
                    result['usage'] = usage
                return result
            else:
                if stderr_text:
                    error_msg = stderr_text
                else:
                    error_msg = output_text[:500] or f"exit code {proc.returncode}"
                print(f"[FAILED] {name}: {error_msg}", file=sys.stderr)
                result = {
                    'name': name,
                    'model': critic['model'],
                    'status': 'error',
                    'output': output_text,
                    'error': error_msg,
                }
                if usage:
                    result['usage'] = usage
                return result
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            print(f"[TIMEOUT] {name}: exceeded {timeout}s", file=sys.stderr)
            return {
                'name': name,
                'model': critic['model'],
                'status': 'error',
                'output': '',
                'error': f'timeout after {timeout}s',
            }


async def run_all_critics(
    critics_data: dict,
    change_dir: Path,
    project_dir: Path | None,
    max_concurrent: int,
    timeout: int,
    budget: float | None,
    dry_run: bool,
    on_complete: callable = None,
    config_type: str = 'critics',
) -> dict:
    """Orchestrate parallel critic execution."""
    output_template = critics_data.get('output_template', '')
    critics = critics_data.get('critics', [])

    # Resolve skillbook paths
    schema_slug = critics_data.get('schema') or 'chaos-theory'
    kind = 'gap-detectors' if 'gap-detector' in config_type else 'critics'
    ace_dir = Path(__file__).parent.parent / '.ace' / kind / schema_slug

    if not critics:
        return {
            'critics_run': 0, 'critics_succeeded': 0,
            'critics_failed': 0, 'results': [],
        }

    team_ctx = _load_skillbook(ACE_DIR / 'team' / 'critique.json')

    if dry_run:
        for critic in critics:
            slug = critic['name'].lower().replace(' ', '-')
            sb_path = ace_dir / f'{slug}.json'
            skillbook_context = _load_skillbook(sb_path)
            prompt = build_prompt(critic, change_dir, project_dir,
                                  skillbook_context, team_context=team_ctx)
            cmd = build_command(critic, change_dir, project_dir,
                                output_template, budget)
            print(f"\n{'=' * 60}", file=sys.stderr)
            print(f"CRITIC: {critic['name']} ({critic['model']})",
                  file=sys.stderr)
            print(f"TOOLS: {'Read,Glob,Grep' if is_accuracy_critic(critic['name']) else 'Read'}",
                  file=sys.stderr)
            print(f"CMD: {cmd[:6]}...", file=sys.stderr)
            print(f"PROMPT:\n{prompt}", file=sys.stderr)
        return {
            'critics_run': 0, 'critics_succeeded': 0,
            'critics_failed': 0, 'results': [], 'dry_run': True,
        }

    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = []
    for critic in critics:
        slug = critic['name'].lower().replace(' ', '-')
        sb_path = ace_dir / f'{slug}.json'
        skillbook_context = _load_skillbook(sb_path)
        prompt = build_prompt(critic, change_dir, project_dir,
                              skillbook_context, team_context=team_ctx)
        cmd = build_command(critic, change_dir, project_dir,
                            output_template, budget)
        tasks.append(run_one_critic(critic, cmd, prompt, timeout, semaphore))

    results = await gather_with_callback(tasks, on_complete)

    succeeded = sum(1 for r in results if r['status'] == 'success')
    failed = len(results) - succeeded

    return {
        'critics_run': len(results),
        'critics_succeeded': succeeded,
        'critics_failed': failed,
        'results': list(results),
    }


ACE_DIR = Path(__file__).resolve().parent.parent / '.ace'


def _show_prompts(
    critics_data: dict, change_dir: Path, project_dir: Path | None,
    config_type: str = 'critics', critic_filter: str | None = None,
):
    """Print assembled prompts to stdout for inspection."""
    critics = critics_data.get('critics', [])
    output_template = critics_data.get('output_template', '')
    schema = critics_data.get('schema') or 'chaos-theory'
    kind = 'gap-detectors' if 'gap-detector' in config_type else 'critics'
    ace_dir = ACE_DIR / kind / schema

    team_ctx = _load_skillbook(ACE_DIR / 'team' / 'critique.json')

    if critic_filter:
        critics = [c for c in critics
                   if c['name'].lower() == critic_filter.lower()]
        if not critics:
            available = ', '.join(c['name'] for c in critics_data.get('critics', []))
            print(f"No critic matching '{critic_filter}'. "
                  f"Available: {available}", file=sys.stderr)
            sys.exit(1)

    for critic in critics:
        slug = critic['name'].lower().replace(' ', '-')
        sb_path = ace_dir / f'{slug}.json'
        skillbook_context = _load_skillbook(sb_path)
        prompt = build_prompt(critic, change_dir, project_dir,
                              skillbook_context, team_context=team_ctx)
        print(f"{'=' * 70}")
        print(f"CRITIC: {critic['name']} (model: {critic['model']})")
        print(f"{'=' * 70}")
        print(prompt)
        print()

    if output_template:
        print(f"{'=' * 70}")
        print("SYSTEM PROMPT (appended to all critics)")
        print(f"{'=' * 70}")
        print(output_template)


def main(argv: list[str] | None = None):
    args = parse_args(argv)
    if args.show_team_guidance:
        guidance = _load_skillbook(ACE_DIR / 'team' / 'critique.json')
        if guidance:
            print(guidance)
        else:
            print("No team guidance found.", file=sys.stderr)
        sys.exit(0)

    if args.change_dir is None:
        print("ERROR: change_dir is required", file=sys.stderr)
        sys.exit(1)

    change_dir = args.change_dir.resolve()

    if not change_dir.exists():
        print(f"ERROR: Change directory not found: {change_dir}",
              file=sys.stderr)
        sys.exit(1)

    if not args.dry_run and not args.show_prompt and not shutil.which('claude'):
        print("ERROR: claude CLI not found in PATH", file=sys.stderr)
        sys.exit(1)

    # Extract sections from spec.yaml if present (chaos-theory-lite schema)
    if (change_dir / 'spec.yaml').exists():
        from split_spec import split_spec
        extracted = split_spec(change_dir)
        if extracted:
            print(f"Extracted {len(extracted)} sections from spec.yaml",
                  file=sys.stderr)

    critics_data = select_critics(change_dir, args.config_type)
    project_dir = resolve_project_dir(change_dir)

    if args.show_prompt:
        _show_prompts(critics_data, change_dir, project_dir,
                      args.config_type, args.critic)
        sys.exit(0)

    if args.critic and args.dry_run:
        all_critics = critics_data.get('critics', [])
        filtered = [c for c in all_critics
                    if c['name'].lower() == args.critic.lower()]
        if not filtered:
            available = ', '.join(c['name'] for c in all_critics)
            print(f"No critic matching '{args.critic}'. "
                  f"Available: {available}", file=sys.stderr)
            sys.exit(1)
        critics_data['critics'] = filtered

    result = asyncio.run(run_all_critics(
        critics_data, change_dir, project_dir,
        args.max_concurrent, args.timeout, args.budget, args.dry_run,
        config_type=args.config_type,
    ))

    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
