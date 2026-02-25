#!/usr/bin/env python3
"""
Group gaps by primary file for per-file parallel resolution.

Reads gaps.md, extracts Primary-file annotations from triaged gaps with
decisions, and outputs a JSON grouping.

Usage:
    python group_gaps.py <change_dir>

Output (JSON to stdout):
    {
      "groups": {
        "functional.md": ["GAP-197", "GAP-198"],
        "tasks.yaml": ["GAP-193", "GAP-194"]
      },
      "gap_lifecycle": ["GAP-186"],
      "ungrouped": []
    }

Gaps must have Triage, Decision, AND Primary-file fields to be grouped.
Gaps triaged as defer-resolution are skipped (no file assignment needed).
"""

import json
import sys
from pathlib import Path

from spec_utils import parse_gaps


def group_gaps(change_dir: Path) -> dict:
    """Group gaps by primary file assignment.

    Returns dict with groups (file -> gap IDs), gap_lifecycle, and ungrouped.
    """
    gaps_path = change_dir / 'gaps.md'
    if not gaps_path.exists():
        print(f"ERROR: gaps.md not found in {change_dir}", file=sys.stderr)
        sys.exit(1)

    content = gaps_path.read_text()
    all_gaps = parse_gaps(content)

    groups: dict[str, list[str]] = {}
    gap_lifecycle: list[str] = []
    ungrouped: list[str] = []

    for gap in all_gaps:
        # Skip gaps without triage or decision (not yet processed by Section E)
        if not gap['triage'] or not gap['decision']:
            continue

        # Skip defer-resolution gaps (no file assignment needed)
        if gap['triage'] == 'defer-resolution':
            continue

        primary_file = gap['primary_file']

        if not primary_file:
            ungrouped.append(gap['id'])
        elif primary_file == 'gap-lifecycle':
            gap_lifecycle.append(gap['id'])
        else:
            groups.setdefault(primary_file, []).append(gap['id'])

    return {
        'groups': groups,
        'gap_lifecycle': gap_lifecycle,
        'ungrouped': ungrouped,
    }


def main(argv: list[str] | None = None):
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 1:
        print("Usage: group_gaps.py <change_dir>", file=sys.stderr)
        sys.exit(1)

    change_dir = Path(argv[0]).resolve()
    if not change_dir.exists():
        print(f"ERROR: Directory not found: {change_dir}", file=sys.stderr)
        sys.exit(1)

    result = group_gaps(change_dir)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
