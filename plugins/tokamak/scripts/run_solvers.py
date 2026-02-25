#!/usr/bin/env python3
"""
Parallel solver orchestrator for OpenSpec gap solution development.

Two-phase architecture:
  Phase 1 (Explore): Haiku subprocesses gather codebase context per gap group
  Phase 2 (Solve): Opus subprocesses develop solutions using specs + codebase context

Supports session resume for rework when proposals are rejected.

Usage:
    # Initial run
    python run_solvers.py <change_dir> --groups '<json>' [--max-concurrent N] [--timeout S] [--dry-run] [--budget N]

    # Resume for rework
    python run_solvers.py <change_dir> --resume --sessions '<json>' --feedback '<json>' [--timeout S] [--budget N]
"""

import argparse
import asyncio
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from spec_utils import (
    build_command,
    gather_with_callback,
    load_schema_artifacts,
    lookup_artifact,
    parse_gaps,
    read_gap_entries,
    resolve_project_dir,
    resolve_skill_content,
    run_one_subprocess,
    try_parse_json,
)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Run parallel gap solvers via claude -p (explore + solve)'
    )
    parser.add_argument('change_dir', type=Path,
                        help='Path to OpenSpec change directory')
    parser.add_argument('--groups', type=str, default=None,
                        help='JSON mapping group labels to gap ID lists')
    parser.add_argument('--max-concurrent', type=int, default=6,
                        help='Maximum parallel claude -p processes (default: 6)')
    parser.add_argument('--timeout', type=int, default=600,
                        help='Timeout per subprocess in seconds (default: 600)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print prompts and commands without launching processes')
    parser.add_argument('--budget', type=float, default=None,
                        help='Max budget per subprocess in USD')

    # Resume mode
    parser.add_argument('--resume', action='store_true',
                        help='Resume solver sessions with rework feedback')
    parser.add_argument('--sessions', type=str, default=None,
                        help='JSON mapping group labels to session IDs (resume mode)')
    parser.add_argument('--feedback', type=str, default=None,
                        help='JSON mapping gap IDs to feedback text (resume mode)')

    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Repo root derivation
# ---------------------------------------------------------------------------

def resolve_repo_root(change_dir: Path) -> Path:
    """Derive repo root from change_dir: openspec/changes/<name> → repo root.

    Validates by checking .git exists.
    """
    repo_root = change_dir.parent.parent.parent
    if not (repo_root / '.git').exists():
        print(f"WARNING: .git not found at derived repo root: {repo_root}",
              file=sys.stderr)
    return repo_root


# ---------------------------------------------------------------------------
# Actionable gap identification
# ---------------------------------------------------------------------------

def find_actionable_gaps(change_dir: Path) -> list[dict]:
    """Identify gaps that need solution development.

    Actionable gaps:
    - Have Triage but no Decision → need solution development
    - Have Placement-result → placement-rejected, need re-evaluation
    - Skip defer-resolution (handled directly by orchestrator)
    """
    gaps_path = change_dir / 'gaps.md'
    if not gaps_path.exists():
        return []

    content = gaps_path.read_text()
    all_gaps = parse_gaps(content)
    actionable = []

    for gap in all_gaps:
        # Placement-rejected: has Placement-result field
        if gap['placement_result']:
            actionable.append(gap)
            continue

        # Has triage but no decision → needs solution development
        if gap['triage'] and not gap['decision']:
            # Skip defer-resolution (orchestrator handles directly)
            if gap['triage'] == 'defer-resolution':
                continue
            actionable.append(gap)

    return actionable


# ---------------------------------------------------------------------------
# Artifact resolution helpers
# ---------------------------------------------------------------------------

