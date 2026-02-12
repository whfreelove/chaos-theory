#!/usr/bin/env python3
"""
Triage policy resolver for OpenSpec gap workflow.
Reads per-change triage configuration and outputs prose for skill consumption.

Usage:
    python resolve_triage_policy.py <change_dir>                    # Read policy, output prose
    python resolve_triage_policy.py <change_dir> --init <profile>   # Write named profile to change dir
    python resolve_triage_policy.py <change_dir> --json             # Output raw JSON instead of prose
    python resolve_triage_policy.py <change_dir> --policy <name>    # Resolve named profile (preview)
    python resolve_triage_policy.py --list                          # List available profiles

Output:
    Prose triage instructions or JSON to stdout
"""

import argparse
import json
import sys
from pathlib import Path

VALID_ACTIONS = {"check-in", "delegate", "defer-release", "defer-resolution"}
VALID_AUTHORITIES = {"user", "agent"}
SEVERITY_LEVELS = ["high", "medium", "low"]

PROFILE_DESCRIPTIONS = {
    "default": "HIGH/MEDIUM=user decides, LOW=agent decides",
    "conservative": "All severities require user check-in",
    "confident": "HIGH=user, MEDIUM/LOW=agent decides",
    "autonomous": "All severities delegated to agent",
}


def load_profiles(script_dir: Path) -> dict:
    """Load bundled triage profiles from plugin root."""
    plugin_root = script_dir.parent
    profiles_path = plugin_root / "triage-policies.json"
    if not profiles_path.exists():
        print(f"ERROR: Bundled profiles not found: {profiles_path}", file=sys.stderr)
        sys.exit(1)
    with open(profiles_path) as f:
        return json.load(f)


def validate_policy(policy: dict) -> list[str]:
    """Validate a triage policy structure. Returns list of error messages."""
    errors = []

    for level in SEVERITY_LEVELS:
        if level not in policy:
            errors.append(f"Missing required key: {level}")
            continue

        entry = policy[level]

        if not isinstance(entry, dict):
            errors.append(f"{level}: must be an object")
            continue

        if "authority" not in entry:
            errors.append(f"{level}: missing 'authority' field")
        elif entry["authority"] not in VALID_AUTHORITIES:
            errors.append(
                f"{level}: authority must be 'user' or 'agent', got '{entry['authority']}'"
            )

        if "actions" not in entry:
            errors.append(f"{level}: missing 'actions' field")
        elif not isinstance(entry["actions"], list) or len(entry["actions"]) == 0:
            errors.append(f"{level}: actions must be a non-empty array")
        else:
            invalid = [a for a in entry["actions"] if a not in VALID_ACTIONS]
            if invalid:
                errors.append(
                    f"{level}: invalid actions: {', '.join(invalid)}. "
                    f"Valid: {', '.join(sorted(VALID_ACTIONS))}"
                )

    return errors


def format_prose(policy: dict) -> str:
    """Format triage policy as prose instructions for skill consumption."""
    lines = ["## Triage Policy", ""]

    for level in SEVERITY_LEVELS:
        entry = policy[level]
        authority = entry["authority"]
        actions = entry["actions"]

        if len(actions) == 1:
            lines.append(
                f"- **{level.upper()} severity**: Apply {actions[0]} directly (single option)."
            )
        elif authority == "user":
            actions_str = ", ".join(actions)
            lines.append(
                f"- **{level.upper()} severity**: User decides via AskUserQuestion. Options: {actions_str}."
            )
        else:
            actions_str = ", ".join(actions)
            lines.append(
                f"- **{level.upper()} severity**: Agent triages autonomously. Options: {actions_str}."
            )

    return "\n".join(lines)


