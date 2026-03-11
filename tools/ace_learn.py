#!/usr/bin/env python3
"""Offline ACE learning tool for tokamak critic skillbooks.

Reads per-critic results from .critique-results.json and evolves
skillbook files via ACE's Reflector + SkillManager pipeline.

Requires: pip install -e ".[ace]"

Usage:
    python tools/ace_learn.py openspec/changes/my-change
    python tools/ace_learn.py openspec/changes/my-change --model opus
    python tools/ace_learn.py openspec/changes/my-change --dry-run
    python tools/ace_learn.py openspec/changes/my-change --propagate

Cross-repo usage (learn from another product's critique results):
    python tools/ace_learn.py /tmp/collected/feature-x \\
        --repo-root /path/to/other-product \\
        --change-path openspec/changes/feature-x
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    from ace import AgentOutput, Reflector, Skillbook, SkillManager
    from ace.llm_providers import ClaudeCodeLLMClient
except ImportError:
    print(
        "ERROR: ace-framework not installed.\n"
        "Install with: pip install -e '.[ace]'\n",
        file=sys.stderr,
    )
    sys.exit(1)

ACE_DIR = Path(__file__).resolve().parent.parent / 'plugins' / 'tokamak' / '.ace'


def _slugify(name: str) -> str:
    """'Requirements Coverage' -> 'requirements-coverage'."""
    return name.lower().replace(' ', '-')


def _git_show(commit: str, filepath: str, cwd: str) -> str:
    """Read a file at a specific commit via git show."""
    try:
        result = subprocess.run(
            ['git', 'show', f'{commit}:{filepath}'],
            capture_output=True, text=True, check=True, cwd=cwd,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return ''


def _evaluate_quality(
    change_dir: Path, run_data: dict, llm,
    repo_root: Path | None = None,
    change_path: str | None = None,
) -> dict[str, str]:
    """Evaluate per-critic finding quality using LLM + spec context.

    Returns {critic_name: quality_context_string}.
    Uses commit hash from run_data to reconstruct specs at critique time.

    For cross-repo use, pass repo_root to point git commands at the
    source repo, and change_path for the relative path within it.
    """
    commit = run_data.get('commit', '')
    if not commit:
        return {}

    git_cwd = str(repo_root) if repo_root else str(change_dir)

    if change_path:
        rel_dir = change_path
    else:
        try:
            toplevel = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                capture_output=True, text=True, check=True, cwd=git_cwd,
            ).stdout.strip()
            rel_dir = str(change_dir.relative_to(toplevel))
        except (subprocess.CalledProcessError, ValueError, OSError):
            return {}

    # Reconstruct spec files at critique time
    spec_files = ['functional.md', 'technical.md', 'infra.md', 'gaps.md']
    specs_content = ''
    for sf in spec_files:
        content = _git_show(commit, f'{rel_dir}/{sf}', git_cwd)
        if content:
            specs_content += f'\n## {sf}\n{content[:3000]}\n'

    quality = {}
    for r in run_data.get('results', []):
        if r.get('status') != 'success' or not r.get('output', '').strip():
            continue

        name = r['name']
        output = r['output']

        # Load critic's evaluation criteria from skillbook
        schema = run_data.get('schema', 'chaos-theory')
        config_type = run_data.get('config_type', 'critics')
        kind = 'gap-detectors' if 'gap-detector' in config_type else 'critics'
        slug = _slugify(name)
        sb_path = ACE_DIR / kind / schema / f'{slug}.json'
        criteria = ''
        if sb_path.exists():
            with open(sb_path) as f:
                sb_data = json.load(f)
            skills = sb_data.get('skills', {})
            if isinstance(skills, dict):
                criteria = '\n\n'.join(
                    s['content'] for s in skills.values()
                    if isinstance(s, dict) and 'content' in s
                )
            else:
                criteria = '\n\n'.join(s['content'] for s in skills if 'content' in s)

        # Rate findings via LLM
        prompt = (
            f"Given these specification artifacts:\n{specs_content[:4000]}\n\n"
            f"And this critic's evaluation criteria:\n{criteria[:2000]}\n\n"
            f"Rate the overall quality of these findings:\n{output[:3000]}\n\n"
            f"For each finding, classify as: useful, noise, vague, or out-of-scope.\n"
            f"Then summarize: N useful, N noise, N vague, N out-of-scope.\n"
            f"End with: Effectiveness: X/Y (Z%)"
        )
        try:
            response = llm.generate(prompt)
            quality[name] = response.strip()
        except Exception as e:
            print(f"  WARNING: Quality eval failed for {name}: {e}", file=sys.stderr)
            quality[name] = ''

    return quality


def learn(
    change_dir: Path, model: str = 'sonnet', dry_run: bool = False,
    repo_root: Path | None = None, change_path: str | None = None,
):
    """Run ACE learning on the latest critique results."""
    results_path = change_dir / '.critique-results.json'
    if not results_path.exists():
        print(f"No .critique-results.json in {change_dir}", file=sys.stderr)
        sys.exit(1)

    with open(results_path) as f:
        runs = json.load(f)

    if not runs:
        print("No critique runs found", file=sys.stderr)
        sys.exit(1)

    data = runs[-1]
    print(f"Learning from run: {data['timestamp']} ({data['config_type']}/{data['schema']})")

    llm = ClaudeCodeLLMClient(model=model)
    reflector = Reflector(llm)
    skill_manager = SkillManager(llm)

    config_type = data['config_type']
    schema = data['schema']
    results = data['results']
    successes = [r for r in results if r['status'] == 'success']
    kind = 'gap-detectors' if 'gap-detector' in config_type else 'critics'

    if not successes:
        print("No successful critic results to learn from", file=sys.stderr)
        sys.exit(1)

    # Evaluate finding quality
    if repo_root:
        print(f"Using repo root: {repo_root}")
        if change_path:
            print(f"Change path in repo: {change_path}")
    print("Evaluating finding quality...")
    quality = _evaluate_quality(change_dir, data, llm, repo_root, change_path)

    # Individual learning per critic
    print(f"\nLearning from {len(successes)} critic(s):")
    for r in successes:
        slug = _slugify(r['name'])
        sb_path = ACE_DIR / kind / schema / f'{slug}.json'

        if not sb_path.exists():
            print(f"  {r['name']}: SKIP (no skillbook at {sb_path})", file=sys.stderr)
            continue

        sb = Skillbook.load_from_file(str(sb_path))

        quality_context = quality.get(r['name'], '')
        agent_output = AgentOutput(
            reasoning=quality_context,
            final_answer=r['output'],
            skill_ids=[],
            raw=r['output'],
        )
        reflection = reflector.reflect(
            question=f"Critic '{r['name']}' evaluation results",
            agent_output=agent_output,
            skillbook=sb,
        )
        sm_output = skill_manager.update_skills(
            reflection=reflection,
            skillbook=sb,
            question_context=f"Critic: {r['name']}",
            progress="",
        )

        if dry_run:
            actions = ', '.join(u.action for u in sm_output.updates) if sm_output.updates else 'none'
            print(f"  {r['name']}: {len(sm_output.updates)} proposed ({actions})")
        else:
            sb.apply_update(sm_output.updates)
            sb.save_to_file(str(sb_path))
            skills = sb.skills if hasattr(sb, 'skills') else []
            print(f"  {r['name']}: {len(sm_output.updates)} updates ({len(skills)} skills)")

    # Team learning
    print("\nTeam learning:")
    combined = "\n\n".join([
        f"## {r['name']}\n{r['output'][:2000]}"
        for r in successes
    ])
    team_path = ACE_DIR / 'team' / 'critique.json'
    if team_path.exists():
        team_sb = Skillbook.load_from_file(str(team_path))
    else:
        team_sb = Skillbook()

    agent_output = AgentOutput(
        reasoning="",
        final_answer=combined,
        skill_ids=[],
        raw=combined,
    )
    reflection = reflector.reflect(
        question="How did these parallel critics perform as a team? "
                 "What gaps exist in coverage? What duplication occurred?",
        agent_output=agent_output,
        skillbook=team_sb,
    )
    sm_output = skill_manager.update_skills(
        reflection=reflection,
        skillbook=team_sb,
        question_context="Critic team coordination",
        progress="",
    )

    if dry_run:
        actions = ', '.join(u.action for u in sm_output.updates) if sm_output.updates else 'none'
        print(f"  Team: {len(sm_output.updates)} proposed ({actions})")
    else:
        team_sb.apply_update(sm_output.updates)
        team_sb.save_to_file(str(team_path))
        print(f"  Team: {len(sm_output.updates)} updates")

    if dry_run:
        print(f"\nDry run complete. No files modified.")
    else:
        print(f"\nDone. Review changes: git diff plugins/tokamak/.ace/")


def propagate(source_schema: str):
    """Copy learned (non-seed) skills from source schema to all other schemas.

    Operates on raw JSON to avoid dependency on internal ACE Update types.
    Only copies skills that were added by ACE learning (not the original
    migrated seed content). Seed skills have id 'eval-criteria-1'.
    """
    schemas = ['chaos-theory', 'chaos-theory-lite', 'chaos-theory-brownfield',
               'chaos-theory-greenfield']

    print(f"\nPropagating from {source_schema}:")
    for kind in ('critics', 'gap-detectors'):
        source_dir = ACE_DIR / kind / source_schema
        if not source_dir.exists():
            continue

        for sb_file in source_dir.glob('*.json'):
            with open(sb_file) as f:
                source_data = json.load(f)

            # Find learned (non-seed) skills — seed has id 'eval-criteria-1'
            source_skills = source_data.get('skills', {})
            learned = {
                sid: s for sid, s in source_skills.items()
                if isinstance(s, dict) and sid != 'eval-criteria-1'
            }
            if not learned:
                continue

            for target_schema in schemas:
                if target_schema == source_schema:
                    continue
                target_path = ACE_DIR / kind / target_schema / sb_file.name
                if not target_path.exists():
                    continue

                with open(target_path) as f:
                    target_data = json.load(f)

                existing_ids = set(target_data.get('skills', {}).keys())
                added = 0
                for sid, skill in learned.items():
                    if sid not in existing_ids:
                        target_data['skills'][sid] = skill
                        added += 1

                if added:
                    with open(target_path, 'w') as f:
                        json.dump(target_data, f, indent=2)
                        f.write('\n')
                    print(f"  {kind}/{target_schema}/{sb_file.name}: +{added} skills")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ACE learning for tokamak critics')
    parser.add_argument('change_dir', type=Path)
    parser.add_argument('--model', default='sonnet',
                        help='LLM model for reflection (default: sonnet)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show proposed changes without applying')
    parser.add_argument('--propagate', action='store_true',
                        help='Copy learned skills across schemas for matching critics')
    parser.add_argument('--repo-root', type=Path, default=None,
                        help='Git repo root for cross-repo quality evaluation '
                             '(default: auto-detect from change_dir)')
    parser.add_argument('--change-path', default=None,
                        help='Relative path of the change dir within --repo-root '
                             '(required when change_dir is outside the target repo)')
    args = parser.parse_args()

    repo_root = args.repo_root.resolve() if args.repo_root else None
    learn(args.change_dir.resolve(), args.model, args.dry_run,
          repo_root, args.change_path)

    if args.propagate and not args.dry_run:
        results_path = args.change_dir.resolve() / '.critique-results.json'
        with open(results_path) as f:
            runs = json.load(f)
        if runs:
            propagate(source_schema=runs[-1]['schema'])
