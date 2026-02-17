#!/usr/bin/env python3
"""
Critic selector for OpenSpec workflow.
Selects critics to run based on file existence and content changes.

Usage:
    python select_critics.py <change_dir> [--force] [--dry-run] [--list] [--scope single|cross]
    python select_critics.py <change_dir> --update-hashes

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


def compute_directory_hash(change_dir: Path, dir_path: Path) -> str | None:
    """Compute combined hash of all files in a directory (sorted, recursive)."""
    files = sorted(f for f in dir_path.rglob('*') if f.is_file())
    if not files:
        return None

    hasher = hashlib.sha256()
    for filepath in files:
        hasher.update(str(filepath.relative_to(change_dir)).encode())
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
    return hasher.hexdigest()[:16]


def get_current_state(change_dir: Path, file_keys: list[str]) -> dict:
    """Get current file existence and hashes."""
    state = {'exists': {}, 'hashes': {}}

    for key in file_keys:
        filepath = change_dir / key
        if filepath.is_dir():
            files_in_dir = sorted(f for f in filepath.rglob('*') if f.is_file())
            state['exists'][key] = len(files_in_dir) > 0
            if files_in_dir:
                state['hashes'][key] = compute_directory_hash(change_dir, filepath)
        else:
            exists = filepath.exists()
            state['exists'][key] = exists
            if exists:
                state['hashes'][key] = compute_file_hash(filepath)

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


def resolve_templates(files: list[str], templates_dir: Path | None) -> dict[str, str]:
    """Map a critic's file list to matching schema template content.

    Lookup strategy per file entry:
      1. Exact match: templates_dir/<filename>
      2. Fallback: templates_dir/<filename>.feature.md (for directory entries like 'requirements')
    """
    if not templates_dir or not templates_dir.is_dir():
        return {}
    templates = {}
    for f in files:
        path = templates_dir / f
        if path.is_file():
            templates[f] = path.read_text()
            continue
        fallback = templates_dir / (f + '.feature.md')
        if fallback.is_file():
            templates[f] = fallback.read_text()
    return templates


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
    parser.add_argument('--update-hashes', action='store_true',
                        help='Save current file hashes and exit (no critic selection)')
    parser.add_argument('--scope', choices=['single', 'cross'],
                        help='Filter by critic scope: single (1 file) or cross (2+ files)')
    args = parser.parse_args()

    # Mutual exclusion: --update-hashes cannot combine with selection flags
    if args.update_hashes and (args.force or args.list or args.scope):
        parser.error('--update-hashes cannot be combined with --force, --list, or --scope')

    change_dir = args.change_dir.resolve()
    script_dir = Path(__file__).parent.resolve()
    plugin_root = script_dir.parent

    # Read .openspec.yaml for schema name and project path
    project_path = None
    schema_name = None
    openspec_path = change_dir / '.openspec.yaml'
    if args.config:
        config_path = args.config
    else:
        config_path = change_dir / '.critique.json'

    if openspec_path.exists():
        import re
        with open(openspec_path) as f:
            for line in f:
                m = re.match(r'^schema:\s*(.+)', line)
                if m:
                    schema_name = m.group(1).strip()
                    if not args.config:
                        schema_config = plugin_root / f'critics.{schema_name}.json'
                        if schema_config.exists():
                            config_path = schema_config
                m = re.match(r'^project:\s*(.+)', line)
                if m:
                    project_path = m.group(1).strip()

    # Resolve templates directory from schema name
    openspec_root = change_dir.parent.parent  # openspec/changes/<name>/ → openspec/
    templates_dir = (
        openspec_root / 'schemas' / schema_name / 'templates'
        if schema_name else None
    )

    # Resolve project directory from project path (bare name under openspec/)
    project_dir = (openspec_root / project_path).resolve() if project_path else None
    if project_dir and not project_dir.exists():
        print(f"INFO: Project directory {project_dir} does not exist yet. Project files skipped.", file=sys.stderr)
        project_dir = None

    default_path = plugin_root / 'critics.chaos-theory.json'

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

    # Derive tracked file keys from all critics' files arrays
    file_keys = sorted({f for critic in config['critics'] for f in critic.get('files', [])})

    # Derive project file keys from critics with project_files
    project_file_keys = sorted({f for critic in config['critics'] for f in critic.get('project_files', [])})

    hash_path = change_dir / '.hashes.json'

    # Error: Hash file corrupted
    try:
        stored_hashes = load_hashes(hash_path)
    except json.JSONDecodeError:
        print(f"WARNING: Corrupted hash file {hash_path}, treating all files as changed.", file=sys.stderr)
        stored_hashes = {}

    current_state = get_current_state(change_dir, file_keys)
    current_hashes = current_state['hashes']

    # Track project file hashes under "project:" prefix to avoid collision
    project_state = {'exists': {}, 'hashes': {}}
    if project_dir and project_file_keys:
        raw_project_state = get_current_state(project_dir, project_file_keys)
        for key in project_file_keys:
            prefixed = f'project:{key}'
            project_state['exists'][prefixed] = raw_project_state['exists'].get(key, False)
            if key in raw_project_state['hashes']:
                project_state['hashes'][prefixed] = raw_project_state['hashes'][key]
                current_hashes[prefixed] = raw_project_state['hashes'][key]

    # --update-hashes: save current hashes (including project hashes) and exit
    if args.update_hashes:
        try:
            save_hashes(hash_path, current_hashes)
            print(f"Hashes saved to {hash_path}", file=sys.stderr)
        except PermissionError:
            print(f"ERROR: Cannot write hash file {hash_path}", file=sys.stderr)
            sys.exit(1)
        return

    selected = []
    for critic in config['critics']:
        name = critic.get('name', '<unnamed>')
        files = critic.get('files', [])

        # Skip requires_project critics when project dir is unavailable
        if critic.get('requires_project', False) and project_dir is None:
            log_selection(name, False, "project docs not available")
            continue

        # Check file existence
        missing = [f for f in files if not current_state['exists'].get(f, False)]
        if missing:
            log_selection(name, False, f"missing files: {', '.join(missing)}")
            continue

        # Build combined tracked keys (change files + prefixed project files)
        project_files = critic.get('project_files', [])
        prefixed_project_files = [f'project:{pf}' for pf in project_files]
        all_tracked = files + prefixed_project_files

        # Check for changes
        if args.force:
            log_selection(name, True, "forced")
            selected.append(critic)
        elif any_hash_changed(all_tracked, current_hashes, stored_hashes):
            changed = [f for f in all_tracked if current_hashes.get(f) != stored_hashes.get(f)]
            log_selection(name, True, f"changed: {', '.join(changed)}")
            selected.append(critic)
        else:
            log_selection(name, False, "no changes detected")

    # Apply scope filter
    if args.scope == 'single':
        selected = [c for c in selected if len(c.get('files', [])) == 1]
    elif args.scope == 'cross':
        selected = [c for c in selected if len(c.get('files', [])) >= 2]

    # Summary
    print(f"--- {len(selected)}/{len(config['critics'])} critics selected ---", file=sys.stderr)

    output = []
    for c in selected:
        expanded_files = []
        for f in c['files']:
            dir_path = change_dir / f
            if dir_path.is_dir():
                expanded_files.extend(
                    sorted(str(p.relative_to(change_dir)) for p in dir_path.rglob('*') if p.is_file())
                )
            else:
                expanded_files.append(f)
        # Expand project files against project_dir
        expanded_project_files = []
        if project_dir and c.get('project_files'):
            for f in c['project_files']:
                pf_path = project_dir / f
                if pf_path.is_dir():
                    expanded_project_files.extend(
                        sorted(str(p.relative_to(project_dir)) for p in pf_path.rglob('*') if p.is_file())
                    )
                elif pf_path.exists():
                    expanded_project_files.append(f)
        output.append({
            'name': c['name'],
            'model': c['model'],
            'files': expanded_files,
            'project_files': expanded_project_files,
            'skills': c.get('skills', []),
            'evaluate': c['evaluate'],
            'templates': resolve_templates(c.get('files', []), templates_dir),
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