def resolve_artifact_files(change_dir: Path) -> list[str]:
    """Get list of artifact files in the change directory."""
    script = Path(__file__).parent / 'resolve_artifacts.py'
    result = subprocess.run(
        [sys.executable, str(script), str(change_dir)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"WARNING: resolve_artifacts.py failed: {result.stderr}",
              file=sys.stderr)
        return []
    data = json.loads(result.stdout)
    return data.get('files', [])


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

EXPLORER_SYSTEM_PROMPT = (
    "You are a codebase investigator gathering context for specification work. "
    "Use Glob to find files, Grep to search content, and Read to examine code. "
    "Do NOT modify any files. Focus on facts, not opinions. "
    "Output ONLY a JSON array to stdout matching the format in the prompt."
)

SOLVER_SYSTEM_PROMPT = (
    "You are a specification architect developing solutions for gaps. "
    "You have READ-ONLY access to specification files — do NOT modify any files. "
    "Read the specification files listed in the prompt to understand the current "
    "state before developing solutions. Use the codebase context section to "
    "ground your solutions in the actual implementation. "
    "All solution vocabulary must use specification conventions, not "
    "implementation or architecture language. "
    "Output ONLY a JSON array to stdout matching the format in the prompt."
)


# ---------------------------------------------------------------------------
# Phase 1: Explore prompts
# ---------------------------------------------------------------------------

def build_explorer_prompt(
    group_gaps: list[dict],
    repo_root: Path,
    project_dir: Path | None,
) -> str:
    """Build prompt for a Phase 1 Haiku explorer subprocess."""
    parts = []

    parts.append("## Assignment\n")
    parts.append(
        "You are investigating a codebase to gather context for specification gap "
        "resolution. For each gap, search the codebase to find relevant implementations, "
        "patterns, and constraints. Your findings will be used by a specification "
        "architect to develop solutions.\n"
    )

    parts.append("## Gaps to Investigate\n")
    for gap in group_gaps:
        parts.append(f"### {gap['id']}: {gap.get('title', '')}")
        if gap.get('severity'):
            parts.append(f"- **Severity**: {gap['severity']}")
        if gap.get('description'):
            parts.append(f"- **Description**: {gap['description']}")
        if gap.get('placement_result'):
            parts.append(f"- **Placement-result**: {gap['placement_result']}")
        parts.append("")

    parts.append("## Codebase\n")
    parts.append(f"The repository root is `{repo_root}/`.")
    if project_dir:
        parts.append(f"The relevant project directory is `{project_dir}/`.")
    parts.append("")

    parts.append("## Instructions\n")
    parts.append(
        "For each gap:\n"
        "1. Search for existing implementations related to the gap's concern\n"
        "   - Use Grep to find relevant functions, classes, patterns\n"
        "   - Use Glob to locate related files\n"
        "   - Read key files to understand current behavior\n"
        "2. Identify patterns and conventions the codebase follows for similar\n"
        "   functionality\n"
        "3. Find constraints: dependencies, APIs, data structures that would\n"
        "   affect solutions\n"
        "4. Note any existing tests or validation related to the concern\n\n"
        "Focus on finding FACTS — what exists, what patterns are used, what\n"
        "constraints apply. Do NOT develop solutions or recommendations.\n\n"
        "Keep code snippets concise (max 20 lines each). Prioritize the most\n"
        "relevant findings.\n"
    )

    parts.append("## Output Format\n")
    parts.append(
        "Output a JSON array with one entry per gap:\n\n"
        "[\n"
        "  {\n"
        '    "gap_id": "GAP-200",\n'
        '    "findings": [\n'
        "      {\n"
        '        "category": "implementation",\n'
        '        "location": "plugins/foo/scripts/bar.py:42",\n'
        '        "summary": "What was found and why it\'s relevant",\n'
        '        "snippet": "def validate_input(...):\\n    ..."\n'
        "      },\n"
        "      {\n"
        '        "category": "pattern",\n'
        '        "location": "plugins/foo/scripts/",\n'
        '        "summary": "Convention observed across the codebase",\n'
        '        "snippet": ""\n'
        "      },\n"
        "      {\n"
        '        "category": "constraint",\n'
        '        "location": "plugins/foo/scripts/baz.py:10",\n'
        '        "summary": "Dependency or API contract that limits solutions",\n'
        '        "snippet": "from spec_utils import ..."\n'
        "      }\n"
        "    ],\n"
        '    "summary": "Overall codebase context for this gap"\n'
        "  }\n"
        "]"
    )

    return '\n'.join(parts)


# ---------------------------------------------------------------------------
# Phase 2: Solve prompts
# ---------------------------------------------------------------------------

COMMON_SOLVER_SKILLS = [
    'tokamak:managing-spec-gaps',
]


def build_solver_prompt(
    group_gaps: list[dict],
    exploration_results: list[dict],
    change_dir: Path,
    change_name: str,
    artifact_files: list[str],
    project_dir: Path | None,
) -> str:
    """Build prompt for a Phase 2 Opus solver subprocess."""
    parts = []

    parts.append("## Assignment\n")
    parts.append(
        f"You are developing solutions for specification gaps in the `{change_name}` change. "
        "For each gap below, analyze the problem using the codebase context and specification "
        "files provided, and develop multiple solutions. Do NOT modify any files.\n"
    )
    parts.append("Gaps assigned to this solver:")
    for gap in group_gaps:
        triage = gap.get('triage', 'unknown')
        if gap.get('placement_result'):
            triage = 'placement-rejected'
        parts.append(f"- {gap['id']} (triage: {triage})")
    parts.append("")

    # Gap details from gaps.md
    gap_ids = [g['id'] for g in group_gaps]
    gap_entries = read_gap_entries(change_dir, gap_ids)
    parts.append("## Gap Details\n")
    parts.append(gap_entries)
    parts.append("")

    # Codebase context from exploration
    if exploration_results:
        parts.append("## Codebase Context\n")
        parts.append(
            "The following codebase investigation was performed for each gap. Use these "
            "findings to ground your solutions in what actually exists in the code.\n"
        )
        for entry in exploration_results:
            gap_id = entry.get('gap_id', 'unknown')
            summary = entry.get('summary', '')
            parts.append(f"### {gap_id}: {summary}\n")
            for finding in entry.get('findings', []):
                category = finding.get('category', '')
                location = finding.get('location', '')
                finding_summary = finding.get('summary', '')
                snippet = finding.get('snippet', '')
                parts.append(f"**{category}** — `{location}`")
                parts.append(finding_summary)
                if snippet:
                    parts.append(f"```\n{snippet}\n```")
                parts.append("")
        parts.append("")

    # Specification files
    parts.append("## Specification Files (read-only)\n")
    parts.append(f"Read these files from `{change_dir}/` to understand the current specification state:")
    for f in artifact_files:
        parts.append(f"- `{change_dir}/{f}`")
    parts.append("")

    # Artifact purposes from schema
    schema_artifacts = load_schema_artifacts(change_dir)
    if schema_artifacts:
        parts.append("## Artifact Purposes\n")
        parts.append(
            "Each specification file serves a specific purpose. Use these descriptions to "
            "determine which file each solution's changes primarily belong in:\n"
        )
        for generates, config in schema_artifacts.items():
            parts.append(f"### {generates}")
            parts.append(config['instruction'])
            parts.append("")

    # Project reference files
    if project_dir:
        parts.append("## Project Reference Files (read-only)\n")
        parts.append(f"Read from `{project_dir}/` for cross-project consistency:")
        for f in ['functional.md', 'technical.md', 'infra.md']:
            pf = project_dir / f
            if pf.exists():
                parts.append(f"- `{project_dir}/{f}`")
        req_dir = project_dir / 'requirements'
        if req_dir.is_dir():
            for rf in sorted(req_dir.rglob('*.feature.md')):
                parts.append(f"- `{rf}`")
        parts.append("")

    # Spec-writing skills — collect unique skills across ALL artifact types + managing-spec-gaps
    all_skill_names = list(COMMON_SOLVER_SKILLS)
    for config in schema_artifacts.values():
        for s in config.get('skills', []):
            if s not in all_skill_names:
                all_skill_names.append(s)

    parts.append("## Spec-Writing Skills\n")
    parts.append(
        "Use these skills as vocabulary and structural reference when drafting Decision "
        "text. Solutions must use specification language, not implementation/architecture "
        "language.\n"
    )
    for skill_name in all_skill_names:
        content = resolve_skill_content(skill_name)
        if content:
            parts.append(f"### {skill_name}\n")
            parts.append(content)
            parts.append("")

    # Instructions per triage type
    parts.append("## Instructions\n")
    parts.append(
        "For each gap, develop solutions following the rules for its triage type.\n\n"
        "Read the specification files BEFORE developing solutions — your solutions must "
        "account for what already exists in the specs. Use the codebase context to ensure "
        "solutions are grounded in the actual implementation.\n"
    )

    parts.append("### For check-in gaps\n")
    parts.append(
        "1. Develop 5+ solutions that account for cascading effects into other spec\n"
        "   sections and files\n"
        "2. Sort solutions from best to worst\n"
        "3. For each solution provide:\n"
        "   - A one-line summary\n"
        "   - Full description of the approach\n"
        "   - Strengths: why this works\n"
        "   - Weaknesses: what's wrong with it\n"
        "   - Cascading effects: which other spec files/sections would need updates\n"
        "   - Decision text: the exact text to record in gaps.md as the Decision field\n"
        "   - Primary file: which artifact file the resolution primarily modifies\n"
        "4. Recommend one solution and explain why\n"
    )

    parts.append("### For delegate gaps\n")
    parts.append(
        "1. Develop 3+ solutions that account for cascading effects\n"
        "2. Same format as check-in\n"
        "3. Pick the best solution yourself and explain why\n"
    )

    parts.append("### For defer-release gaps\n")
    parts.append(
        "1. Develop 4 plausible rationale approaches considering:\n"
        "   - Functional scope, capability, and risk impacts of deferment\n"
        "   - Where the deferral should be recorded: Functional Out of Scope,\n"
        "     Functional Known Risk, Technical Decision, Technical Known Risk,\n"
        "     or combinations\n"
        "2. Sort approaches from best to worst\n"
        "3. For each approach provide:\n"
        "   - Summary of the rationale\n"
        "   - Where it gets recorded (which spec sections)\n"
        "   - Why this framing is appropriate\n"
        "   - What's wrong with this framing\n"
        "   - Decision text: the exact text to record in gaps.md\n"
        "   - Primary file: which artifact file the resolution primarily modifies\n"
        "4. Recommend one approach and explain why\n"
    )

    parts.append("### For placement-rejected gaps\n")
    parts.append(
        "1. Read the Placement-result field to understand the rejection reason and\n"
        "   recommended file\n"
        "2. Propose 3 alternatives:\n"
        "   a. Accept the recommended file from Placement-result — draft a Decision\n"
        "      that fits that file's purpose\n"
        "   b. A different file — explain why it's a better fit, draft a Decision\n"
        "   c. Revise the original Decision — rewrite it to fit the original file's\n"
        "      purpose\n"
        "3. For each alternative provide:\n"
        "   - Summary of the approach\n"
        "   - Decision text\n"
        "   - Primary file\n"
        "   - Why this alternative works\n"
        "4. Recommend one alternative and explain why\n"
    )

    # Dependency detection
    parts.append("### Dependency detection\n")
    parts.append(
        "If any gaps in your assignment have decision dependencies — where choosing\n"
        "a solution for one gap constrains or invalidates solutions for another —\n"
        "declare them in a \"dependencies\" field. Types:\n"
        "- \"joint-decision\": gaps must be decided together\n"
        "- \"constrains\": this gap's decision narrows options for the dependent gap\n"
        "- \"invalidates\": choosing certain solutions here would make the other gap moot\n\n"
        "Only declare genuine dependencies where an implementor could make\n"
        "inconsistent decisions. Do not flag thematic similarity as dependency.\n"
    )

    # Output format
    parts.append("## Output Format\n")
    parts.append(
        "Output a JSON array with one entry per gap:\n\n"
        "[\n"
        "  {\n"
        '    "gap_id": "GAP-200",\n'
        '    "triage": "check-in",\n'
        '    "dependencies": [\n'
        "      {\n"
        '        "gap_id": "GAP-201",\n'
        '        "relationship": "joint-decision",\n'
        '        "rationale": "Both gaps concern the same design axis"\n'
        "      }\n"
        "    ],\n"
        '    "problem_context": "A clear explanation of the problem for a user who\n'
        '      has not read the gap details. Include enough context for an informed\n'
        '      decision.",\n'
        '    "solutions": [\n'
        "      {\n"
        '        "rank": 1,\n'
        '        "summary": "One-line summary of this approach",\n'
        '        "description": "Full description of the approach",\n'
        '        "strengths": "Why this works well",\n'
        '        "weaknesses": "What\'s wrong with it or what it trades off",\n'
        '        "cascading_effects": [\n'
        '          "functional.md: Section X needs corresponding update",\n'
        '          "requirements/foo/requirements.feature.md: Add coverage scenario"\n'
        "        ],\n"
        '        "decision_text": "The exact Decision text to record in gaps.md",\n'
        '        "primary_file": "functional.md"\n'
        "      }\n"
        "    ],\n"
        '    "recommendation": {\n'
        '      "rank": 1,\n'
        '      "reasoning": "Why this is the best option"\n'
        "    }\n"
        "  }\n"
        "]\n\n"
        "Omit the \"dependencies\" field entirely if a gap has no dependencies."
    )

    return '\n'.join(parts)


# ---------------------------------------------------------------------------
# Rework prompt
# ---------------------------------------------------------------------------

def build_rework_prompt(feedback: dict[str, str]) -> str:
    """Build prompt for rework via session resume."""
    parts = []

    parts.append("## Rework Request\n")
    parts.append(
        "The following proposals were reviewed and need improvement.\n"
    )

    for gap_id, feedback_text in feedback.items():
        parts.append(f"### {gap_id}\n")
        parts.append(f"**Feedback**: {feedback_text}\n")

    parts.append(
        "Develop improved solutions addressing the feedback above. You have full context "
        "from your previous analysis — do not repeat findings, focus on addressing the "
        "specific feedback.\n\n"
        "Output the same JSON format as before, but only include entries for the gaps "
        "listed above. Gaps not listed here were accepted as-is."
    )

    return '\n'.join(parts)


# ---------------------------------------------------------------------------
# Phase execution
# ---------------------------------------------------------------------------

async def run_exploration_phase(
    groups: dict[str, list[dict]],
    repo_root: Path,
    change_dir: Path,
    project_dir: Path | None,
    max_concurrent: int,
    timeout: int,
    budget: float | None,
    dry_run: bool,
    on_complete: callable = None,
) -> tuple[dict[str, list[dict]], list[dict]]:
    """Phase 1: Run Haiku explorers per group.

    Returns (exploration, failures) where failures is a list of
    {'name': str, 'error': str, 'phase': 'explore'} dicts.
    """
    if dry_run:
        for label, group_gaps in groups.items():
            prompt = build_explorer_prompt(group_gaps, repo_root, project_dir)
            cmd = build_command(
                change_dir, project_dir,
                EXPLORER_SYSTEM_PROMPT, 'haiku', budget,
                tools='Read,Glob,Grep',
                extra_dirs=[repo_root],
            )
            print(f"\n{'=' * 60}", file=sys.stderr)
            print(f"EXPLORER: {label} ({len(group_gaps)} gaps)", file=sys.stderr)
            print(f"GAPS: {', '.join(g['id'] for g in group_gaps)}", file=sys.stderr)
            print(f"CMD: {cmd[:6]}...", file=sys.stderr)
            print(f"PROMPT:\n{prompt}", file=sys.stderr)
        return {}, []

    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = []
    labels = []

    for label, group_gaps in groups.items():
        prompt = build_explorer_prompt(group_gaps, repo_root, project_dir)
        cmd = build_command(
            change_dir, project_dir,
            EXPLORER_SYSTEM_PROMPT, 'haiku', budget,
            tools='Read,Glob,Grep',
            extra_dirs=[repo_root],
        )
        tasks.append(run_one_subprocess(
            f"explore:{label}", cmd, prompt, timeout, semaphore,
        ))
        labels.append(label)

    results = await gather_with_callback(tasks, on_complete)

    exploration: dict[str, list[dict]] = {}
    failures: list[dict] = []
    for i, result in enumerate(results):
        label = labels[i]
        if result['status'] == 'success':
            exploration[label] = result.get('report', [])
            print(f"[EXPLORE] {label}: {len(exploration[label])} gap contexts",
                  file=sys.stderr)
        else:
            exploration[label] = []
            failures.append({
                'name': f'explore:{label}',
                'error': result.get('error', 'unknown'),
                'phase': 'explore',
            })
            print(f"[EXPLORE] {label}: FAILED — {result.get('error', 'unknown')}",
                  file=sys.stderr)

    return exploration, failures


async def run_solver_phase(
    groups: dict[str, list[dict]],
    exploration: dict[str, list[dict]],
    change_dir: Path,
    change_name: str,
    artifact_files: list[str],
    project_dir: Path | None,
    max_concurrent: int,
    timeout: int,
    budget: float | None,
    dry_run: bool,
    on_complete: callable = None,
) -> tuple[dict[str, str], list[dict], list[dict]]:
    """Phase 2: Run Opus solvers per group.

    Returns (sessions, proposals, failures) where failures is a list of
    {'name': str, 'error': str, 'phase': 'solve'} dicts.
    """
    sessions: dict[str, str] = {}
    all_proposals: list[dict] = []

    if dry_run:
        for label, group_gaps in groups.items():
            session_id = str(uuid.uuid4())
            sessions[label] = session_id
            explore_results = exploration.get(label, [])
            prompt = build_solver_prompt(
                group_gaps, explore_results, change_dir, change_name,
                artifact_files, project_dir,
            )
            cmd = build_command(
                change_dir, project_dir,
                SOLVER_SYSTEM_PROMPT, 'opus', budget,
                tools='Read',
                session_id=session_id,
            )
            print(f"\n{'=' * 60}", file=sys.stderr)
            print(f"SOLVER: {label} ({len(group_gaps)} gaps)", file=sys.stderr)
            print(f"GAPS: {', '.join(g['id'] for g in group_gaps)}", file=sys.stderr)
            print(f"SESSION: {session_id}", file=sys.stderr)
            print(f"CMD: {cmd[:6]}...", file=sys.stderr)
            print(f"PROMPT:\n{prompt}", file=sys.stderr)
        return sessions, [], []

    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = []
    labels = []

    for label, group_gaps in groups.items():
        session_id = str(uuid.uuid4())
        sessions[label] = session_id
        explore_results = exploration.get(label, [])
        prompt = build_solver_prompt(
            group_gaps, explore_results, change_dir, change_name,
            artifact_files, project_dir,
        )
        cmd = build_command(
            change_dir, project_dir,
            SOLVER_SYSTEM_PROMPT, 'opus', budget,
            tools='Read',
            session_id=session_id,
        )
        tasks.append(run_one_subprocess(
            f"solve:{label}", cmd, prompt, timeout, semaphore,
        ))
        labels.append(label)

    results = await gather_with_callback(tasks, on_complete)

    failures: list[dict] = []
    for i, result in enumerate(results):
        label = labels[i]
        if result['status'] == 'success':
            proposals = result.get('report', [])
            all_proposals.extend(proposals)
            print(f"[SOLVE] {label}: {len(proposals)} proposals",
                  file=sys.stderr)
        else:
            failures.append({
                'name': f'solve:{label}',
                'error': result.get('error', 'unknown'),
                'phase': 'solve',
            })
            print(f"[SOLVE] {label}: FAILED — {result.get('error', 'unknown')}",
                  file=sys.stderr)

    return sessions, all_proposals, failures


async def run_rework_phase(
    sessions: dict[str, str],
    feedback: dict[str, str],
    groups: dict[str, list[dict]],
    change_dir: Path,
    project_dir: Path | None,
    max_concurrent: int,
    timeout: int,
    budget: float | None,
    dry_run: bool,
    on_complete: callable = None,
) -> tuple[list[dict], list[dict]]:
    """Resume solver sessions with rework feedback.

    Returns (proposals, failures) where failures is a list of
    {'name': str, 'error': str, 'phase': 'rework'} dicts.
    """
    # Determine which sessions need rework based on feedback gap IDs
    feedback_gap_ids = set(feedback.keys())
    sessions_to_resume: dict[str, dict] = {}  # label → {session_id, feedback subset}

    for label, group_gaps in groups.items():
        group_gap_ids = {g['id'] for g in group_gaps}
        overlap = feedback_gap_ids & group_gap_ids
        if overlap:
            session_id = sessions.get(label)
            if session_id:
                sessions_to_resume[label] = {
                    'session_id': session_id,
                    'feedback': {gid: feedback[gid] for gid in overlap},
                }

    if not sessions_to_resume:
        print("No sessions need rework.", file=sys.stderr)
        return [], []

    if dry_run:
        for label, info in sessions_to_resume.items():
            prompt = build_rework_prompt(info['feedback'])
            cmd = build_command(
                change_dir, project_dir,
                SOLVER_SYSTEM_PROMPT, 'opus', budget,
                tools='Read',
                session_id=info['session_id'],
                resume=True,
            )
            print(f"\n{'=' * 60}", file=sys.stderr)
            print(f"REWORK: {label} (session {info['session_id']})",
                  file=sys.stderr)
            print(f"FEEDBACK GAPS: {', '.join(info['feedback'].keys())}",
                  file=sys.stderr)
            print(f"CMD: {cmd[:6]}...", file=sys.stderr)
            print(f"PROMPT:\n{prompt}", file=sys.stderr)
        return [], []

    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = []
    labels = []

    for label, info in sessions_to_resume.items():
        prompt = build_rework_prompt(info['feedback'])
        cmd = build_command(
            change_dir, project_dir,
            SOLVER_SYSTEM_PROMPT, 'opus', budget,
            tools='Read',
            session_id=info['session_id'],
            resume=True,
        )
        tasks.append(run_one_subprocess(
            f"rework:{label}", cmd, prompt, timeout, semaphore,
        ))
        labels.append(label)

    results = await gather_with_callback(tasks, on_complete)

    all_proposals: list[dict] = []
    failures: list[dict] = []
    for i, result in enumerate(results):
        label = labels[i]
        if result['status'] == 'success':
            proposals = result.get('report', [])
            all_proposals.extend(proposals)
            print(f"[REWORK] {label}: {len(proposals)} reworked proposals",
                  file=sys.stderr)
        else:
            failures.append({
                'name': f'rework:{label}',
                'error': result.get('error', 'unknown'),
                'phase': 'rework',
            })
            print(f"[REWORK] {label}: FAILED — {result.get('error', 'unknown')}",
                  file=sys.stderr)

    return all_proposals, failures


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

async def run_initial(
    change_dir: Path,
    groups_json: dict[str, list[str]] | None,
    max_concurrent: int,
    timeout: int,
    budget: float | None,
    dry_run: bool,
    on_complete: callable = None,
) -> dict:
    """Initial run: explore + solve."""
    change_name = change_dir.name
    repo_root = resolve_repo_root(change_dir)
    project_dir = resolve_project_dir(change_dir)
    artifact_files = resolve_artifact_files(change_dir)

    # Find actionable gaps
    actionable = find_actionable_gaps(change_dir)
    if not actionable:
        print("No actionable gaps found.", file=sys.stderr)
        return {'sessions': {}, 'proposals': [], 'failures': []}

    # Build groups: either from --groups JSON or auto-group all into one
    gap_lookup = {g['id']: g for g in actionable}
    groups: dict[str, list[dict]] = {}

    if groups_json:
        for label, gap_ids in groups_json.items():
            group_gaps = [gap_lookup[gid] for gid in gap_ids if gid in gap_lookup]
            if group_gaps:
                groups[label] = group_gaps
    else:
        # Auto-group: all actionable gaps in a single group
        groups['all'] = actionable

    if not groups:
        print("No gaps matched provided groups.", file=sys.stderr)
        return {'sessions': {}, 'proposals': [], 'failures': []}

    total_gaps = sum(len(g) for g in groups.values())
    print(f"\n=== Solving {total_gaps} gaps in {len(groups)} groups ===",
          file=sys.stderr)

    # Phase 1: Explore
    print("\n=== Phase 1: Exploration (Haiku) ===", file=sys.stderr)
    exploration, explore_failures = await run_exploration_phase(
        groups, repo_root, change_dir, project_dir,
        max_concurrent, timeout, budget, dry_run,
        on_complete=on_complete,
    )

    # Phase 2: Solve
    print("\n=== Phase 2: Solution Development (Opus) ===", file=sys.stderr)
    sessions, proposals, solve_failures = await run_solver_phase(
        groups, exploration, change_dir, change_name,
        artifact_files, project_dir,
        max_concurrent, timeout, budget, dry_run,
        on_complete=on_complete,
    )

    return {
        'sessions': sessions,
        'proposals': proposals,
        'failures': explore_failures + solve_failures,
    }


async def run_resume(
    change_dir: Path,
    sessions_json: dict[str, str],
    feedback_json: dict[str, str],
    max_concurrent: int,
    timeout: int,
    budget: float | None,
    dry_run: bool,
    on_complete: callable = None,
) -> dict:
    """Resume run: rework rejected proposals."""
    project_dir = resolve_project_dir(change_dir)

    # Reconstruct groups from actionable gaps + sessions
    actionable = find_actionable_gaps(change_dir)
    gap_lookup = {g['id']: g for g in actionable}

    # We need to figure out which gaps belong to which session.
    # Since we don't store the original grouping, we infer from feedback:
    # each feedback gap must belong to one of the sessions.
    # For resume, we pass groups through so the rework phase can match.
    # Build a single-group mapping (feedback gaps only).
    feedback_gaps = [gap_lookup[gid] for gid in feedback_json if gid in gap_lookup]

    # Create groups matching sessions structure
    groups: dict[str, list[dict]] = {}
    for label in sessions_json:
        groups[label] = feedback_gaps  # rework phase will filter by overlap

    proposals, rework_failures = await run_rework_phase(
        sessions_json, feedback_json, groups,
        change_dir, project_dir,
        max_concurrent, timeout, budget, dry_run,
        on_complete=on_complete,
    )

    return {
        'proposals': proposals,
        'failures': rework_failures,
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

    if args.resume:
        # Resume mode
        if not args.sessions or not args.feedback:
            print("ERROR: --resume requires --sessions and --feedback",
                  file=sys.stderr)
            sys.exit(1)
        sessions_json = json.loads(args.sessions)
        feedback_json = json.loads(args.feedback)
        result = asyncio.run(run_resume(
            change_dir, sessions_json, feedback_json,
            args.max_concurrent, args.timeout, args.budget, args.dry_run,
        ))
    else:
        # Initial mode
        groups_json = json.loads(args.groups) if args.groups else None
        result = asyncio.run(run_initial(
            change_dir, groups_json,
            args.max_concurrent, args.timeout, args.budget, args.dry_run,
        ))

    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