def cmd_init(change_dir: Path, profile_name: str, force: bool, script_dir: Path):
    """Write a named profile to .triage-policy.json in the change directory."""
    profiles = load_profiles(script_dir)

    if profile_name not in profiles:
        available = ", ".join(sorted(profiles.keys()))
        print(
            f"ERROR: Unknown profile '{profile_name}'. Available: {available}",
            file=sys.stderr,
        )
        sys.exit(1)

    policy_path = change_dir / ".triage-policy.json"
    if policy_path.exists() and not force:
        print(
            f"ERROR: {policy_path} already exists. Use --force to overwrite.",
            file=sys.stderr,
        )
        sys.exit(1)

    policy = profiles[profile_name]
    with open(policy_path, "w") as f:
        json.dump(policy, f, indent=2)
        f.write("\n")

    print(f"Wrote '{profile_name}' profile to {policy_path}", file=sys.stderr)


def cmd_list(script_dir: Path):
    """List available profile names with descriptions."""
    profiles = load_profiles(script_dir)

    print("Available triage profiles:\n")
    for name in profiles:
        desc = PROFILE_DESCRIPTIONS.get(name, "")
        print(f"  {name:15s} {desc}")


def cmd_read(change_dir: Path, output_json: bool):
    """Read .triage-policy.json and output prose or JSON."""
    policy_path = change_dir / ".triage-policy.json"

    if not policy_path.exists():
        print(
            f"ERROR: No .triage-policy.json in {change_dir}.\n"
            f"\n"
            f"Run tokamak:new-change to create a change with triage policy initialized,\n"
            f"or initialize manually: python {Path(__file__).resolve()} {change_dir} --init <profile>\n"
            f"Use --list to see available profiles.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        with open(policy_path) as f:
            policy = json.load(f)
    except json.JSONDecodeError as e:
        print(
            f"ERROR: Invalid JSON in {policy_path}: line {e.lineno}, col {e.colno}: {e.msg}",
            file=sys.stderr,
        )
        sys.exit(1)

    errors = validate_policy(policy)
    if errors:
        print(f"ERROR: Invalid triage policy in {policy_path}:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    if output_json:
        print(json.dumps(policy, indent=2))
    else:
        print(format_prose(policy))


def cmd_policy(profile_name: str, output_json: bool, script_dir: Path):
    """Resolve a named profile without reading .triage-policy.json."""
    profiles = load_profiles(script_dir)

    if profile_name not in profiles:
        available = ", ".join(sorted(profiles.keys()))
        print(
            f"ERROR: Unknown profile '{profile_name}'. Available: {available}",
            file=sys.stderr,
        )
        sys.exit(1)

    policy = profiles[profile_name]

    if output_json:
        print(json.dumps(policy, indent=2))
    else:
        print(format_prose(policy))


def main():
    parser = argparse.ArgumentParser(
        description="Resolve triage policy for OpenSpec gap workflow"
    )
    parser.add_argument(
        "change_dir",
        type=Path,
        nargs="?",
        help="Path to OpenSpec change directory",
    )
    parser.add_argument(
        "--init",
        metavar="PROFILE",
        help="Write named profile to .triage-policy.json in change dir",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing .triage-policy.json (with --init)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available profile names with descriptions",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of prose",
    )
    parser.add_argument(
        "--policy",
        metavar="NAME",
        help="Resolve a named profile instead of reading .triage-policy.json",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).parent.resolve()

    # --list doesn't need change_dir
    if args.list:
        cmd_list(script_dir)
        return

    # All other modes require change_dir
    if args.change_dir is None:
        parser.error("change_dir is required (unless using --list)")

    change_dir = args.change_dir.resolve()

    if not change_dir.exists():
        print(f"ERROR: Change directory not found: {change_dir}", file=sys.stderr)
        sys.exit(1)

    # --init mode
    if args.init:
        cmd_init(change_dir, args.init, args.force, script_dir)
        return

    # --policy mode (preview named profile)
    if args.policy:
        cmd_policy(args.policy, args.json, script_dir)
        return

    # Default: read .triage-policy.json
    cmd_read(change_dir, args.json)


if __name__ == "__main__":
    main()
