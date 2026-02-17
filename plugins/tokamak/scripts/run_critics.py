#!/usr/bin/env python3
"""
Parallel critic orchestrator for OpenSpec workflow.

Launches claude -p processes in parallel to run critics deterministically.
Replaces unreliable "launch N Task calls in a single message" approach.

Usage:
    python run_critics.py <change_dir> [--max-concurrent N] [--timeout S] [--dry-run]
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


ACCURACY_CRITICS = frozenset({
    "Capability Accuracy",
    "Requirement Accuracy",
    "Architecture Accuracy",
    "Decision Plausibility",
    "Infrastructure Accuracy",
})


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Run OpenSpec critics in parallel via claude -p'
    )
    parser.add_argument('change_dir', type=Path,
                        help='Path to OpenSpec change directory')
    parser.add_argument('--max-concurrent', type=int, default=5,
                        help='Maximum parallel claude -p processes (default: 5)')
    parser.add_argument('--timeout', type=int, default=300,
                        help='Timeout per critic in seconds (default: 300)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print prompts and commands without launching processes')
    parser.add_argument('--budget', type=float, default=None,
                        help='Max budget per critic in USD')
    return parser.parse_args(argv)


def select_critics(change_dir: Path) -> dict:
    """Call select_critics.py and parse its JSON output."""
    script = Path(__file__).parent / 'select_critics.py'
    result = subprocess.run(
        [sys.executable, str(script), str(change_dir)],
        capture_output=True, text=True,
    )
    if result.stderr:
        print(result.stderr, end='', file=sys.stderr)
    if result.returncode != 0:
        print(f"ERROR: select_critics.py exited with code {result.returncode}",
              file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def resolve_project_dir(change_dir: Path) -> Path | None:
    """Resolve project directory from .openspec.yaml project field."""
    openspec_path = change_dir / '.openspec.yaml'
    if not openspec_path.exists():
        return None
    with open(openspec_path) as f:
        for line in f:
            m = re.match(r'^project:\s*(.+)', line)
            if m:
                openspec_root = change_dir.parent.parent  # openspec/changes/<name>/ → openspec/
                project_dir = (openspec_root / m.group(1).strip()).resolve()
                if project_dir.exists():
                    return project_dir
                return None
    return None


def is_accuracy_critic(name: str) -> bool:
    return name in ACCURACY_CRITICS


def build_prompt(critic: dict, change_dir: Path,
                 project_dir: Path | None) -> str:
    """Construct the evaluation prompt for a single critic."""
    parts = []

    parts.append("## Evaluation Criteria\n")
    parts.append(critic['evaluate'])
    parts.append("")

    # Files to evaluate (relative to change_dir)
    parts.append("## Files to evaluate\n")
    parts.append(f"Read these files from `{change_dir}/`:")
    for f in critic['files']:
        parts.append(f"- `{change_dir}/{f}`")
    parts.append("")

    # Schema template instructions
    templates = critic.get('templates', {})
    if templates:
        parts.append("## Schema Template Instructions (read-only context)\n")
        parts.append(
            "The following are authoring instructions from the schema templates "
            "that guided artifact creation. Use these to understand intentional "
            "structural choices in the evaluated files. Do NOT flag behaviors "
            "that comply with template guidance.\n"
        )
        for filename, content in templates.items():
            parts.append(f"### Template: `{filename}`\n")
            parts.append(content)
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

            if proc.returncode == 0:
                print(f"[SUCCESS] {name}", file=sys.stderr)
                return {
                    'name': name,
                    'model': critic['model'],
                    'status': 'success',
                    'output': stdout.decode().strip(),
                }
            else:
                error_msg = stderr.decode().strip() or f"exit code {proc.returncode}"
                print(f"[FAILED] {name}: {error_msg}", file=sys.stderr)
                return {
                    'name': name,
                    'model': critic['model'],
                    'status': 'error',
                    'output': stdout.decode().strip(),
                    'error': error_msg,
                }
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
) -> dict:
    """Orchestrate parallel critic execution."""
    output_template = critics_data.get('output_template', '')
    critics = critics_data.get('critics', [])

    if not critics:
        return {
            'critics_run': 0, 'critics_succeeded': 0,
            'critics_failed': 0, 'results': [],
        }

    if dry_run:
        for critic in critics:
            prompt = build_prompt(critic, change_dir, project_dir)
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
        prompt = build_prompt(critic, change_dir, project_dir)
        cmd = build_command(critic, change_dir, project_dir,
                            output_template, budget)
        tasks.append(run_one_critic(critic, cmd, prompt, timeout, semaphore))

    results = await asyncio.gather(*tasks)

    succeeded = sum(1 for r in results if r['status'] == 'success')
    failed = len(results) - succeeded

    return {
        'critics_run': len(results),
        'critics_succeeded': succeeded,
        'critics_failed': failed,
        'results': list(results),
    }


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

    critics_data = select_critics(change_dir)
    project_dir = resolve_project_dir(change_dir)

    result = asyncio.run(run_all_critics(
        critics_data, change_dir, project_dir,
        args.max_concurrent, args.timeout, args.budget, args.dry_run,
    ))

    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
