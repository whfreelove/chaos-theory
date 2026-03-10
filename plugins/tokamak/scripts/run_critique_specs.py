#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "questionary>=2.0",
#     "rich>=13.0",
#     "ruamel.yaml>=0.18",
# ]
# ///
"""
Standalone CLI for the critique-specs workflow.

Replaces SKILL.md agent orchestration with a Python process that:
- Uses `claude -p` subprocesses for AI work
- Uses `rich` for terminal display
- Uses `questionary` for interactive user decisions
- Calls existing library functions from run_critics/record_findings/spec_utils

Sections: Critique → Validate → Document → Report

Usage:
    python run_critique_specs.py openspec/changes/my-change
    python run_critique_specs.py openspec/changes/my-change --from val
    python run_critique_specs.py openspec/changes/my-change --dry-run
    python run_critique_specs.py openspec/changes/my-change --max-concurrent 4 --budget 0.50
"""

import argparse
import asyncio
import json
import shutil
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TaskID, TextColumn, TimeElapsedColumn
from rich.table import Table

from resolve_artifacts import resolve_artifacts
from spec_utils import (
    build_command,
    next_gap_id,
    parse_gaps,
    resolve_project_dir,
    resolve_skill_content,
    run_one_subprocess,
    try_parse_json,
)

console = Console()


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SECTION_ORDER = ['critique', 'validate', 'document', 'report']

SECTION_LABELS = {
    'critique': 'Critique',
    'validate': 'Validate',
    'document': 'Document',
    'report': 'Report',
}

SELECT_CRITICS_SCRIPT = Path(__file__).parent / 'select_critics.py'
TEMPLATE_DIR = Path(__file__).parent.parent / 'skills' / 'critique-specs' / 'templates'

VALIDATE_SYSTEM_PROMPT = (
    "You are a specification validator. Your job is to classify critic findings "
    "as COVERED, PARTIAL, or UNCOVERED relative to existing gaps, other findings, "
    "and the spec artifacts themselves.\n\n"
    "Output ONLY a JSON array to stdout.\n\n"
    "Format: [{\"finding\": \"<original finding text>\", "
    "\"status\": \"COVERED|PARTIAL|UNCOVERED\", "
    "\"matched_gaps\": [\"GAP-XX\"], "
    "\"match_source\": \"gap|finding|spec\", "
    "\"match_reason\": \"Quoted text from both finding and matched item\"}]"
)

DOCUMENT_SYSTEM_PROMPT = (
    "You are a specification gap documenter. Your job is to write new gap entries "
    "into gaps.md following the established format and gap writing guidance.\n\n"
    "Use the Edit tool to modify gaps.md — append new gaps at the end of the file.\n"
    "Do NOT modify resolved.md or any other files.\n\n"
    "Output ONLY a JSON array to stdout summarizing what you did.\n\n"
    "Format: [{\"id\": \"GAP-XX\", \"change\": \"new|update\", \"description\": \"...\"}]"
)


# ---------------------------------------------------------------------------
# Spinner handle for progress tracking
# ---------------------------------------------------------------------------

@dataclass
class SpinnerHandle:
    """Mutable handle yielded by WorkflowTracker.spinner() for live updates."""
    _progress: Progress
    _task_id: TaskID
    _base_desc: str
    _timeout: int | None
    _completed: int = 0
    _total: int | None = None

    def advance(self):
        """Mark one subprocess as complete and refresh the spinner text."""
        self._completed += 1
        self._progress.update(self._task_id, description=self._format())

    def _format(self) -> str:
        parts = [self._base_desc]
        if self._total is not None:
            parts.append(f"{self._completed}/{self._total} done")
        return " · ".join(parts)


# ---------------------------------------------------------------------------
# Critique log — accumulates metadata across sections
# ---------------------------------------------------------------------------

@dataclass
class CritiqueLog:
    """Tracks critique workflow state across all sections for commit message."""
    critics_run: int = 0
    critics_succeeded: int = 0
    critics_failed: int = 0
    config_type: str = 'critics'
    findings_text: str = ''
    findings_total: int = 0
    findings_covered: int = 0
    findings_partial: int = 0
    findings_uncovered: int = 0
    gaps_recorded: list[tuple[str, str]] = field(default_factory=list)
    gaps_updated: list[tuple[str, str]] = field(default_factory=list)
    validation_results: list[dict] = field(default_factory=list)
    selection_report: list[dict] = field(default_factory=list)
    commit: str = ''


# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------

