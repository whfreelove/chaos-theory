#!/usr/bin/env python3
"""One-time migration: extract `evaluate` fields from critic/gap-detector configs
into per-schema skillbook files under plugins/tokamak/.ace/.

Creates ACE-compatible skillbook JSON directly (no ace-framework dependency).
After creating all skillbooks, removes `evaluate` from the config JSONs.

Usage:
    python tools/migrate_evaluate_to_skillbooks.py
    python tools/migrate_evaluate_to_skillbooks.py --dry-run
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parent.parent / 'plugins' / 'tokamak'
ACE_DIR = PLUGIN_ROOT / '.ace'

# Config files: (kind, filename)
CONFIG_FILES = []
for kind in ('critics', 'gap-detectors'):
    for schema in ('chaos-theory', 'chaos-theory-lite', 'chaos-theory-brownfield',
                    'chaos-theory-greenfield'):
        path = PLUGIN_ROOT / f'{kind}.{schema}.json'
        if path.exists():
            CONFIG_FILES.append((kind, schema, path))


def slugify(name: str) -> str:
    """Convert critic name to filesystem slug: 'Requirements Coverage' -> 'requirements-coverage'."""
    return name.lower().replace(' ', '-')


def make_skillbook(evaluate_text: str, critic_name: str, config_filename: str) -> dict:
    """Construct a skillbook JSON matching ACE's Skillbook.from_dict() format."""
    now = datetime.now(timezone.utc).isoformat()
    skill_id = 'eval-criteria-1'
    return {
        'skills': {
            skill_id: {
                'id': skill_id,
                'section': 'evaluation-criteria',
                'content': evaluate_text,
                'helpful': 0, 'harmful': 0, 'neutral': 0,
                'created_at': now, 'updated_at': now,
                'embedding': None, 'status': 'active',
                'justification': None, 'evidence': None,
                'sources': [],
            }
        },
        'sections': {'evaluation-criteria': [skill_id]},
        'next_id': 1,
        'metadata': {
            'version': '0.1.0',
            'mutations': [],
            'source': f'migrated from {config_filename}',
            'critic': critic_name,
        },
    }


def migrate(dry_run: bool = False) -> None:
    created = []
    modified = []

    # Phase 1: Read all configs and create skillbooks
    for kind, schema, config_path in CONFIG_FILES:
        with open(config_path) as f:
            config = json.load(f)

        # Determine ACE subdirectory kind
        ace_kind = 'gap-detectors' if kind == 'gap-detectors' else 'critics'
        schema_dir = ACE_DIR / ace_kind / schema

        for critic in config.get('critics', []):
            name = critic.get('name', '')
            evaluate = critic.get('evaluate')
            if not evaluate:
                print(f"  SKIP: {name} in {config_path.name} (no evaluate field)",
                      file=sys.stderr)
                continue

            slug = slugify(name)
            sb_path = schema_dir / f'{slug}.json'
            sb_data = make_skillbook(evaluate, name, config_path.name)

            if dry_run:
                print(f"  WOULD CREATE: {sb_path.relative_to(PLUGIN_ROOT)}")
            else:
                sb_path.parent.mkdir(parents=True, exist_ok=True)
                with open(sb_path, 'w') as f:
                    json.dump(sb_data, f, indent=2)
                    f.write('\n')

            created.append(sb_path)

    # Phase 2: Create empty team skillbook
    team_path = ACE_DIR / 'team' / 'critique.json'
    team_data = {
        'skills': {},
        'sections': {},
        'next_id': 0,
        'metadata': {'version': '0.1.0', 'mutations': []},
    }
    if dry_run:
        print(f"  WOULD CREATE: {team_path.relative_to(PLUGIN_ROOT)}")
    else:
        team_path.parent.mkdir(parents=True, exist_ok=True)
        with open(team_path, 'w') as f:
            json.dump(team_data, f, indent=2)
            f.write('\n')
    created.append(team_path)

    # Phase 3: Remove evaluate from all configs
    for kind, schema, config_path in CONFIG_FILES:
        with open(config_path) as f:
            config = json.load(f)

        changed = False
        for critic in config.get('critics', []):
            if 'evaluate' in critic:
                if not dry_run:
                    del critic['evaluate']
                changed = True

        if changed:
            if dry_run:
                count = sum(1 for c in config.get('critics', []) if 'evaluate' in c)
                print(f"  WOULD MODIFY: {config_path.name} (remove evaluate from {count} entries)")
            else:
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                    f.write('\n')
            modified.append(config_path)

    # Summary
    print(f"\n{'DRY RUN - ' if dry_run else ''}Migration summary:")
    print(f"  Skillbook files created: {len(created)}")
    print(f"  Config files modified: {len(modified)}")

    if not dry_run:
        print(f"\nVerify: grep -r '\"evaluate\"' plugins/tokamak/critics.*.json plugins/tokamak/gap-detectors.*.json")
        print(f"Review: ls -la plugins/tokamak/.ace/critics/ plugins/tokamak/.ace/gap-detectors/")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Migrate evaluate fields to skillbook files')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be created/modified without making changes')
    args = parser.parse_args()
    migrate(dry_run=args.dry_run)
