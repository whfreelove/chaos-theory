#!/usr/bin/env python3
"""
Critic selector for OpenSpec workflow.
Selects critics to run based on file existence and content changes.

Usage:
    python select_critics.py <change_dir> [--force] [--dry-run] [--list]

Output:
    JSON array of critic definitions to stdout
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()[:16]


def compute_requirements_hash(change_dir: Path) -> str | None:
    """Compute combined hash of all requirements/*/requirements.feature.md files."""
    requirements_dir = change_dir / 'requirements'
    if not requirements_dir.exists():
        return None

    requirements_files = sorted(requirements_dir.glob('*/requirements.feature.md'))
    if not requirements_files:
        return None

    hasher = hashlib.sha256()
    for requirements_file in requirements_files:
        hasher.update(str(requirements_file.relative_to(change_dir)).encode())
        with open(requirements_file, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
    return hasher.hexdigest()[:16]


def get_current_state(change_dir: Path) -> dict:
    """Get current file existence and hashes."""
    state = {'exists': {}, 'hashes': {}}

    for filename in ['functional.md', 'technical.md', 'tasks.yaml']:
        filepath = change_dir / filename
        exists = filepath.exists()
        state['exists'][filename] = exists
        if exists:
            state['hashes'][filename] = compute_file_hash(filepath)

    requirements_dir = change_dir / 'requirements'
    requirements_files = list(requirements_dir.glob('*/requirements.feature.md')) if requirements_dir.exists() else []
    state['exists']['requirements'] = len(requirements_files) > 0
    if requirements_files:
        state['hashes']['requirements'] = compute_requirements_hash(change_dir)

    return state


def files_exist(state: dict, file_keys: list[str]) -> bool:
    """Check if all required files exist."""
    return all(state['exists'].get(key, False) for key in file_keys)


def any_hash_changed(file_keys: list[str], current_hashes: dict, stored_hashes: dict) -> bool:
    """Check if any required file has changed (or is new)."""
    for key in file_keys:
        current = current_hashes.get(key)
        stored = stored_hashes.get(key)
        if current and current != stored:
            return True
    return False


def load_config(config_path: Path, default_path: Path | None = None) -> dict:
    """Load config file, falling back to default if not found."""
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    if default_path and default_path.exists():
        with open(default_path) as f:
            return json.load(f)
    return {'critics': []}


def load_hashes(hash_path: Path) -> dict:
    """Load hashes from separate file."""
    if hash_path.exists():
        with open(hash_path) as f:
            return json.load(f)
    return {}


def save_hashes(hash_path: Path, hashes: dict):
    """Save hashes to separate file."""
    with open(hash_path, 'w') as f:
        json.dump(hashes, f, indent=2)
        f.write('\n')


def log_selection(name: str, selected: bool, reason: str):
    """Log critic selection status to stderr."""
    status = "SELECTED" if selected else "SKIPPED"
    print(f"[{status}] {name}: {reason}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description='Select critics to run based on file changes'
    )
    parser.add_argument('change_dir', type=Path,
                        help='Path to OpenSpec change directory')
    parser.add_argument('--config', type=Path, default=None,
                        help='Config file path (default: <change_dir>/.critique.json)')
    parser.add_argument('--force', action='store_true',
                        help='Select all critics regardless of hash changes')
    parser.add_argument('--dry-run', action='store_true',
                        help='Do not update stored hashes')
    parser.add_argument('--list', action='store_true',
                        help='List critic names only')
    args = parser.parse_args()

    change_dir = args.change_dir.resolve()
    config_path = args.config or (change_dir / '.critique.json')
    script_dir = Path(__file__).parent.resolve()
    default_path = script_dir.parent / 'default-critique.json'

    # Error: Directory not found
    if not change_dir.exists():
        print(f"ERROR: Change directory not found: {change_dir}", file=sys.stderr)
        print(f"FIX: Verify the path exists. Expected an OpenSpec change directory.", file=sys.stderr)
        sys.exit(1)

    # Error: Config loading failed
    try:
        config = load_config(config_path, default_path)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in config file: {config_path}", file=sys.stderr)
        print(f"FIX: Check syntax at line {e.lineno}, column {e.colno}: {e.msg}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"ERROR: Cannot read config file: {config_path}", file=sys.stderr)
        print(f"FIX: Check file permissions.", file=sys.stderr)
        sys.exit(1)

    # Error: No critics configured
    if not config.get('critics'):
        print(f"ERROR: No critics defined in config.", file=sys.stderr)
        print(f"FIX: Add a 'critics' array to {config_path} or {default_path}", file=sys.stderr)
        sys.exit(1)

    hash_path = change_dir / '.hashes.json'

    # Error: Hash file corrupted
    try:
        stored_hashes = load_hashes(hash_path)
    except json.JSONDecodeError:
        print(f"WARNING: Corrupted hash file {hash_path}, treating all files as changed.", file=sys.stderr)
        stored_hashes = {}

    current_state = get_current_state(change_dir)
    current_hashes = current_state['hashes']

    selected = []
    for critic in config['critics']:
        name = critic.get('name', '<unnamed>')
        files = critic.get('files', [])

        # Check file existence
        missing = [f for f in files if not current_state['exists'].get(f, False)]
        if missing:
            log_selection(name, False, f"missing files: {', '.join(missing)}")
            continue

        # Check for changes
        if args.force:
            log_selection(name, True, "forced")
            selected.append(critic)
        elif any_hash_changed(files, current_hashes, stored_hashes):
            changed = [f for f in files if current_hashes.get(f) != stored_hashes.get(f)]
            log_selection(name, True, f"changed: {', '.join(changed)}")
            selected.append(critic)
        else:
            log_selection(name, False, "no changes detected")

    # Summary
    print(f"--- {len(selected)}/{len(config['critics'])} critics selected ---", file=sys.stderr)

    if not args.dry_run and selected:
        try:
            save_hashes(hash_path, current_hashes)
        except PermissionError:
            print(f"WARNING: Cannot write hash file {hash_path}. Hashes not saved.", file=sys.stderr)

    output = []
    for c in selected:
        files = ['requirements/*/requirements.feature.md' if f == 'requirements' else f for f in c['files']]
        output.append({
            'name': c['name'],
            'model': c['model'],
            'files': files,
            'skills': c.get('skills', []),
            'evaluate': c['evaluate']
        })

    if args.list:
        print(json.dumps([c['name'] for c in selected]))
    else:
        result = {
            'output_template': config.get('output_template', ''),
            'critics': output
        }
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
