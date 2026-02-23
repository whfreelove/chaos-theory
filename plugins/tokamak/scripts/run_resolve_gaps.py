#!/usr/bin/env python3
"""
Standalone CLI for the resolve-gaps workflow (Sections D→H).

Replaces SKILL.md agent orchestration with a Python process that:
- Uses `claude -p` subprocesses for AI work
- Uses `rich` for terminal display
- Uses `questionary` for interactive user decisions
- Calls existing library functions from run_solvers/run_resolvers/run_critics

Usage:
    python run_resolve_gaps.py openspec/changes/my-change
    python run_resolve_gaps.py openspec/changes/my-change --from E
    python run_resolve_gaps.py openspec/changes/my-change --dry-run
    python run_resolve_gaps.py openspec/changes/my-change --max-concurrent 4 --budget 0.50
"""

import argparse
import asyncio
import json
import re
import shutil
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

import questionary
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from spec_utils import (
    append_gap_entry,
    build_command,
    clear_gap_field,
    format_detector_finding_as_gap,
    move_gap_to_resolved,
    next_gap_id,
    parse_gaps,
    read_gap_entries,
    resolve_project_dir,
    resolve_skill_content,
    run_one_subprocess,
    try_parse_json,
    write_gap_field,
    write_gap_fields,
)

console = Console()

SECTION_ORDER = ['D', 'E', 'F', 'G', 'H']

SECTION_LABELS = {
    'D': 'Triage',
    'E': 'Solve',
    'F': 'Resolve',
    'G': 'Cleanup',
    'H': 'Report',
}


# ---------------------------------------------------------------------------
# Resolution log — accumulates metadata across sections D→H
# ---------------------------------------------------------------------------

