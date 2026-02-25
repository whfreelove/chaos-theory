#!/usr/bin/env python3
"""
Schema-agnostic artifact resolver for OpenSpec workflows.

Resolves artifact files from a schema definition, enabling workflow skills
(resolve-gaps, ratify-specs) to work across any schema.

Usage:
    python resolve_artifacts.py <change_dir>

Output (JSON to stdout):
    {
      "schema": "chaos-theory-lite",
      "files": ["spec.yaml"],
      "artifacts": [
        {"id": "spec", "files": ["spec.yaml"], "instruction": "..."}
      ],
      "has_tasks": true
    }
"""

import glob as globmod
import json
import re
import sys
from pathlib import Path

from ruamel.yaml import YAML


def read_openspec_field(change_dir: Path, field: str) -> str | None:
    """Read a field value from .openspec.yaml using line-level parsing."""
    openspec_path = change_dir / '.openspec.yaml'
    if not openspec_path.exists():
        return None
    with open(openspec_path) as f:
        for line in f:
            m = re.match(rf'^{re.escape(field)}:\s*(.+)', line)
            if m:
                return m.group(1).strip()
    return None


def resolve_artifacts(change_dir: Path) -> dict:
    """Resolve artifact files from schema definition.

    Returns dict with schema name, resolved files, artifact details,
    and whether the schema has a tasks artifact with content.
    """
    change_dir = change_dir.resolve()

    # Read schema name from .openspec.yaml
    schema_name = read_openspec_field(change_dir, 'schema')
    if not schema_name:
        print("ERROR: No schema field in .openspec.yaml", file=sys.stderr)
        sys.exit(1)

    # Locate schema.yaml
    openspec_root = change_dir.parent.parent  # openspec/changes/<name>/ → openspec/
    schema_path = openspec_root / 'schemas' / schema_name / 'schema.yaml'
    if not schema_path.exists():
        print(f"ERROR: Schema not found: {schema_path}", file=sys.stderr)
        sys.exit(1)

    yaml = YAML()
    with open(schema_path) as f:
        schema = yaml.load(f)

    all_files = []
    artifacts = []
    has_tasks = False

    for artifact in schema.get('artifacts', []):
        artifact_id = artifact['id']
        generates = artifact['generates']

        # Glob-resolve the generates pattern against change_dir
        pattern = str(change_dir / generates)
        matched = sorted(globmod.glob(pattern, recursive=True))
        resolved_files = [
            str(Path(m).relative_to(change_dir)) for m in matched
            if Path(m).is_file()
        ]

        all_files.extend(resolved_files)
        artifacts.append({
            'id': artifact_id,
            'files': resolved_files,
            'instruction': artifact.get('instruction', ''),
        })

        # Check if tasks artifact has content
        if artifact_id == 'tasks':
            for f in resolved_files:
                fpath = change_dir / f
                if fpath.exists():
                    content = fpath.read_text().strip()
                    # Strip comment-only lines
                    non_comment = [
                        line for line in content.splitlines()
                        if line.strip() and not line.strip().startswith('#')
                    ]
                    if non_comment:
                        has_tasks = True
                        break

    return {
        'schema': schema_name,
        'files': all_files,
        'artifacts': artifacts,
        'has_tasks': has_tasks,
    }


def main(argv: list[str] | None = None):
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 1:
        print("Usage: resolve_artifacts.py <change_dir>", file=sys.stderr)
        sys.exit(1)

    change_dir = Path(argv[0]).resolve()
    if not change_dir.exists():
        print(f"ERROR: Directory not found: {change_dir}", file=sys.stderr)
        sys.exit(1)

    result = resolve_artifacts(change_dir)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
