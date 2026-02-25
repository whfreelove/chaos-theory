#!/usr/bin/env python3
"""List spec-writing skills needed for a change's artifact types.

Usage: python list_skills.py <change_dir>

Outputs deduplicated Skill() invocations for artifacts that exist in the
change directory, so the orchestrating agent can load domain vocabulary
before developing solutions.
"""

import sys
from pathlib import Path

from spec_utils import load_schema_artifacts, lookup_artifact


def list_skills(change_dir: Path) -> list[tuple[str, list[str]]]:
    """Return (skill_name, [artifact_filenames]) pairs for existing artifacts."""
    artifacts = load_schema_artifacts(change_dir)
    if not artifacts:
        return []

    # Collect actual artifact files in the change directory
    artifact_files: list[str] = []
    for p in sorted(change_dir.rglob('*')):
        if not p.is_file():
            continue
        rel = str(p.relative_to(change_dir))
        # Skip non-artifact files
        if rel.startswith('.') or rel in ('gaps.md', 'resolved.md', 'findings.json'):
            continue
        artifact_files.append(rel)

    # Map skills to the artifact filenames that reference them
    skill_files: dict[str, list[str]] = {}
    for filename in artifact_files:
        config = lookup_artifact(artifacts, filename)
        if config:
            for skill in config['skills']:
                skill_files.setdefault(skill, []).append(filename)

    return list(skill_files.items())


def main():
    if len(sys.argv) < 2:
        print('Usage: list_skills.py <change_dir>', file=sys.stderr)
        sys.exit(1)

    change_dir = Path(sys.argv[1])
    if not change_dir.is_absolute():
        change_dir = Path.cwd() / change_dir

    if not change_dir.exists():
        print(f'Change directory not found: {change_dir}', file=sys.stderr)
        sys.exit(1)

    skills = list_skills(change_dir)
    if not skills:
        print('No spec-writing skills found for this change.')
        return

    for skill_name, filenames in skills:
        label = ', '.join(filenames)
        print(f'- Skill({skill_name}) — for {label}')


if __name__ == '__main__':
    main()