def _check_clean_change_dir(change_dir: Path) -> None:
    """Block if the change directory has uncommitted git changes."""
    resolved = change_dir.resolve()
    try:
        repo_root = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True, text=True, check=True,
            cwd=str(resolved),
        ).stdout.strip()
        rel_path = str(resolved.relative_to(repo_root))
    except (subprocess.CalledProcessError, ValueError):
        return  # Not in a git repo — skip check

    result = subprocess.run(
        ['git', 'status', '--porcelain', '--', rel_path],
        capture_output=True, text=True,
        cwd=repo_root,
    )
    dirty_lines = result.stdout.strip()
    if dirty_lines:
        console.print("[red]ERROR: Change directory has uncommitted changes:[/red]")
        for line in dirty_lines.splitlines():
            console.print(f"  {line}")
        console.print(
            "\n[yellow]Commit or stash changes before running critique.[/yellow]"
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Fail-fast error types
# ---------------------------------------------------------------------------

@dataclass
class SubprocessFailure:
    """Record of a single failed subprocess within a workflow section."""
    name: str
    error: str
    phase: str = ''


class SectionFailedError(Exception):
    """Raised when one or more subprocesses fail within a workflow section."""
    def __init__(self, section: str, failures: list[SubprocessFailure]):
        self.section = section
        self.failures = failures
        names = ', '.join(f.name for f in failures[:5])
        if len(failures) > 5:
            names += f' (+{len(failures) - 5} more)'
        super().__init__(f"Section {section}: {len(failures)} subprocess(es) failed [{names}]")


# ---------------------------------------------------------------------------
# Workflow progress tracker
# ---------------------------------------------------------------------------

@dataclass
class WorkflowTracker:
    """Tracks workflow progress across critique-specs sections."""
    start_section: str = 'critique'
    completed: set[str] = field(default_factory=set)
    current: str | None = None
    current_step: int = 0
    current_total: int = 0

    def enter_section(self, section: str, total_steps: int) -> None:
        """Mark a section as active and display the progress header."""
        if self.current:
            self.completed.add(self.current)
        self.current = section
        self.current_step = 0
        self.current_total = total_steps
        self._render_header()

    def step(self, description: str) -> None:
        """Advance the step counter and display step info."""
        self.current_step += 1
        console.print(
            f"  [dim]Step {self.current_step}/{self.current_total}[/dim] · {description}"
        )

    def complete_section(self) -> None:
        """Mark the current section as completed."""
        if self.current:
            self.completed.add(self.current)

    @contextmanager
    def spinner(self, description: str, timeout: int | None = None, total: int | None = None):
        """Context manager that shows a spinner with elapsed time."""
        parts = [description]
        if timeout is not None:
            mins, secs = divmod(timeout, 60)
            parts.append(f"(timeout: {mins}:{secs:02d}/proc)")
        base_desc = " ".join(parts)

        initial_desc = base_desc
        if total is not None:
            initial_desc = f"{base_desc} · 0/{total} done"

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            task_id = progress.add_task(initial_desc, total=None)
            handle = SpinnerHandle(
                _progress=progress,
                _task_id=task_id,
                _base_desc=base_desc,
                _timeout=timeout,
                _completed=0,
                _total=total,
            )
            yield handle

    def _render_header(self) -> None:
        """Render the workflow progress bar and section header."""
        start_idx = SECTION_ORDER.index(self.start_section)
        parts = []
        for s in SECTION_ORDER:
            label = SECTION_LABELS[s]
            idx = SECTION_ORDER.index(s)
            if idx < start_idx:
                parts.append(f"[dim]– {label}[/dim]")
            elif s in self.completed:
                parts.append(f"[green]✓ {label}[/green]")
            elif s == self.current:
                parts.append(f"[bold cyan]● {label}[/bold cyan]")
            else:
                parts.append(f"[dim]○ {label}[/dim]")
        console.print()
        console.rule("  ".join(parts))


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------

def _resolve_from_section(value: str) -> str:
    """Resolve a --from prefix (>=3 chars) to a full section name."""
    value = value.lower()
    # Exact match first
    if value in SECTION_ORDER:
        return value
    if len(value) < 3:
        raise argparse.ArgumentTypeError(
            f"Section prefix must be at least 3 characters, got '{value}'"
        )
    matches = [s for s in SECTION_ORDER if s.startswith(value)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise argparse.ArgumentTypeError(
            f"Ambiguous section prefix '{value}': matches {', '.join(matches)}"
        )
    raise argparse.ArgumentTypeError(
        f"Unknown section '{value}'. Valid: {', '.join(SECTION_ORDER)} (or 3+ char prefix)"
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Standalone critique-specs workflow (Critique → Validate → Document → Report)'
    )
    parser.add_argument('change_dir', type=Path,
                        help='Path to OpenSpec change directory')
    parser.add_argument('--from', dest='from_section', default='critique',
                        type=_resolve_from_section,
                        help='Resume from section (default: critique). '
                             'Accepts 3+ char prefix: cri, val, doc, rep')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print prompts/commands without executing claude -p')
    parser.add_argument('--max-concurrent', type=int, default=6,
                        help='Maximum parallel claude -p processes (default: 6)')
    parser.add_argument('--timeout', type=int, default=600,
                        help='Timeout per subprocess in seconds (default: 600)')
    parser.add_argument('--budget', type=float, default=None,
                        help='Max budget per subprocess in USD')
    parser.add_argument('--config-type', default=None,
                        help='Override config type prefix (default: critics)')
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _resolve_config_type(change_dir: Path, override: str | None) -> str:
    """Resolve critic config type prefix (e.g. 'critics', 'gap-detectors')."""
    if override:
        return override
    return 'critics'


def _ensure_gap_files(change_dir: Path) -> None:
    """Ensure gaps.md and resolved.md exist, copying from templates if missing."""
    for filename in ('gaps.md', 'resolved.md'):
        target = change_dir / filename
        if not target.exists():
            template = TEMPLATE_DIR / filename
            if template.exists():
                shutil.copy2(template, target)
                console.print(f"  Created {filename} from template")
            else:
                target.write_text(f"# {filename.replace('.md', '').title()}\n\n")
                console.print(f"  Created empty {filename}")


def _load_cached_state(change_dir: Path, required_section: str) -> dict:
    """Load .critique-state.json and verify it meets section requirements."""
    cache_path = change_dir / '.critique-state.json'
    if not cache_path.exists():
        console.print(f"[red]ERROR: No cached state found at {cache_path}[/red]")
        console.print(f"[yellow]Run the workflow from an earlier section first:[/yellow]")
        req_idx = SECTION_ORDER.index(required_section)
        if req_idx > 0:
            prev = SECTION_ORDER[req_idx - 1]
            console.print(f"  [cyan]python run_critique_specs.py {change_dir} --from {prev}[/cyan]")
        else:
            console.print(f"  [cyan]python run_critique_specs.py {change_dir}[/cyan]")
        sys.exit(1)

    with open(cache_path) as f:
        state = json.load(f)

    last_completed = state.get('last_completed', '')
    if last_completed not in SECTION_ORDER:
        console.print(f"[red]ERROR: Invalid cached state (last_completed: {last_completed})[/red]")
        sys.exit(1)

    last_idx = SECTION_ORDER.index(last_completed)
    required_idx = SECTION_ORDER.index(required_section)
    if last_idx < required_idx:
        console.print(
            f"[red]ERROR: Cached state is from '{last_completed}', "
            f"but '{required_section}' requires at least '{SECTION_ORDER[required_idx]}'[/red]"
        )
        console.print(f"[yellow]Re-run from the required section:[/yellow]")
        console.print(
            f"  [cyan]python run_critique_specs.py {change_dir} "
            f"--from {SECTION_ORDER[required_idx]}[/cyan]"
        )
        sys.exit(1)

    return state


def _save_cached_state(change_dir: Path, log: CritiqueLog, section: str) -> None:
    """Write .critique-state.json after a section completes."""
    cache_path = change_dir / '.critique-state.json'
    state = {
        'last_completed': section,
        'config_type': log.config_type,
        'critics_run': log.critics_run,
        'critics_succeeded': log.critics_succeeded,
        'critics_failed': log.critics_failed,
        'findings_text': log.findings_text,
        'validation_results': [v for v in log.validation_results],
        'selection_report': log.selection_report,
        'commit': log.commit,
    }
    with open(cache_path, 'w') as f:
        json.dump(state, f, indent=2)
        f.write('\n')


def _cleanup_cached_state(change_dir: Path) -> None:
    """Remove .critique-state.json after successful workflow completion."""
    cache_path = change_dir / '.critique-state.json'
    if cache_path.exists():
        cache_path.unlink()


async def _run_single_subprocess(
    name: str, cmd: list[str], prompt: str, timeout: int, max_concurrent: int
) -> dict:
    """Run a single claude -p subprocess with semaphore control."""
    semaphore = asyncio.Semaphore(max_concurrent)
    return await run_one_subprocess(name, cmd, prompt, timeout, semaphore)


def _render_failure_panel(error: SectionFailedError, change_dir: Path) -> None:
    """Render a rich table of failed subprocesses with retry guidance."""
    table = Table(title=f"Section {SECTION_LABELS.get(error.section, error.section)} Failures")
    table.add_column("Subprocess", style="bold red")
    table.add_column("Phase", style="dim")
    table.add_column("Error")

    for f in error.failures:
        table.add_row(f.name, f.phase or '—', f.error)

    console.print()
    console.print(table)
    console.print(Panel(
        f"[bold red]{len(error.failures)} subprocess(es) failed in "
        f"{SECTION_LABELS.get(error.section, error.section)}.[/bold red]\n\n"
        f"Retry from this section:\n"
        f"  [cyan]python run_critique_specs.py {change_dir} --from {error.section}[/cyan]",
        title="Workflow Stopped",
        border_style="red",
    ))


def _truncate(text: str, max_len: int) -> str:
    """Truncate text to max_len characters."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + '...'


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------


def _resolve_spec_files(change_dir: Path) -> list[str]:
    """Resolve spec artifact file paths for validation cross-referencing.

    Uses resolve_artifacts() for schema-agnostic resolution, then adds
    .sections/*.yaml split files for chaos-theory-lite schema.
    """
    try:
        data = resolve_artifacts(change_dir)
    except SystemExit:
        return []

    files = list(data['files'])

    # For lite schema, also include the split section files
    # (split_spec already ran in step 2 of the workflow)
    sections_dir = change_dir / '.sections'
    if sections_dir.is_dir():
        for p in sorted(sections_dir.glob('*.yaml')):
            rel = str(p.relative_to(change_dir))
            if rel not in files:
                files.append(rel)

    return files


def _build_validation_prompt(
    findings_text: str,
    change_dir: Path,
    project_dir: Path | None,
) -> str:
    """Build the user prompt for the Validate section."""
    parts = [
        "## Assignment\n",
        "Validate whether each critic finding is semantically distinct from:\n"
        "1. Existing gaps in gaps.md and resolved.md\n"
        "2. Other critic findings in this batch\n"
        "3. Content already present in the spec artifacts\n",
        "For each finding, classify as:\n"
        "- COVERED: fully duplicated by an existing gap, another finding, "
        "or already addressed in the spec artifacts\n"
        "- PARTIAL: overlaps with an existing gap, another finding, "
        "or spec content (same topic, different angle or scope)\n"
        "- UNCOVERED: genuinely new concern not addressed anywhere\n",
        "For each mapping, quote specific text from BOTH the finding AND the matched item.\n"
        "If you cannot quote matching text, mark UNCOVERED.\n",
        "For COVERED findings matched to another finding: indicate which finding is more "
        "comprehensive (that one survives, the other is COVERED).\n",
        "For COVERED/PARTIAL findings matched to spec content: set match_source to \"spec\" "
        "and quote the spec text that addresses the concern.\n",
        "Set match_source to \"gap\" when matched to gaps.md/resolved.md, "
        "\"finding\" when matched to another finding, \"spec\" when matched to spec artifacts.\n",
    ]

    if project_dir:
        parts.append(
            "For project consistency findings, also check project docs (Current Limitations, "
            "Known Risks, Out of Scope). If acknowledged there, mark COVERED.\n"
        )

    parts.extend([
        "## Critic Findings\n",
        findings_text,
        "\n## Existing Gaps\n",
        f"Read these files to check for already-documented gaps:\n"
        f"- `{change_dir}/gaps.md`\n"
        f"- `{change_dir}/resolved.md`\n",
    ])

    # Spec artifacts — schema-agnostic via resolve_artifacts
    spec_files = _resolve_spec_files(change_dir)
    if spec_files:
        parts.append("\n## Spec Artifacts\n")
        parts.append(
            "Read these files to check if findings are already addressed in the specs:\n"
        )
        for f in spec_files:
            parts.append(f"- `{change_dir}/{f}`\n")

    if project_dir:
        parts.append(
            f"\n## Project Reference Files\n"
            f"Read reference files from `{project_dir}/` for context on "
            f"acknowledged limitations.\n"
        )

    return '\n'.join(parts)


def _build_documentation_prompt(
    findings_text: str,
    validation_results: list[dict],
    next_id: str,
    change_dir: Path,
    project_dir: Path | None,
) -> str:
    """Build the user prompt for the Document section."""
    # Filter to UNCOVERED and PARTIAL only
    actionable = [v for v in validation_results
                  if v.get('status') in ('UNCOVERED', 'PARTIAL')]

    parts = [
        "## Assignment\n",
        "Write new gap entries into gaps.md for the following validated findings. "
        "Each finding has been pre-filtered — only UNCOVERED and PARTIAL findings are included.\n",
        f"Start gap numbering from {next_id}.\n",
        "## Validated Findings\n",
        "```json",
        json.dumps(actionable, indent=2),
        "```\n",
        "## Original Critic Findings (for full context)\n",
        findings_text,
        "\n## Gap Writing Guidance\n",
    ]

    # Include managing-spec-gaps skill content
    skill_content = resolve_skill_content('tokamak:managing-spec-gaps')
    if skill_content:
        parts.append(skill_content)
        parts.append("")

    parts.extend([
        "\n## Merge Instructions\n",
        "- Re-evaluate severity for each finding before writing\n"
        "- Write gaps in evergreen language (no temporal references)\n"
        "- Format source as kebab-case with -critic suffix (e.g., functional-critic)\n"
        "- If two findings cover the same concern at different scopes, "
        "write ONE gap at the broader scope and note the narrower concern in the description\n",
        f"\n## Files\n",
        f"- Edit: `{change_dir}/gaps.md`\n"
        f"- Read (context only): `{change_dir}/resolved.md`\n",
    ])

    if project_dir:
        parts.append(
            f"- Read (context only): project docs at `{project_dir}/`\n"
        )

    return '\n'.join(parts)


# ---------------------------------------------------------------------------
# Section: Critique
# ---------------------------------------------------------------------------

def run_critique(
    change_dir: Path,
    tracker: WorkflowTracker,
    log: CritiqueLog,
    max_concurrent: int,
    timeout: int,
    budget: float | None,
    dry_run: bool,
) -> CritiqueLog:
    """Critique section: run parallel critics and collect findings."""
    tracker.enter_section('critique', 4)

    sys.path.insert(0, str(Path(__file__).parent))
    from run_critics import run_all_critics, select_critics

    # Step 1: Ensure gap files exist
    tracker.step("Ensuring gaps.md and resolved.md exist")
    _ensure_gap_files(change_dir)

    # Step 2: Split spec.yaml if present (chaos-theory-lite schema)
    tracker.step("Preparing artifacts")
    if (change_dir / 'spec.yaml').exists():
        from split_spec import split_spec
        extracted = split_spec(change_dir)
        if extracted:
            console.print(f"  Extracted {len(extracted)} sections from spec.yaml")

    # Step 3: Select and run critics
    tracker.step("Running parallel critics")
    config_type = log.config_type
    critics_data = select_critics(change_dir, config_type)
    log.selection_report = critics_data.get('selection_report', [])

    # Resolve git commit hash
    try:
        log.commit = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True, text=True, check=True,
            cwd=str(change_dir),
        ).stdout.strip()
    except subprocess.CalledProcessError:
        log.commit = ''

    project_dir = resolve_project_dir(change_dir)

    critic_count = len(critics_data.get('critics', []))
    if critic_count == 0:
        console.print("\n[yellow]No critics selected (all files unchanged or missing).[/yellow]")
        # Guidance: recommend resolve-gaps if active gaps exist, else ratify-specs
        gaps_path = change_dir / 'gaps.md'
        if gaps_path.exists():
            gaps = parse_gaps(gaps_path.read_text())
            if gaps:
                console.print(
                    "[dim]Active gaps exist — consider running resolve-gaps:[/dim]\n"
                    f"  [cyan]python run_resolve_gaps.py {change_dir}[/cyan]"
                )
            else:
                console.print(
                    "[dim]No active gaps — specs may be ready for ratification.[/dim]"
                )
        log.critics_run = 0
        return log

    with tracker.spinner("Running critics...", timeout=timeout, total=critic_count) as handle:
        result = asyncio.run(run_all_critics(
            critics_data, change_dir, project_dir,
            max_concurrent, timeout, budget, dry_run,
            on_complete=handle.advance,
            config_type=config_type,
        ))

    log.critics_run = result.get('critics_run', 0)
    log.critics_succeeded = result.get('critics_succeeded', 0)
    log.critics_failed = result.get('critics_failed', 0)

    # Handle failures
    results = result.get('results', [])
    failures = [r for r in results if r.get('status') != 'success']

    if failures and not dry_run:
        # Report failures in a table
        fail_table = Table(title="Critic Failures")
        fail_table.add_column("Critic", style="bold red")
        fail_table.add_column("Error")
        for r in failures:
            fail_table.add_row(r.get('name', 'unknown'), r.get('error', 'unknown'))
        console.print(fail_table)

        successes = [r for r in results if r.get('status') == 'success']
        if not successes:
            raise SectionFailedError('critique', [
                SubprocessFailure(name=r.get('name', 'unknown'),
                                  error=r.get('error', 'unknown'),
                                  phase='critic-run')
                for r in failures
            ])

        proceed = questionary.confirm(
            f"{len(failures)} critic(s) failed. Proceed with {len(successes)} successful result(s)?",
            default=True,
        ).ask()
        if not proceed:
            raise SectionFailedError('critique', [
                SubprocessFailure(name=r.get('name', 'unknown'),
                                  error=r.get('error', 'unknown'),
                                  phase='critic-run')
                for r in failures
            ])

    # Step 4: Concatenate findings
    tracker.step("Concatenating findings")
    findings_parts = []
    successes = [r for r in results if r.get('status') == 'success']
    for r in successes:
        output = r.get('output', '').strip()
        if output:
            findings_parts.append(f"## {r['name']}\n\n{output}")

    log.findings_text = '\n\n'.join(findings_parts)
    console.print(
        f"  Collected findings from {len(successes)} critic(s) "
        f"({len(log.findings_text)} chars)"
    )

    # Save per-critic results for offline ACE learning
    schema = critics_data.get('schema') or 'chaos-theory'
    results_path = change_dir / '.critique-results.json'
    MAX_CRITIQUE_RUNS = 10
    existing_runs = []
    if results_path.exists():
        try:
            with open(results_path) as f:
                existing_runs = json.load(f)
        except (json.JSONDecodeError, ValueError):
            existing_runs = []
    existing_runs.append({
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'config_type': config_type,
        'schema': schema,
        'commit': log.commit,
        'results': [
            {'name': r['name'], 'status': r['status'],
             'output': r.get('output', ''), 'model': r.get('model', '')}
            for r in results
        ],
    })
    existing_runs = existing_runs[-MAX_CRITIQUE_RUNS:]
    try:
        with open(results_path, 'w') as f:
            json.dump(existing_runs, f, indent=2)
    except OSError as e:
        print(f"WARNING: Could not save critique results: {e}", file=sys.stderr)

    # Save state
    _save_cached_state(change_dir, log, 'critique')

    return log


# ---------------------------------------------------------------------------
# Section: Validate
# ---------------------------------------------------------------------------

def run_validate(
    change_dir: Path,
    tracker: WorkflowTracker,
    log: CritiqueLog,
    max_concurrent: int,
    timeout: int,
    budget: float | None,
    dry_run: bool,
) -> CritiqueLog:
    """Validate section: filter findings against existing gaps and each other."""
    tracker.enter_section('validate', 3)

    from record_findings import parse_critic_name

    project_dir = resolve_project_dir(change_dir)

    # Step 1: Build prompts
    tracker.step("Building validation prompt")
    findings_text = log.findings_text
    if not findings_text:
        console.print("[yellow]No findings to validate.[/yellow]")
        log.validation_results = []
        _save_cached_state(change_dir, log, 'validate')
        return log

    system_prompt = VALIDATE_SYSTEM_PROMPT
    user_prompt = _build_validation_prompt(findings_text, change_dir, project_dir)

    cmd = build_command(
        change_dir, project_dir,
        system_prompt, 'sonnet', budget,
        tools='Read',
    )

    # Step 2: Run validation subprocess
    tracker.step("Running validation subprocess")
    if dry_run:
        console.print(Panel(
            f"[dim]DRY-RUN: Validation prompt ({len(user_prompt)} chars)[/dim]\n\n"
            f"{user_prompt[:500]}{'...' if len(user_prompt) > 500 else ''}",
            title="Validate (dry-run)",
        ))
        log.validation_results = []
        _save_cached_state(change_dir, log, 'validate')
        return log

    with tracker.spinner("Validating findings...", timeout=timeout) as _handle:
        result = asyncio.run(_run_single_subprocess(
            "finding-validator", cmd, user_prompt, timeout, max_concurrent
        ))

    if result['status'] != 'success':
        raise SectionFailedError('validate', [SubprocessFailure(
            name='finding-validator',
            error=result.get('error', 'unknown'),
            phase='validation',
        )])

    # Parse results
    validation_results = result.get('report', [])

    # Handle empty report with non-empty output
    if not validation_results and result.get('output', '').strip():
        console.print("[yellow]Validator returned output but no parseable JSON report.[/yellow]")
        choice = questionary.select(
            "How to proceed?",
            choices=[
                questionary.Choice("Treat all findings as UNCOVERED", value='uncovered'),
                questionary.Choice("Abort workflow", value='abort'),
            ],
        ).ask()
        if choice is None or choice == 'abort':
            console.print("[red]Aborted.[/red]")
            sys.exit(1)
        # Synthesize UNCOVERED entries — one per critic output block
        validation_results = []
        for block in findings_text.split('\n## '):
            block = block.strip()
            if not block:
                continue
            # Extract first line as finding identifier
            first_line = block.split('\n')[0].strip()
            if first_line.startswith('## '):
                first_line = first_line[3:]
            validation_results.append({
                'finding': first_line,
                'status': 'UNCOVERED',
                'matched_gaps': [],
                'match_source': '',
                'match_reason': 'Synthesized — validator parse failure',
            })

    log.validation_results = validation_results

    # Step 3: Record to findings.json
    tracker.step("Recording findings and displaying summary")

    # Record to findings.json
    findings_path = change_dir / 'findings.json'
    if findings_path.exists():
        with open(findings_path) as f:
            rounds = json.load(f)
        if not isinstance(rounds, list):
            rounds = []
    else:
        rounds = []

    round_num = len(rounds) + 1
    findings_entries = []
    for entry in validation_results:
        finding_text = entry.get('finding', '')
        findings_entries.append({
            'critic': parse_critic_name(finding_text),
            'finding': finding_text,
            'status': entry.get('status', 'UNCOVERED'),
            'matched_gaps': entry.get('matched_gaps', []),
            'match_source': entry.get('match_source', ''),
            'match_reason': entry.get('match_reason', ''),
        })

    round_entry = {
        'round': round_num,
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'findings': findings_entries,
    }
    if log.commit:
        round_entry['commit'] = log.commit
    if log.selection_report:
        round_entry['critics'] = log.selection_report
    rounds.append(round_entry)

    with open(findings_path, 'w') as f:
        json.dump(rounds, f, indent=2)
        f.write('\n')

    console.print(f"  Recorded round {round_num} with {len(findings_entries)} findings")

    # Compute summary counts
    covered = sum(1 for v in validation_results if v.get('status') == 'COVERED')
    partial = sum(1 for v in validation_results if v.get('status') == 'PARTIAL')
    uncovered = sum(1 for v in validation_results if v.get('status') == 'UNCOVERED')

    log.findings_total = len(validation_results)
    log.findings_covered = covered
    log.findings_partial = partial
    log.findings_uncovered = uncovered

    # Display summary table
    summary_table = Table(title="Validation Summary")
    summary_table.add_column("Status", style="bold")
    summary_table.add_column("Count", justify="right")
    summary_table.add_row("[dim]COVERED[/dim]", str(covered))
    summary_table.add_row("[yellow]PARTIAL[/yellow]", str(partial))
    summary_table.add_row("[green]UNCOVERED[/green]", str(uncovered))
    console.print(summary_table)

    # All covered → skip Document
    if uncovered == 0 and partial == 0:
        console.print("[dim]All findings are covered — no new gaps to document.[/dim]")

    # Save state
    _save_cached_state(change_dir, log, 'validate')

    return log


# ---------------------------------------------------------------------------
# Section: Document
# ---------------------------------------------------------------------------

def run_document(
    change_dir: Path,
    tracker: WorkflowTracker,
    log: CritiqueLog,
    max_concurrent: int,
    timeout: int,
    budget: float | None,
    dry_run: bool,
) -> CritiqueLog:
    """Document section: write pre-filtered findings into gaps.md."""
    tracker.enter_section('document', 3)

    project_dir = resolve_project_dir(change_dir)

    # Check if there's anything to document
    actionable = [v for v in log.validation_results
                  if v.get('status') in ('UNCOVERED', 'PARTIAL')]
    if not actionable:
        console.print("[dim]No UNCOVERED or PARTIAL findings — skipping Document section.[/dim]")
        tracker.step("Checking for actionable findings — none")
        tracker.step("Skipped")
        tracker.step("Skipped")
        return log

    # Step 1: Snapshot gaps.md and build prompt
    tracker.step("Preparing documentation prompt")
    gaps_path = change_dir / 'gaps.md'
    gaps_md_before = gaps_path.read_text() if gaps_path.exists() else ''

    next_id = next_gap_id(change_dir)
    user_prompt = _build_documentation_prompt(
        log.findings_text, log.validation_results,
        next_id, change_dir, project_dir,
    )
    system_prompt = DOCUMENT_SYSTEM_PROMPT

    cmd = build_command(
        change_dir, project_dir,
        system_prompt, 'sonnet', budget,
        tools='Read,Edit,Write',
    )

    # Step 2: Run documentation subprocess
    tracker.step("Running documentation subprocess")
    if dry_run:
        console.print(Panel(
            f"[dim]DRY-RUN: Documentation prompt ({len(user_prompt)} chars)[/dim]\n\n"
            f"{user_prompt[:500]}{'...' if len(user_prompt) > 500 else ''}",
            title="Document (dry-run)",
        ))
        return log

    with tracker.spinner("Documenting gaps...", timeout=timeout) as _handle:
        result = asyncio.run(_run_single_subprocess(
            "gap-documenter", cmd, user_prompt, timeout, max_concurrent
        ))

    if result['status'] != 'success':
        raise SectionFailedError('document', [SubprocessFailure(
            name='gap-documenter',
            error=result.get('error', 'unknown'),
            phase='documentation',
        )])

    # Step 3: Validate integrity and track changes
    tracker.step("Validating gaps.md integrity")

    # Parse the report for change tracking
    report = result.get('report', [])
    for entry in report:
        gap_id = entry.get('id', '')
        change_type = entry.get('change', 'new')
        desc = entry.get('description', '')
        if change_type == 'new':
            log.gaps_recorded.append((gap_id, _truncate(desc, 60)))
        elif change_type == 'update':
            log.gaps_updated.append((gap_id, _truncate(desc, 60)))

    # Validate gaps.md didn't get corrupted
    gaps_md_after = gaps_path.read_text() if gaps_path.exists() else ''
    try:
        gaps_after = parse_gaps(gaps_md_after)
        gaps_before = parse_gaps(gaps_md_before)
        if len(gaps_after) < len(gaps_before):
            console.print(
                f"[red]WARNING: gaps.md has fewer gaps after documentation "
                f"({len(gaps_after)} < {len(gaps_before)})[/red]"
            )
            restore = questionary.confirm(
                "Restore gaps.md to pre-documentation state?", default=True,
            ).ask()
            if restore:
                gaps_path.write_text(gaps_md_before)
                console.print("[yellow]Restored gaps.md[/yellow]")
                log.gaps_recorded.clear()
                log.gaps_updated.clear()
    except Exception as e:
        console.print(f"[red]WARNING: Could not parse gaps.md after documentation: {e}[/red]")
        restore = questionary.confirm(
            "Restore gaps.md to pre-documentation state?", default=True,
        ).ask()
        if restore:
            gaps_path.write_text(gaps_md_before)
            console.print("[yellow]Restored gaps.md[/yellow]")
            log.gaps_recorded.clear()
            log.gaps_updated.clear()

    console.print(
        f"  Recorded {len(log.gaps_recorded)} new gap(s), "
        f"updated {len(log.gaps_updated)} existing gap(s)"
    )

    return log


# ---------------------------------------------------------------------------
# Section: Report
# ---------------------------------------------------------------------------

def run_report(
    change_dir: Path,
    tracker: WorkflowTracker,
    log: CritiqueLog,
    dry_run: bool,
) -> None:
    """Report section: summary tables, hash update, git commit."""
    tracker.enter_section('report', 3)

    change_name = change_dir.name
    config_type = log.config_type

    # Step 1: Summary tables
    tracker.step("Building summary tables")

    # Critics summary
    critics_table = Table(title="Critics")
    critics_table.add_column("Metric", style="bold")
    critics_table.add_column("Count", justify="right")
    critics_table.add_row("Run", str(log.critics_run))
    critics_table.add_row("[green]Succeeded[/green]", str(log.critics_succeeded))
    if log.critics_failed:
        critics_table.add_row("[red]Failed[/red]", str(log.critics_failed))
    console.print(critics_table)

    # Validation summary
    if log.findings_total > 0:
        val_table = Table(title="Validation Results")
        val_table.add_column("Status", style="bold")
        val_table.add_column("Count", justify="right")
        val_table.add_row("[dim]Covered[/dim]", str(log.findings_covered))
        val_table.add_row("[yellow]Partial[/yellow]", str(log.findings_partial))
        val_table.add_row("[green]Uncovered[/green]", str(log.findings_uncovered))
        console.print(val_table)

    # Gap changes
    if log.gaps_recorded:
        gaps_table = Table(title="New Gaps")
        gaps_table.add_column("Gap ID", style="green")
        gaps_table.add_column("Description")
        for gap_id, desc in log.gaps_recorded:
            gaps_table.add_row(gap_id, desc)
        console.print(gaps_table)

    if log.gaps_updated:
        update_table = Table(title="Updated Gaps")
        update_table.add_column("Gap ID", style="yellow")
        update_table.add_column("Description")
        for gap_id, desc in log.gaps_updated:
            update_table.add_row(gap_id, desc)
        console.print(update_table)

    # Step 2: Update hashes
    tracker.step("Updating hashes and staging")

    if not dry_run:
        try:
            subprocess.run(
                [sys.executable, str(SELECT_CRITICS_SCRIPT),
                 str(change_dir), '--update-hashes', '--type', config_type],
                check=True, capture_output=True, text=True,
            )
            console.print("  Updated critic hashes")
        except subprocess.CalledProcessError as e:
            console.print(f"[yellow]WARNING: Hash update failed: {e.stderr.strip()}[/yellow]")

    # Git add + diff check
    change_rel = str(change_dir)
    has_changes = False

    if not dry_run:
        try:
            subprocess.run(
                ['git', 'add', change_rel],
                check=True, capture_output=True, text=True,
            )
            diff_result = subprocess.run(
                ['git', 'diff', '--cached', '--quiet'],
                capture_output=True, text=True,
            )
            has_changes = diff_result.returncode != 0
        except subprocess.CalledProcessError:
            has_changes = False

    if not has_changes and not log.gaps_recorded and not log.gaps_updated:
        console.print("[dim]No changes to commit.[/dim]")
        if not dry_run:
            _cleanup_cached_state(change_dir)
        return

    # Step 3: Build commit message and commit
    tracker.step("Committing results")

    gap_count = len(log.gaps_recorded) + len(log.gaps_updated)
    if gap_count > 0:
        subject = f"spec({change_name}): Record {gap_count} critique gap{'s' if gap_count != 1 else ''}"
    else:
        subject = f"spec({change_name}): Record critique round (0 findings)"

    body_lines = []
    for gap_id, desc in log.gaps_recorded:
        body_lines.append(f"- {gap_id}: new — {desc}")
    for gap_id, desc in log.gaps_updated:
        body_lines.append(f"- {gap_id}: updated — {desc}")

    if log.findings_covered:
        body_lines.append(f"- {log.findings_covered} finding(s) covered by existing gaps")
    if log.findings_partial:
        body_lines.append(f"- {log.findings_partial} finding(s) partially covered")

    body = '\n'.join(body_lines)

    console.print(Panel(
        f"[bold]{subject}[/bold]\n\n{body}" if body else f"[bold]{subject}[/bold]",
        title="Commit Message",
    ))

    if dry_run:
        console.print("[dim]DRY-RUN: Skipping commit.[/dim]")
        return

    if not has_changes:
        console.print("[dim]No staged changes to commit.[/dim]")
        _cleanup_cached_state(change_dir)
        return

    proceed = questionary.confirm("Stage and commit?", default=True).ask()
    if not proceed:
        console.print("[dim]Skipped commit.[/dim]")
        return

    try:
        commit_msg = f"{subject}\n\n{body}" if body else subject
        subprocess.run(
            ['git', 'commit', '-m', commit_msg],
            check=True, capture_output=True, text=True,
        )
        console.print("[green]Committed successfully.[/green]")
    except subprocess.CalledProcessError as e:
        raise SectionFailedError('report', [SubprocessFailure(
            name='git-commit',
            error=e.stderr.strip() or str(e),
            phase='commit',
        )]) from e

    _cleanup_cached_state(change_dir)


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None):
    args = parse_args(argv)
    change_dir = args.change_dir.resolve()

    if not change_dir.exists():
        console.print(f"[red]ERROR: Change directory not found: {change_dir}[/red]")
        sys.exit(1)

    if not args.dry_run and not shutil.which('claude'):
        console.print("[red]ERROR: claude CLI not found in PATH[/red]")
        sys.exit(1)

    if not args.dry_run:
        _check_clean_change_dir(change_dir)

    start_section = args.from_section
    start_idx = SECTION_ORDER.index(start_section)

    # Resolve config type
    config_type = _resolve_config_type(change_dir, args.config_type)

    # Initialize log (or restore from cache on resume)
    log = CritiqueLog(config_type=config_type)

    # Restore log fields from cache when resuming
    if start_section != 'critique':
        required_prev = SECTION_ORDER[start_idx - 1]
        state = _load_cached_state(change_dir, required_prev)
        log.config_type = state.get('config_type', config_type)
        log.critics_run = state.get('critics_run', 0)
        log.critics_succeeded = state.get('critics_succeeded', 0)
        log.critics_failed = state.get('critics_failed', 0)
        log.findings_text = state.get('findings_text', '')
        log.validation_results = state.get('validation_results', [])
        log.selection_report = state.get('selection_report', [])
        log.commit = state.get('commit', '')

    tracker = WorkflowTracker(start_section=start_section)

    console.print(Panel(
        f"Change: [bold]{change_dir.name}[/bold]\n"
        f"Config type: {config_type}\n"
        f"Starting from: {SECTION_LABELS.get(start_section, start_section)}\n"
        f"Dry run: {args.dry_run}\n"
        f"Max concurrent: {args.max_concurrent}\n"
        f"Budget: {args.budget or 'unlimited'}",
        title="Critique Specs Workflow",
    ))

    try:
        # Critique
        if start_idx <= SECTION_ORDER.index('critique'):
            log = run_critique(
                change_dir, tracker, log,
                args.max_concurrent, args.timeout, args.budget, args.dry_run,
            )
            tracker.complete_section()

            # Early exit if no critics ran
            if log.critics_run == 0:
                console.print("\n[bold]Workflow complete (no critics to run).[/bold]")
                return

        # Validate
        if start_idx <= SECTION_ORDER.index('validate'):
            log = run_validate(
                change_dir, tracker, log,
                args.max_concurrent, args.timeout, args.budget, args.dry_run,
            )
            tracker.complete_section()

        # Document (skip if all findings covered)
        if start_idx <= SECTION_ORDER.index('document'):
            actionable = [v for v in log.validation_results
                          if v.get('status') in ('UNCOVERED', 'PARTIAL')]
            if actionable or start_section == 'document':
                log = run_document(
                    change_dir, tracker, log,
                    args.max_concurrent, args.timeout, args.budget, args.dry_run,
                )
            else:
                tracker.enter_section('document', 1)
                tracker.step("Skipped — all findings covered")
            tracker.complete_section()

        # Report
        if start_idx <= SECTION_ORDER.index('report'):
            run_report(change_dir, tracker, log, args.dry_run)
            tracker.complete_section()

        console.print("\n[bold green]Workflow complete.[/bold green]")

    except SectionFailedError as e:
        _render_failure_panel(e, change_dir)
        sys.exit(1)


if __name__ == '__main__':
    main()