@dataclass
class ResolutionLog:
    """Tracks resolution actions across all sections for commit message."""
    triaged: list[tuple[str, str]] = field(default_factory=list)
    decided: list[tuple[str, str]] = field(default_factory=list)
    resolved: list[tuple[str, str]] = field(default_factory=list)
    implicit_recorded: list[tuple[str, str]] = field(default_factory=list)
    implicit_resolved: list[tuple[str, str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Workflow progress tracker
# ---------------------------------------------------------------------------

@dataclass
class WorkflowTracker:
    """Tracks workflow progress across sections D→H."""
    start_section: str = 'D'
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
    def spinner(self, description: str):
        """Context manager that shows a spinner with elapsed time."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(description, total=None)
            yield

    def _render_header(self) -> None:
        """Render the workflow progress bar and section header."""
        start_idx = SECTION_ORDER.index(self.start_section)
        parts = []
        for s in SECTION_ORDER:
            label = SECTION_LABELS[s]
            idx = SECTION_ORDER.index(s)
            if idx < start_idx:
                parts.append(f"[dim]– {s}[/dim]")
            elif s in self.completed:
                parts.append(f"[green]✓ {s}:{label}[/green]")
            elif s == self.current:
                parts.append(f"[bold cyan]● {s}:{label}[/bold cyan]")
            else:
                parts.append(f"[dim]○ {s}:{label}[/dim]")
        console.print()
        console.rule("  ".join(parts))


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Standalone resolve-gaps workflow (Sections D→H)'
    )
    parser.add_argument('change_dir', type=Path,
                        help='Path to OpenSpec change directory')
    parser.add_argument('--from', dest='from_section', default='D',
                        choices=SECTION_ORDER,
                        help='Resume from a specific section (default: D)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print prompts/commands without executing claude -p')
    parser.add_argument('--max-concurrent', type=int, default=6,
                        help='Maximum parallel claude -p processes (default: 6)')
    parser.add_argument('--timeout', type=int, default=900,
                        help='Timeout per subprocess in seconds (default: 900)')
    parser.add_argument('--budget', type=float, default=None,
                        help='Max budget per subprocess in USD')
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Triage policy loading
# ---------------------------------------------------------------------------

def load_triage_policy(change_dir: Path) -> dict:
    """Load .triage-policy.json from the change directory."""
    policy_path = change_dir / '.triage-policy.json'
    if not policy_path.exists():
        console.print(
            f"[red]ERROR: No .triage-policy.json in {change_dir}.[/red]\n"
            "Initialize with: python resolve_triage_policy.py <change_dir> --init <profile>"
        )
        sys.exit(1)
    with open(policy_path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Section D: Triage
# ---------------------------------------------------------------------------

TRIAGE_SYSTEM_PROMPT = (
    "You are triaging specification gaps. For each gap, assign a triage value "
    "from the allowed actions based on the gap's severity and your analysis "
    "of the gap's nature. Output ONLY a JSON array to stdout.\n\n"
    "Format: [{\"id\": \"GAP-XX\", \"triage\": \"check-in|delegate|defer-release|defer-resolution\"}]"
)


def run_triage(
    change_dir: Path,
    tracker: WorkflowTracker,
    log: ResolutionLog,
    max_concurrent: int,
    timeout: int,
    budget: float | None,
    dry_run: bool,
) -> ResolutionLog:
    """Section D: Triage gap resolution method."""
    tracker.enter_section('D', 4)

    tracker.step("Loading triage policy and finding untriaged gaps")
    policy = load_triage_policy(change_dir)
    gaps_path = change_dir / 'gaps.md'
    if not gaps_path.exists():
        console.print("[red]No gaps.md found.[/red]")
        return log

    all_gaps = parse_gaps(gaps_path.read_text())
    untriaged = [g for g in all_gaps if not g['triage']]

    if not untriaged:
        console.print("[dim]No untriaged gaps found.[/dim]")
        return log

    console.print(f"Found [bold]{len(untriaged)}[/bold] untriaged gaps.")

    # Categorize gaps by their triage path
    single_option: list[tuple[dict, str]] = []  # (gap, action)
    agent_decided: list[dict] = []
    user_decided: list[tuple[dict, list[str]]] = []  # (gap, actions)

    for gap in untriaged:
        severity = (gap.get('severity') or 'medium').lower()
        policy_entry = policy.get(severity, policy.get('medium'))
        if not policy_entry:
            user_decided.append((gap, ['check-in', 'delegate', 'defer-release', 'defer-resolution']))
            continue

        actions = policy_entry['actions']
        authority = policy_entry['authority']

        if len(actions) == 1:
            single_option.append((gap, actions[0]))
        elif authority == 'agent':
            agent_decided.append(gap)
        else:
            user_decided.append((gap, actions))

    # Path 1: Single-option — apply directly
    tracker.step(f"Applying single-option triage values — {len(single_option)} gaps" if single_option else "Applying single-option triage values — skipped (0 gaps)")
    if single_option:
        for gap, action in single_option:
            write_gap_field(change_dir, gap['id'], 'Triage', action)
            log.triaged.append((gap['id'], action))
            console.print(f"  {gap['id']}: {action} (auto)")

    # Path 2: Agent-decided — claude -p
    tracker.step(f"Agent triage — {len(agent_decided)} gaps" if agent_decided else "Agent triage — skipped (0 gaps)")
    if agent_decided:
        with tracker.spinner("Running agent triage..."):
            triage_results = _run_agent_triage(
                change_dir, agent_decided, policy, max_concurrent, timeout, budget, dry_run
            )
        for gap_id, triage_value in triage_results:
            write_gap_field(change_dir, gap_id, 'Triage', triage_value)
            log.triaged.append((gap_id, triage_value))
            console.print(f"  {gap_id}: {triage_value} (agent)")

    # Path 3: User-decided — questionary
    tracker.step(f"User triage + summary — {len(user_decided)} gaps" if user_decided else "User triage + summary — skipped (0 gaps)")
    if user_decided:
        for gap, actions in user_decided:
            _display_gap_panel(gap)
            choice = questionary.select(
                f"Triage for {gap['id']}:",
                choices=actions,
            ).ask()
            if choice is None:
                console.print("[red]Aborted.[/red]")
                sys.exit(1)
            write_gap_field(change_dir, gap['id'], 'Triage', choice)
            log.triaged.append((gap['id'], choice))

    # Summary panel
    _display_triage_summary(log.triaged)
    return log


def _run_agent_triage(
    change_dir: Path,
    gaps: list[dict],
    policy: dict,
    max_concurrent: int,
    timeout: int,
    budget: float | None,
    dry_run: bool,
) -> list[tuple[str, str]]:
    """Launch a Sonnet claude -p subprocess to triage agent-decided gaps."""
    project_dir = resolve_project_dir(change_dir)
    gap_ids = [g['id'] for g in gaps]
    gap_entries = read_gap_entries(change_dir, gap_ids)

    # Build prompt
    skill_content = resolve_skill_content('tokamak:managing-spec-gaps') or ''
    prompt_parts = [
        "## Assignment\n",
        "Triage the following gaps by assigning each a resolution method.\n",
        "## Triage Policy\n",
    ]
    for severity in ['high', 'medium', 'low']:
        entry = policy.get(severity)
        if entry and entry.get('authority') == 'agent':
            actions = ', '.join(entry['actions'])
            prompt_parts.append(f"- **{severity.upper()}**: Choose from: {actions}")
    prompt_parts.extend([
        "\n## Gap Management Reference\n",
        skill_content,
        "\n## Gaps to Triage\n",
        gap_entries,
        "\n## Output Format\n",
        'Output a JSON array: [{"id": "GAP-XX", "triage": "<action>"}]',
    ])
    prompt = '\n'.join(prompt_parts)

    cmd = build_command(
        change_dir, project_dir,
        TRIAGE_SYSTEM_PROMPT, 'sonnet', budget,
        tools='Read',
    )

    if dry_run:
        console.print(Panel(f"[dim]DRY-RUN: Agent triage for {len(gaps)} gaps[/dim]"))
        console.print(f"CMD: {' '.join(cmd[:6])}...")
        return [(g['id'], 'check-in') for g in gaps]

    result = asyncio.run(_run_single_subprocess(
        "agent-triage", cmd, prompt, timeout, max_concurrent
    ))

    if result['status'] != 'success':
        console.print(f"[red]Agent triage failed: {result.get('error', 'unknown')}[/red]")
        console.print("[yellow]Falling back to user triage...[/yellow]")
        results = []
        for gap in gaps:
            _display_gap_panel(gap)
            severity = (gap.get('severity') or 'medium').lower()
            actions = policy.get(severity, {}).get('actions', ['check-in'])
            choice = questionary.select(
                f"Triage for {gap['id']}:", choices=actions
            ).ask()
            if choice is None:
                sys.exit(1)
            results.append((gap['id'], choice))
        return results

    parsed = result.get('report', [])
    triage_map = {e['id']: e['triage'] for e in parsed if 'id' in e and 'triage' in e}

    results = []
    for gap in gaps:
        triage_value = triage_map.get(gap['id'])
        if triage_value:
            results.append((gap['id'], triage_value))
        else:
            console.print(f"[yellow]Agent did not triage {gap['id']}, asking user...[/yellow]")
            _display_gap_panel(gap)
            severity = (gap.get('severity') or 'medium').lower()
            actions = policy.get(severity, {}).get('actions', ['check-in'])
            choice = questionary.select(
                f"Triage for {gap['id']}:", choices=actions
            ).ask()
            if choice is None:
                sys.exit(1)
            results.append((gap['id'], choice))

    return results


async def _run_single_subprocess(
    name: str, cmd: list[str], prompt: str, timeout: int, max_concurrent: int
) -> dict:
    """Run a single claude -p subprocess."""
    semaphore = asyncio.Semaphore(max_concurrent)
    return await run_one_subprocess(name, cmd, prompt, timeout, semaphore)


# ---------------------------------------------------------------------------
# Section E: Solve + Apply Decisions
# ---------------------------------------------------------------------------

DELEGATE_REVIEWER_SYSTEM_PROMPT = (
    "You are reviewing specification gap proposals for soundness. "
    "For each delegate proposal, evaluate whether the recommendation is well-reasoned, "
    "consistent with the specification files, and addresses the gap adequately. "
    "Output ONLY a JSON array to stdout.\n\n"
    "Format: [{\"gap_id\": \"GAP-XX\", \"accepted\": true|false, "
    "\"decision\": \"...\", \"primary_file\": \"...\", \"issues\": \"...\"}]\n\n"
    "When accepted is true, include decision and primary_file from the best proposal. "
    "When accepted is false, include issues describing what's wrong."
)

GROUPER_SYSTEM_PROMPT = (
    "You are grouping specification gaps for parallel solution development. "
    "Output ONLY a JSON object to stdout mapping group labels to gap ID lists.\n\n"
    'Format: {"group-label": ["GAP-XX", "GAP-YY"]}'
)


def run_solve(
    change_dir: Path,
    tracker: WorkflowTracker,
    log: ResolutionLog,
    max_concurrent: int,
    timeout: int,
    budget: float | None,
    dry_run: bool,
    gap_subset: list[str] | None = None,
) -> ResolutionLog:
    """Section E: Solve + apply decisions."""
    tracker.enter_section('E', 5)

    # Import solver functions
    sys.path.insert(0, str(Path(__file__).parent))
    from run_solvers import find_actionable_gaps, run_initial, run_resume

    # Find actionable gaps (optionally filtered to subset)
    tracker.step("Finding actionable gaps")
    actionable = find_actionable_gaps(change_dir)
    if gap_subset:
        actionable = [g for g in actionable if g['id'] in gap_subset]

    if not actionable:
        console.print("[dim]No actionable gaps for Section E.[/dim]")
        return log

    console.print(f"Found [bold]{len(actionable)}[/bold] actionable gaps.")

    # Handle defer-resolution gaps directly
    gaps_md = (change_dir / 'gaps.md').read_text()
    all_gaps = parse_gaps(gaps_md)
    defer_res = [g for g in all_gaps if g['triage'] == 'defer-resolution' and not g['decision']]
    if gap_subset:
        defer_res = [g for g in defer_res if g['id'] in gap_subset]
    for gap in defer_res:
        decision = "Defer resolution to a future change. Gap is blocking but resolution is out of scope."
        write_gap_field(change_dir, gap['id'], 'Decision', decision)
        write_gap_field(change_dir, gap['id'], 'Primary-file', 'gap-lifecycle')
        log.decided.append((gap['id'], 'defer-resolution'))
        console.print(f"  {gap['id']}: defer-resolution (auto)")

    # Group gaps for parallel solving
    tracker.step("Grouping gaps")
    with tracker.spinner("Running gap grouper..."):
        groups_json = _run_gap_grouper(change_dir, actionable, max_concurrent, timeout, budget, dry_run)

    # Run solvers (explore + solve)
    tracker.step("Running solvers")
    with tracker.spinner("Running solvers (explore + solve)..."):
        solver_result = asyncio.run(run_initial(
            change_dir, groups_json, max_concurrent, timeout, budget, dry_run,
        ))

    sessions = solver_result.get('sessions', {})
    proposals = solver_result.get('proposals', [])

    # Persist session IDs for crash recovery
    sessions_path = change_dir / '.solver-sessions.json'
    sessions_path.write_text(json.dumps(sessions, indent=2) + '\n')

    if not proposals and not dry_run:
        console.print("[yellow]No proposals returned from solvers.[/yellow]")
        _cleanup_sessions(sessions_path)
        return log

    # Process proposals by triage type
    rework_feedback: dict[str, dict] = {}  # gap_id -> {source, feedback}

    proposal_map = {p['gap_id']: p for p in proposals if 'gap_id' in p}
    actionable_map = {g['id']: g for g in actionable}

    # Separate by triage type
    delegate_proposals = []
    checkin_proposals = []
    defer_release_proposals = []
    placement_rejected_proposals = []

    for gap_id, proposal in proposal_map.items():
        gap = actionable_map.get(gap_id)
        if not gap:
            continue
        triage = gap.get('triage', '')
        if gap.get('placement_result'):
            placement_rejected_proposals.append((gap, proposal))
        elif triage == 'delegate':
            delegate_proposals.append((gap, proposal))
        elif triage == 'check-in':
            checkin_proposals.append((gap, proposal))
        elif triage == 'defer-release':
            defer_release_proposals.append((gap, proposal))
        else:
            checkin_proposals.append((gap, proposal))  # fallback

    # Process delegate proposals via AI reviewer
    tracker.step("Processing proposals")
    if delegate_proposals:
        console.print(f"\n[cyan]Reviewing {len(delegate_proposals)} delegate proposals...[/cyan]")
        with tracker.spinner("Reviewing delegate proposals..."):
            rework_feedback.update(
                _process_delegate_proposals(
                    change_dir, delegate_proposals, log,
                    max_concurrent, timeout, budget, dry_run
                )
            )

    # Process check-in proposals via user
    if checkin_proposals:
        console.print(f"\n[yellow]User decisions needed for {len(checkin_proposals)} check-in gaps...[/yellow]")
        rework_feedback.update(
            _process_user_proposals(change_dir, checkin_proposals, log, 'check-in')
        )

    # Process defer-release proposals via user
    if defer_release_proposals:
        console.print(f"\n[yellow]User decisions needed for {len(defer_release_proposals)} defer-release gaps...[/yellow]")
        rework_feedback.update(
            _process_user_proposals(change_dir, defer_release_proposals, log, 'defer-release')
        )

    # Process placement-rejected proposals via user
    if placement_rejected_proposals:
        console.print(f"\n[yellow]User decisions needed for {len(placement_rejected_proposals)} placement-rejected gaps...[/yellow]")
        rework_feedback.update(
            _process_user_proposals(change_dir, placement_rejected_proposals, log, 'placement-rejected')
        )

    # Rework loop
    tracker.step(f"Rework loop — {len(rework_feedback)} proposals" if rework_feedback else "Rework loop — skipped (0 proposals)")
    if rework_feedback:
        feedback_text = {gid: info['feedback'] for gid, info in rework_feedback.items()}
        with tracker.spinner("Reworking proposals..."):
            rework_result = asyncio.run(run_resume(
                change_dir, sessions, feedback_text,
                max_concurrent, timeout, budget, dry_run,
            ))
        reworked = rework_result.get('proposals', [])
        reworked_map = {p['gap_id']: p for p in reworked if 'gap_id' in p}

        # Re-present reworked proposals
        for gap_id, proposal in reworked_map.items():
            gap = actionable_map.get(gap_id)
            if not gap:
                continue
            console.print(f"\n[magenta]Reworked proposal for {gap_id}:[/magenta]")
            _display_proposal(proposal)
            decision, primary_file = _ask_user_proposal_decision(proposal)
            if decision:
                write_gap_fields(change_dir, gap_id, {
                    'Decision': decision,
                    'Primary-file': primary_file,
                })
                log.decided.append((gap_id, _truncate(decision, 60)))

    _cleanup_sessions(sessions_path)

    # Summary
    console.print(Panel(
        f"[green]Section E complete: {len(log.decided)} decisions recorded[/green]",
        title="Section E Summary",
    ))
    return log


def _run_gap_grouper(
    change_dir: Path,
    actionable: list[dict],
    max_concurrent: int,
    timeout: int,
    budget: float | None,
    dry_run: bool,
) -> dict[str, list[str]] | None:
    """Launch Haiku claude -p to group gaps for parallel solving."""
    if len(actionable) <= 2:
        # No grouping needed for small sets
        return None

    project_dir = resolve_project_dir(change_dir)
    gap_ids = [g['id'] for g in actionable]
    gap_entries = read_gap_entries(change_dir, gap_ids)

    prompt_parts = [
        "## Assignment\n",
        "Group these gaps for parallel solution development. Gaps that share "
        "thematic concerns or would affect the same specification areas should "
        "be grouped together.\n",
        "## Gaps\n",
        gap_entries,
        '\n## Output Format\n',
        'Output a JSON object mapping group labels to gap ID arrays:\n'
        '{"label1": ["GAP-XX", "GAP-YY"], "label2": ["GAP-ZZ"]}',
    ]
    prompt = '\n'.join(prompt_parts)

    cmd = build_command(
        change_dir, project_dir,
        GROUPER_SYSTEM_PROMPT, 'haiku', budget,
        tools='Read,Glob,Grep',
    )

    if dry_run:
        console.print(Panel("[dim]DRY-RUN: Gap grouper[/dim]"))
        return None

    result = asyncio.run(_run_single_subprocess(
        "gap-grouper", cmd, prompt, timeout, max_concurrent
    ))

    if result['status'] == 'success':
        # Try to parse the grouping
        output = result.get('output', '')
        try:
            groups = json.loads(output)
            if isinstance(groups, dict):
                return groups
        except json.JSONDecodeError:
            pass
        # Try from report
        report = result.get('report', [])
        if report and isinstance(report[0], dict):
            return report[0]

    console.print("[yellow]Grouper failed, proceeding without grouping.[/yellow]")
    return None


def _process_delegate_proposals(
    change_dir: Path,
    proposals: list[tuple[dict, dict]],
    log: ResolutionLog,
    max_concurrent: int,
    timeout: int,
    budget: float | None,
    dry_run: bool,
) -> dict[str, dict]:
    """Review delegate proposals via Sonnet claude -p and apply accepted ones.

    Returns rework feedback dict for rejected proposals.
    """
    project_dir = resolve_project_dir(change_dir)
    rework_feedback: dict[str, dict] = {}

    # Build prompt for reviewer
    proposals_json = []
    for gap, proposal in proposals:
        proposals_json.append({
            'gap_id': gap['id'],
            'title': gap.get('title', ''),
            'problem_context': proposal.get('problem_context', ''),
            'solutions': proposal.get('solutions', []),
            'recommendation': proposal.get('recommendation', {}),
        })

    gap_ids = [g['id'] for g, _ in proposals]
    gap_entries = read_gap_entries(change_dir, gap_ids)

    prompt_parts = [
        "## Assignment\n",
        "Review these delegate proposals for soundness. Accept well-reasoned "
        "proposals that address the gap adequately. Reject proposals with "
        "issues and explain what's wrong.\n",
        "## Gap Details\n",
        gap_entries,
        "\n## Proposals\n",
        "```json",
        json.dumps(proposals_json, indent=2),
        "```\n",
        "## Output Format\n",
        'Output a JSON array:\n'
        '[{"gap_id": "GAP-XX", "accepted": true, "decision": "...", '
        '"primary_file": "...", "issues": ""}]',
    ]
    prompt = '\n'.join(prompt_parts)

    cmd = build_command(
        change_dir, project_dir,
        DELEGATE_REVIEWER_SYSTEM_PROMPT, 'sonnet', budget,
        tools='Read',
    )

    if dry_run:
        console.print(Panel("[dim]DRY-RUN: Delegate reviewer[/dim]"))
        # In dry-run, auto-accept all
        for gap, proposal in proposals:
            rec = proposal.get('recommendation', {})
            rank = rec.get('rank', 1)
            solutions = proposal.get('solutions', [])
            sol = next((s for s in solutions if s.get('rank') == rank), solutions[0] if solutions else {})
            decision = sol.get('decision_text', 'Accepted by delegate')
            primary_file = sol.get('primary_file', 'gap-lifecycle')
            log.decided.append((gap['id'], _truncate(decision, 60)))
        return rework_feedback

    result = asyncio.run(_run_single_subprocess(
        "delegate-reviewer", cmd, prompt, timeout, max_concurrent
    ))

    if result['status'] != 'success':
        console.print("[red]Delegate reviewer failed, falling back to user review.[/red]")
        rework_feedback.update(
            _process_user_proposals(change_dir, proposals, log, 'delegate')
        )
        return rework_feedback

    reviews = result.get('report', [])
    review_map = {r['gap_id']: r for r in reviews if 'gap_id' in r}

    for gap, proposal in proposals:
        review = review_map.get(gap['id'])
        if review and review.get('accepted'):
            decision = review.get('decision', '')
            primary_file = review.get('primary_file', 'gap-lifecycle')
            write_gap_fields(change_dir, gap['id'], {
                'Decision': decision,
                'Primary-file': primary_file,
            })
            log.decided.append((gap['id'], _truncate(decision, 60)))
            console.print(f"  [green]{gap['id']}: accepted by reviewer[/green]")
        elif review:
            issues = review.get('issues', 'Reviewer found issues')
            console.print(f"  [red]{gap['id']}: rejected — {issues}[/red]")
            rework_feedback[gap['id']] = {
                'source': 'reviewer',
                'feedback': issues,
            }
        else:
            # Reviewer didn't return a result for this gap
            console.print(f"  [yellow]{gap['id']}: no reviewer result, asking user...[/yellow]")
            rework_feedback.update(
                _process_user_proposals(change_dir, [(gap, proposal)], log, 'delegate')
            )

    return rework_feedback


def _build_dependency_graph(proposals: list[tuple[dict, dict]]) -> dict[str, set[str]]:
    """Build bidirectional dependency graph from solver proposal metadata.

    Returns gap_id → set of dependent gap_ids.
    """
    dep_graph: dict[str, set[str]] = {}
    for _gap, proposal in proposals:
        gap_id = proposal.get('gap_id', '')
        for dep in proposal.get('dependencies', []):
            dep_id = dep.get('gap_id', '')
            if not dep_id or dep_id == gap_id:
                continue
            dep_graph.setdefault(gap_id, set()).add(dep_id)
            # Bidirectional for joint-decision
            if dep.get('relationship') == 'joint-decision':
                dep_graph.setdefault(dep_id, set()).add(gap_id)
    return dep_graph


def _reorder_for_dependencies(
    remaining: list[tuple[dict, dict]],
    decided_gaps: set[str],
    dep_graph: dict[str, set[str]],
    just_decided: str,
) -> list[tuple[dict, dict]]:
    """Re-order remaining proposals so that gaps affected by the latest
    decision are presented next.
    """
    affected = dep_graph.get(just_decided, set()) - decided_gaps
    if not affected:
        return remaining

    # Partition into affected (front) and unaffected (back)
    front = [p for p in remaining if p[1].get('gap_id', p[0]['id']) in affected]
    back = [p for p in remaining if p[1].get('gap_id', p[0]['id']) not in affected]
    return front + back


def _process_user_proposals(
    change_dir: Path,
    proposals: list[tuple[dict, dict]],
    log: ResolutionLog,
    triage_type: str,
) -> dict[str, dict]:
    """Present proposals to user via rich/questionary. Returns rework feedback.

    When solver proposals include dependency metadata, dependent gaps are
    presented together and the user is notified of cross-gap decision impacts.
    """
    rework_feedback: dict[str, dict] = {}
    dep_graph = _build_dependency_graph(proposals)
    decided_gaps: set[str] = set()
    remaining = list(proposals)

    # Show dependency clusters if any exist
    if dep_graph:
        clusters_shown: set[str] = set()
        for gap_id, deps in dep_graph.items():
            cluster = {gap_id} | deps
            cluster_key = ','.join(sorted(cluster))
            if cluster_key not in clusters_shown:
                clusters_shown.add(cluster_key)
                console.print(
                    f"[yellow]Dependency cluster: {', '.join(sorted(cluster))} "
                    f"— these gaps have decision dependencies[/yellow]"
                )

    while remaining:
        gap, proposal = remaining.pop(0)
        gap_id = proposal.get('gap_id', gap['id'])

        # Notify about dependencies with already-decided gaps
        related_decided = dep_graph.get(gap_id, set()) & decided_gaps
        if related_decided:
            console.print(
                f"[yellow]Note: {gap_id} has dependencies with already-decided "
                f"gaps: {', '.join(sorted(related_decided))}[/yellow]"
            )

        _display_proposal_panel(gap, proposal, triage_type)

        solutions = proposal.get('solutions', [])
        if not solutions:
            console.print(f"  [yellow]No solutions for {gap_id}[/yellow]")
            decided_gaps.add(gap_id)
            continue

        # Build choices
        choices = []
        rec = proposal.get('recommendation', {})
        rec_rank = rec.get('rank', 1)

        for sol in solutions:
            rank = sol.get('rank', 0)
            summary = sol.get('summary', 'No summary')
            label = f"[{rank}] {summary}"
            if rank == rec_rank:
                label += " (recommended)"
            choices.append(questionary.Choice(title=label, value=sol))

        choices.append(questionary.Choice(title="[Other — provide custom direction]", value='OTHER'))

        selected = questionary.select(
            f"Decision for {gap_id}:",
            choices=choices,
        ).ask()

        if selected is None:
            console.print("[red]Aborted.[/red]")
            sys.exit(1)

        if selected == 'OTHER':
            custom = questionary.text(
                f"Custom direction for {gap_id}:"
            ).ask()
            if custom is None:
                sys.exit(1)
            rework_feedback[gap_id] = {
                'source': 'user',
                'feedback': custom,
            }
        else:
            decision = selected.get('decision_text', '')
            primary_file = selected.get('primary_file', 'gap-lifecycle')
            write_gap_fields(change_dir, gap_id, {
                'Decision': decision,
                'Primary-file': primary_file,
            })
            log.decided.append((gap_id, _truncate(decision, 60)))

        decided_gaps.add(gap_id)

        # Re-order remaining to present affected gaps next
        if dep_graph.get(gap_id):
            affected = dep_graph[gap_id] - decided_gaps
            if affected:
                console.print(
                    f"[yellow]Decision on {gap_id} may affect: "
                    f"{', '.join(sorted(affected))}[/yellow]"
                )
                remaining = _reorder_for_dependencies(
                    remaining, decided_gaps, dep_graph, gap_id,
                )

    return rework_feedback


def _ask_user_proposal_decision(proposal: dict) -> tuple[str | None, str]:
    """Ask user to pick a solution from a reworked proposal. Returns (decision, primary_file)."""
    solutions = proposal.get('solutions', [])
    if not solutions:
        return None, 'gap-lifecycle'

    choices = []
    rec = proposal.get('recommendation', {})
    rec_rank = rec.get('rank', 1)

    for sol in solutions:
        rank = sol.get('rank', 0)
        summary = sol.get('summary', 'No summary')
        label = f"[{rank}] {summary}"
        if rank == rec_rank:
            label += " (recommended)"
        choices.append(questionary.Choice(title=label, value=sol))

    selected = questionary.select(
        "Select solution:", choices=choices,
    ).ask()

    if selected is None:
        sys.exit(1)

    return selected.get('decision_text', ''), selected.get('primary_file', 'gap-lifecycle')


# ---------------------------------------------------------------------------
# Section F: Resolve
# ---------------------------------------------------------------------------

def run_resolve(
    change_dir: Path,
    tracker: WorkflowTracker,
    log: ResolutionLog,
    max_concurrent: int,
    timeout: int,
    budget: float | None,
    dry_run: bool,
) -> tuple[ResolutionLog, list[str] | None]:
    """Section F: Resolve per-file."""
    tracker.enter_section('F', 3)

    sys.path.insert(0, str(Path(__file__).parent))
    from group_gaps import group_gaps
    from run_resolvers import run_all_phases

    # Check for ungrouped gaps
    tracker.step("Checking gap grouping")
    grouping = group_gaps(change_dir)
    ungrouped = grouping.get('ungrouped', [])

    if ungrouped:
        console.print(Panel(
            "[red]The following gaps are missing Primary-file assignments "
            "and cannot be resolved:[/red]\n\n" +
            '\n'.join(f"  - {gid}" for gid in ungrouped),
            title="Ungrouped Gaps",
        ))
        action = questionary.select(
            "How to proceed?",
            choices=[
                questionary.Choice("Assign Primary-file manually for each", value='assign'),
                questionary.Choice("Abort workflow", value='abort'),
            ],
        ).ask()

        if action is None or action == 'abort':
            console.print("[red]Aborted.[/red]")
            sys.exit(1)

        # Manual assignment
        from resolve_artifacts import resolve_artifacts
        artifacts_data = resolve_artifacts(change_dir)
        artifact_files = artifacts_data.get('files', [])
        file_choices = artifact_files + ['gap-lifecycle']

        for gap_id in ungrouped:
            chosen_file = questionary.select(
                f"Primary-file for {gap_id}:", choices=file_choices,
            ).ask()
            if chosen_file is None:
                sys.exit(1)
            write_gap_field(change_dir, gap_id, 'Primary-file', chosen_file)

    # Run all resolver phases
    tracker.step("Running resolvers")
    with tracker.spinner("Running resolvers (primary → propagation → collation)..."):
        result = asyncio.run(run_all_phases(
            change_dir, max_concurrent, timeout, budget, dry_run,
        ))

    collation = result.get('collation') or {}
    resolved_count = collation.get('resolved', 0)
    placement_rejected = collation.get('placement_rejected', 0)

    # Track resolved gaps
    primary_results = result.get('primary', {}).get('results', [])
    for pr in primary_results:
        for entry in pr.get('report', []):
            if entry.get('action') == 'resolved':
                gap_id = entry.get('gap', '')
                outcome = entry.get('outcome', '')
                log.resolved.append((gap_id, _truncate(outcome, 60)))

    tracker.step("Summary + circuit-break check")
    console.print(Panel(
        f"[green]Resolved: {resolved_count}[/green]\n"
        f"Placement rejected: {placement_rejected}\n"
        f"Conflicts: {len(collation.get('conflicts', []))}",
        title="Section F Summary",
    ))

    # Check for failures
    failed_resolvers = [
        r for r in primary_results if r.get('status') != 'success'
    ]
    if failed_resolvers:
        console.print(Panel(
            "[red]Failed resolvers:[/red]\n" +
            '\n'.join(f"  - {r['name']}: {r.get('error', 'unknown')}"
                      for r in failed_resolvers if r.get('status') != 'success'),
            title="Failures",
        ))
        proceed = questionary.confirm(
            "Proceed with partial results?", default=True
        ).ask()
        if not proceed:
            sys.exit(1)

    # Circuit-break check (Issue 3)
    circuit_break_gaps = None
    if placement_rejected and placement_rejected > 0:
        circuit_break_gaps = _check_circuit_breaks(change_dir)

    return log, circuit_break_gaps


def _check_circuit_breaks(change_dir: Path) -> list[str] | None:
    """Check for circuit-broken gaps after collation.

    Returns list of gap IDs that need re-entry to Section E, or None.
    """
    gaps_md = (change_dir / 'gaps.md').read_text()
    all_gaps = parse_gaps(gaps_md)

    circuit_broken = [
        g for g in all_gaps
        if g.get('placement_result') and 'circuit break' in (g['placement_result'] or '').lower()
    ]

    if not circuit_broken:
        return None

    console.print(Panel(
        "[red bold]Circuit Break Detected[/red bold]\n\n"
        "The following gaps were rejected from placement twice and escalated "
        "to user check-in:\n\n" +
        '\n'.join(f"  - {g['id']}: {g.get('title', '')}" for g in circuit_broken) +
        "\n\nThese gaps will be sent back to Section E for re-solving.",
        title="Circuit Break",
    ))

    return [g['id'] for g in circuit_broken]


# ---------------------------------------------------------------------------
# Section G: Cleanup
# ---------------------------------------------------------------------------

CATEGORIZER_SYSTEM_PROMPT = (
    "You are categorizing gap-detector findings. For each finding, determine "
    "whether it represents a stale concern (already resolved), a superseded "
    "concern (replaced by newer gap), or an uncovered concern (new gap needed). "
    "Output ONLY a JSON array to stdout.\n\n"
    "Format: [{\"finding_index\": 0, \"category\": \"stale|superseded|uncovered\", "
    "\"recommendation\": \"check-in|delegate|defer-release|defer-resolution\", "
    "\"reasoning\": \"...\"}]"
)


def run_cleanup(
    change_dir: Path,
    tracker: WorkflowTracker,
    log: ResolutionLog,
    max_concurrent: int,
    timeout: int,
    budget: float | None,
    dry_run: bool,
) -> ResolutionLog:
    """Section G: Gap cleanup."""
    tracker.enter_section('G', 4)

    sys.path.insert(0, str(Path(__file__).parent))
    from run_critics import run_all_critics, select_critics

    # Step 1: Run gap detectors
    tracker.step("Running gap detectors")
    critics_data = select_critics(change_dir, config_type='gap-detectors')
    project_dir = resolve_project_dir(change_dir)

    with tracker.spinner("Running gap detectors..."):
        detector_result = asyncio.run(run_all_critics(
            critics_data, change_dir, project_dir,
            max_concurrent, timeout, budget, dry_run,
        ))

    # Step 2: Record implicit gaps
    tracker.step("Recording implicit gaps")
    all_findings = []
    for cr in detector_result.get('results', []):
        if cr.get('status') != 'success':
            continue
        parsed = try_parse_json(cr.get('output', ''))
        for finding in parsed:
            finding['_critic'] = cr.get('name', 'unknown')
            all_findings.append(finding)

    if all_findings:
        console.print(f"\n[cyan]Found {len(all_findings)} detector findings.[/cyan]")
        current_id = next_gap_id(change_dir)
        gap_n = int(current_id.split('-')[1])

        new_gaps = []
        for finding in all_findings:
            gid = f'GAP-{gap_n}'
            title, severity, fields = format_detector_finding_as_gap(
                finding, gid, finding.get('_critic', 'unknown')
            )
            append_gap_entry(change_dir, gid, title, severity, fields)
            log.implicit_recorded.append((gid, title))
            new_gaps.append({'id': gid, 'title': title, 'severity': severity, 'finding': finding})
            gap_n += 1

        console.print(f"[green]Recorded {len(new_gaps)} implicit gaps.[/green]")

        # Step 3: Categorize findings via AI + user validation (Issue 6)
        tracker.step("Categorizing findings")
        if new_gaps and not dry_run:
            with tracker.spinner("Categorizing findings..."):
                _categorize_findings(
                    change_dir, new_gaps, log, max_concurrent, timeout, budget
                )
    else:
        console.print("[dim]No detector findings.[/dim]")
        tracker.step("Categorizing findings — skipped (0 findings)")

    # Step 4: Handle remaining actionable gaps from cleanup
    tracker.step("Handling remaining gaps + summary")
    from run_solvers import find_actionable_gaps
    remaining = find_actionable_gaps(change_dir)
    remaining_checkin = [g for g in remaining if g['triage'] in ('check-in', 'delegate')]

    if remaining_checkin:
        console.print(
            f"\n[yellow]{len(remaining_checkin)} remaining check-in/delegate gaps "
            f"from cleanup need solving.[/yellow]"
        )
        # Reuse Section E flow for these gaps
        subset_ids = [g['id'] for g in remaining_checkin]
        log = run_solve(
            change_dir, tracker, log, max_concurrent, timeout, budget, dry_run,
            gap_subset=subset_ids,
        )

    # Step 5: Handle defer-release gaps
    gaps_md = (change_dir / 'gaps.md').read_text()
    all_gaps = parse_gaps(gaps_md)
    defer_release = [g for g in all_gaps if g['triage'] == 'defer-release' and not g['decision']]
    for gap in defer_release:
        decision = "Acknowledge gap as acceptable for now, defer to future release."
        write_gap_field(change_dir, gap['id'], 'Decision', decision)
        write_gap_field(change_dir, gap['id'], 'Primary-file', 'gap-lifecycle')
        log.decided.append((gap['id'], 'defer-release'))

    # Step 6: Handle defer-resolution gaps
    all_gaps = parse_gaps((change_dir / 'gaps.md').read_text())
    defer_resolution = [g for g in all_gaps if g['triage'] == 'defer-resolution' and not g['decision']]
    for gap in defer_resolution:
        decision = "Blocking release, but defer resolution to future work."
        write_gap_field(change_dir, gap['id'], 'Decision', decision)
        write_gap_field(change_dir, gap['id'], 'Primary-file', 'gap-lifecycle')
        log.decided.append((gap['id'], 'defer-resolution'))

    console.print(Panel(
        f"[green]Implicit gaps recorded: {len(log.implicit_recorded)}[/green]",
        title="Section G Summary",
    ))
    return log


def _categorize_findings(
    change_dir: Path,
    new_gaps: list[dict],
    log: ResolutionLog,
    max_concurrent: int,
    timeout: int,
    budget: float | None,
) -> None:
    """AI-assisted categorization of detector findings with user validation."""
    project_dir = resolve_project_dir(change_dir)

    # Build prompt for categorizer
    findings_for_prompt = []
    for i, ng in enumerate(new_gaps):
        findings_for_prompt.append({
            'index': i,
            'gap_id': ng['id'],
            'title': ng['title'],
            'severity': ng['severity'],
            'description': ng['finding'].get('description', ng['finding'].get('finding', '')),
        })

    gap_ids = [ng['id'] for ng in new_gaps]
    gap_entries = read_gap_entries(change_dir, gap_ids)

    prompt_parts = [
        "## Assignment\n",
        "Categorize these detector findings. Determine whether each is:\n"
        "- **stale**: Already resolved by existing gaps/resolutions\n"
        "- **superseded**: Replaced by a newer, broader gap\n"
        "- **uncovered**: Genuinely new concern needing resolution\n",
        "## Findings\n",
        "```json",
        json.dumps(findings_for_prompt, indent=2),
        "```\n",
        "## Gap Context\n",
        gap_entries,
        "\n## Output Format\n",
        'Output a JSON array with one entry per finding:\n'
        '[{"finding_index": 0, "category": "stale|superseded|uncovered", '
        '"recommendation": "check-in|delegate|defer-release|defer-resolution", '
        '"reasoning": "Why this categorization"}]',
    ]
    prompt = '\n'.join(prompt_parts)

    cmd = build_command(
        change_dir, project_dir,
        CATEGORIZER_SYSTEM_PROMPT, 'sonnet', budget,
        tools='Read',
    )

    result = asyncio.run(_run_single_subprocess(
        "finding-categorizer", cmd, prompt, timeout, max_concurrent
    ))

    categorizations = {}
    if result['status'] == 'success':
        parsed = result.get('report', [])
        for entry in parsed:
            idx = entry.get('finding_index', -1)
            if 0 <= idx < len(new_gaps):
                categorizations[idx] = entry

    # Present each finding to user with AI recommendation as default
    for i, ng in enumerate(new_gaps):
        ai_cat = categorizations.get(i, {})
        ai_category = ai_cat.get('category', 'uncovered')
        ai_recommendation = ai_cat.get('recommendation', 'check-in')
        ai_reasoning = ai_cat.get('reasoning', '')

        console.print(Panel(
            f"**{ng['id']}**: {ng['title']}\n\n"
            f"AI categorization: [bold]{ai_category}[/bold]\n"
            f"AI recommendation: {ai_recommendation}\n"
            f"Reasoning: {ai_reasoning}",
            title=f"Finding {i + 1}/{len(new_gaps)}",
        ))

        # User validates or overrides
        choices = ['stale', 'superseded', 'uncovered']
        # Put AI recommendation first
        if ai_category in choices:
            choices.remove(ai_category)
            choices.insert(0, ai_category + ' (AI recommended)')

        choice = questionary.select(
            f"Category for {ng['id']}:", choices=choices,
        ).ask()
        if choice is None:
            sys.exit(1)

        category = choice.replace(' (AI recommended)', '')

        if category == 'stale':
            # Move to resolved as superseded/deprecated
            move_gap_to_resolved(
                change_dir, ng['id'], 'deprecated',
                f"Stale finding — already covered. {ai_reasoning}"
            )
        elif category == 'superseded':
            move_gap_to_resolved(
                change_dir, ng['id'], 'superseded',
                f"Superseded by broader gap. {ai_reasoning}"
            )
        else:
            # uncovered — assign triage
            triage_choices = ['check-in', 'delegate', 'defer-release', 'defer-resolution']
            if ai_recommendation in triage_choices:
                triage_choices.remove(ai_recommendation)
                triage_choices.insert(0, ai_recommendation + ' (AI recommended)')

            triage = questionary.select(
                f"Triage for {ng['id']}:", choices=triage_choices,
            ).ask()
            if triage is None:
                sys.exit(1)
            triage = triage.replace(' (AI recommended)', '')
            write_gap_field(change_dir, ng['id'], 'Triage', triage)


# ---------------------------------------------------------------------------
# Section H: Report
# ---------------------------------------------------------------------------

def run_report(
    change_dir: Path,
    tracker: WorkflowTracker,
    log: ResolutionLog,
    dry_run: bool,
) -> None:
    """Section H: Report and commit."""
    tracker.enter_section('H', 3)

    change_name = change_dir.name

    # Build summary
    tracker.step("Building summary tables")
    resolved_table = Table(title="Resolved Gaps")
    resolved_table.add_column("Gap ID", style="green")
    resolved_table.add_column("Outcome")
    for gap_id, outcome in log.resolved:
        resolved_table.add_row(gap_id, outcome)

    if log.implicit_recorded:
        implicit_table = Table(title="Implicit Gaps Recorded")
        implicit_table.add_column("Gap ID", style="cyan")
        implicit_table.add_column("Title")
        for gap_id, title in log.implicit_recorded:
            implicit_table.add_row(gap_id, title)

    # Display summary
    tracker.step("Displaying report")
    console.print()
    if log.resolved:
        console.print(resolved_table)
    if log.implicit_recorded:
        console.print(implicit_table)

    # Remaining gaps summary
    gaps_md = (change_dir / 'gaps.md').read_text()
    remaining = parse_gaps(gaps_md)
    if remaining:
        remaining_table = Table(title="Remaining Gaps")
        remaining_table.add_column("Gap ID", style="yellow")
        remaining_table.add_column("Severity")
        remaining_table.add_column("Triage")
        for gap in remaining:
            remaining_table.add_row(
                gap['id'],
                gap.get('severity', ''),
                gap.get('triage', '') or 'untriaged',
            )
        console.print(remaining_table)

    # Build commit message
    resolved_count = len(log.resolved)
    implicit_count = len(log.implicit_recorded)
    subject_parts = []
    if resolved_count:
        subject_parts.append(f"Resolve {resolved_count} gaps")
    if implicit_count:
        subject_parts.append(f"record {implicit_count} implicit gaps")

    if not subject_parts:
        console.print("[dim]No changes to commit.[/dim]")
        return

    subject = f"spec({change_name}): {', '.join(subject_parts)}"

    body_lines = []
    for gap_id, outcome in log.resolved:
        body_lines.append(f"- {gap_id}: resolved — {outcome}")
    for gap_id, title in log.implicit_recorded:
        body_lines.append(f"- {gap_id}: recorded — {title}")
    for gap_id, title in log.implicit_resolved:
        body_lines.append(f"- {gap_id}: implicit resolved — {title}")

    body = '\n'.join(body_lines)

    console.print(Panel(
        f"[bold]{subject}[/bold]\n\n{body}",
        title="Commit Message",
    ))

    if dry_run:
        console.print("[dim]DRY-RUN: Skipping commit.[/dim]")
        return

    # Stage and commit
    tracker.step("Stage and commit")
    proceed = questionary.confirm("Stage and commit?", default=True).ask()
    if not proceed:
        console.print("[dim]Skipped commit.[/dim]")
        return

    change_rel = str(change_dir)
    try:
        subprocess.run(
            ['git', 'add', change_rel],
            check=True, capture_output=True, text=True,
        )
        commit_msg = f"{subject}\n\n{body}"
        subprocess.run(
            ['git', 'commit', '-m', commit_msg],
            check=True, capture_output=True, text=True,
        )
        console.print("[green]Committed successfully.[/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Git error: {e.stderr}[/red]")


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _display_gap_panel(gap: dict) -> None:
    """Display a gap summary in a rich panel."""
    content = f"**{gap['id']}**: {gap.get('title', '')}\n\n"
    if gap.get('severity'):
        content += f"Severity: {gap['severity']}\n"
    if gap.get('description'):
        content += f"\n{gap['description']}"
    console.print(Panel(Markdown(content), title=gap['id']))


def _display_proposal(proposal: dict) -> None:
    """Display a proposal's solutions in a rich table."""
    solutions = proposal.get('solutions', [])
    if not solutions:
        return

    context = proposal.get('problem_context', '')
    if context:
        console.print(Panel(Markdown(context), title="Problem Context"))

    table = Table(title="Solutions")
    table.add_column("Rank", style="bold", width=4)
    table.add_column("Summary")
    table.add_column("Primary File", width=20)

    for sol in solutions:
        table.add_row(
            str(sol.get('rank', '')),
            sol.get('summary', ''),
            sol.get('primary_file', ''),
        )
    console.print(table)

    rec = proposal.get('recommendation', {})
    if rec:
        console.print(f"  [bold]Recommended:[/bold] Rank {rec.get('rank', '?')} — {rec.get('reasoning', '')}")


def _display_proposal_panel(gap: dict, proposal: dict, triage_type: str) -> None:
    """Display a full proposal panel for user decision."""
    _display_gap_panel(gap)

    context = proposal.get('problem_context', '')
    if context:
        console.print(Panel(Markdown(context), title="Problem Context"))

    solutions = proposal.get('solutions', [])
    rec = proposal.get('recommendation', {})
    rec_rank = rec.get('rank', 1)

    for sol in solutions:
        rank = sol.get('rank', 0)
        is_rec = rank == rec_rank
        style = "green" if is_rec else "white"
        title = f"Solution {rank}"
        if is_rec:
            title += " (recommended)"

        content_parts = [f"**{sol.get('summary', '')}**\n"]
        if sol.get('description'):
            content_parts.append(sol['description'] + '\n')
        if sol.get('strengths'):
            content_parts.append(f"**Strengths**: {sol['strengths']}\n")
        if sol.get('weaknesses'):
            content_parts.append(f"**Weaknesses**: {sol['weaknesses']}\n")
        if sol.get('cascading_effects'):
            content_parts.append("**Cascading effects**:\n")
            for effect in sol['cascading_effects']:
                content_parts.append(f"  - {effect}\n")
        if sol.get('primary_file'):
            content_parts.append(f"**Primary file**: {sol['primary_file']}\n")

        console.print(Panel(
            Markdown('\n'.join(content_parts)),
            title=title,
            border_style=style,
        ))


def _display_triage_summary(triaged: list[tuple[str, str]]) -> None:
    """Display a triage summary panel."""
    if not triaged:
        return

    table = Table(title="Triage Results")
    table.add_column("Gap ID", style="bold")
    table.add_column("Triage")

    for gap_id, triage_value in triaged:
        style = {
            'check-in': 'yellow',
            'delegate': 'cyan',
            'defer-release': 'blue',
            'defer-resolution': 'dim',
        }.get(triage_value, 'white')
        table.add_row(gap_id, f"[{style}]{triage_value}[/{style}]")

    console.print(table)


def _truncate(text: str, max_len: int) -> str:
    """Truncate text to max_len characters."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + '...'


def _cleanup_sessions(sessions_path: Path) -> None:
    """Remove session persistence file."""
    if sessions_path.exists():
        sessions_path.unlink()


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

    start_section = args.from_section
    start_idx = SECTION_ORDER.index(start_section)
    log = ResolutionLog()
    tracker = WorkflowTracker(start_section=start_section)

    console.print(Panel(
        f"Change: [bold]{change_dir.name}[/bold]\n"
        f"Starting from: Section {start_section}\n"
        f"Dry run: {args.dry_run}\n"
        f"Max concurrent: {args.max_concurrent}\n"
        f"Budget: {args.budget or 'unlimited'}",
        title="Resolve Gaps Workflow",
    ))

    # Section D: Triage
    if start_idx <= SECTION_ORDER.index('D'):
        log = run_triage(
            change_dir, tracker, log,
            args.max_concurrent, args.timeout, args.budget, args.dry_run,
        )
        tracker.complete_section()

    # Section E: Solve + Decide
    if start_idx <= SECTION_ORDER.index('E'):
        # Check for cached sessions on resume
        sessions_path = change_dir / '.solver-sessions.json'
        if start_section == 'E' and sessions_path.exists():
            console.print("[yellow]Found cached solver sessions from previous run.[/yellow]")
            use_cached = questionary.confirm(
                "Resume from cached sessions?", default=True
            ).ask()
            if not use_cached:
                _cleanup_sessions(sessions_path)

        log = run_solve(
            change_dir, tracker, log,
            args.max_concurrent, args.timeout, args.budget, args.dry_run,
        )
        tracker.complete_section()

    # Section F: Resolve (with circuit-break re-entry)
    if start_idx <= SECTION_ORDER.index('F'):
        log, circuit_break_ids = run_resolve(
            change_dir, tracker, log,
            args.max_concurrent, args.timeout, args.budget, args.dry_run,
        )
        tracker.complete_section()

        if circuit_break_ids:
            console.print(
                f"\n[magenta]Re-entering Section E for {len(circuit_break_ids)} "
                f"circuit-broken gaps...[/magenta]"
            )
            log = run_solve(
                change_dir, tracker, log,
                args.max_concurrent, args.timeout, args.budget, args.dry_run,
                gap_subset=circuit_break_ids,
            )
            # Re-run resolve for the subset
            log, still_broken = run_resolve(
                change_dir, tracker, log,
                args.max_concurrent, args.timeout, args.budget, args.dry_run,
            )
            if still_broken:
                console.print("[red]Circuit break persists after re-entry. Manual intervention needed.[/red]")

    # Section G: Cleanup
    if start_idx <= SECTION_ORDER.index('G'):
        log = run_cleanup(
            change_dir, tracker, log,
            args.max_concurrent, args.timeout, args.budget, args.dry_run,
        )
        tracker.complete_section()

    # Section H: Report + Commit
    if start_idx <= SECTION_ORDER.index('H'):
        run_report(change_dir, tracker, log, args.dry_run)
        tracker.complete_section()

    console.print("\n[bold green]Workflow complete.[/bold green]")


if __name__ == '__main__':
    main()
