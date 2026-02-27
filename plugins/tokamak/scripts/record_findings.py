#!/usr/bin/env python3
"""Persist Section B validation output to findings.json.

Reads validation JSON from stdin, appends a timestamped round entry
to findings.json in the change directory.

Usage:
    echo '<validation_json>' | python record_findings.py <change_dir>
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def _get_git_commit() -> str:
    """Get current git HEAD commit hash, or empty string if unavailable."""
    try:
        return subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ''


def parse_critic_name(finding_text: str) -> str:
    """Extract critic name from finding text.

    Findings follow the pattern "CriticName-N: title" in headings.
    Convert to kebab-case-critic suffix format.
    """
    # Try "Name-N: ..." pattern from critic output headings
    m = re.match(r'^([A-Za-z][A-Za-z ]+?)(?:-\d+)?:', finding_text)
    if m:
        name = m.group(1).strip().lower().replace(' ', '-')
        if not name.endswith('-critic'):
            name += '-critic'
        return name
    return 'unknown-critic'


def main():
    if len(sys.argv) < 2:
        print("Usage: echo '<json>' | python record_findings.py <change_dir>",
              file=sys.stderr)
        sys.exit(1)

    change_dir = Path(sys.argv[1])
    if not change_dir.exists():
        print(f"ERROR: Change directory not found: {change_dir}",
              file=sys.stderr)
        sys.exit(1)

    # Read validation JSON from stdin
    raw = sys.stdin.read().strip()
    if not raw:
        print("ERROR: No validation JSON provided on stdin", file=sys.stderr)
        sys.exit(1)

    try:
        validation = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON on stdin: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(validation, list):
        print("ERROR: Validation JSON must be a list", file=sys.stderr)
        sys.exit(1)

    # Read existing findings.json or create empty
    findings_path = change_dir / 'findings.json'
    if findings_path.exists():
        with open(findings_path) as f:
            rounds = json.load(f)
        if not isinstance(rounds, list):
            rounds = []
    else:
        rounds = []

    # Determine round number
    round_num = len(rounds) + 1

    # Build findings entries
    findings = []
    for entry in validation:
        finding_text = entry.get('finding', '')
        findings.append({
            'critic': parse_critic_name(finding_text),
            'finding': finding_text,
            'status': entry.get('status', 'UNCOVERED'),
            'matched_gaps': entry.get('matched_gaps', []),
            'match_reason': entry.get('match_reason', ''),
        })

    # Append round entry
    rounds.append({
        'round': round_num,
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'commit': _get_git_commit(),
        'findings': findings,
    })

    # Write back
    with open(findings_path, 'w') as f:
        json.dump(rounds, f, indent=2)
        f.write('\n')

    print(f"Recorded round {round_num} with {len(findings)} findings "
          f"to {findings_path}", file=sys.stderr)


if __name__ == '__main__':
    main()
