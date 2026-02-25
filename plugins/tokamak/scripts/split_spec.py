#!/usr/bin/env python3
"""
Section extractor for chaos-theory-lite single-file specs.

Splits a spec.yaml into per-section files under .sections/ for
context-isolated critic evaluation. No-op for multi-file schemas.

Usage:
    python split_spec.py <change_dir>
"""

import sys
from io import StringIO
from pathlib import Path

from ruamel.yaml import YAML


def split_spec(change_dir: Path) -> list[str]:
    """Extract top-level sections from spec.yaml into .sections/ directory.

    Returns list of extracted section filenames, or empty list if no spec.yaml.
    """
    spec_path = change_dir / 'spec.yaml'
    if not spec_path.exists():
        return []

    yaml = YAML()
    yaml.preserve_quotes = True

    with open(spec_path) as f:
        doc = yaml.load(f)

    if not isinstance(doc, dict):
        print(f"WARNING: spec.yaml is not a mapping, skipping extraction",
              file=sys.stderr)
        return []

    sections_dir = change_dir / '.sections'
    sections_dir.mkdir(exist_ok=True)

    extracted = []
    for key in doc:
        section_path = sections_dir / f'{key}.yaml'
        section_doc = {key: doc[key]}

        buf = StringIO()
        yaml.dump(section_doc, buf)

        section_path.write_text(buf.getvalue())
        extracted.append(f'.sections/{key}.yaml')

    return extracted


def main(argv: list[str] | None = None):
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 1:
        print("Usage: split_spec.py <change_dir>", file=sys.stderr)
        sys.exit(1)

    change_dir = Path(argv[0]).resolve()
    if not change_dir.exists():
        print(f"ERROR: Directory not found: {change_dir}", file=sys.stderr)
        sys.exit(1)

    extracted = split_spec(change_dir)
    if extracted:
        print(f"Extracted {len(extracted)} sections:", file=sys.stderr)
        for f in extracted:
            print(f"  {f}", file=sys.stderr)
    else:
        print("No spec.yaml found, nothing to extract", file=sys.stderr)


if __name__ == '__main__':
    main()
