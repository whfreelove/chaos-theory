#!/usr/bin/env python3
"""Shared utilities for OpenSpec tokamak scripts."""

import asyncio
import json
import os
import re
import shutil
import sys
from collections.abc import Callable
from pathlib import Path, PurePosixPath


async def gather_with_callback(
    coros: list,
    on_complete: Callable[[], None] | None = None,
) -> list:
    """Wrap asyncio.gather with a per-completion callback.

    Each coroutine's result is preserved in order. After each one finishes,
    on_complete() is called (if provided) so callers can update progress.
    """
    if on_complete is None:
        return await asyncio.gather(*coros)

    async def _wrap(coro):
        result = await coro
        on_complete()
        return result

    return await asyncio.gather(*[_wrap(c) for c in coros])


def resolve_skill_content(skill_name: str) -> str | None:
    """Read a tokamak skill's SKILL.md content."""
    name = skill_name.removeprefix('tokamak:')
    skill_file = Path(__file__).parent.parent / 'skills' / name / 'SKILL.md'
    if skill_file.exists():
        return skill_file.read_text()
    return None


def resolve_project_dir(change_dir: Path) -> Path | None:
    """Resolve project directory from .openspec.yaml project field."""
    openspec_path = change_dir / '.openspec.yaml'
    if not openspec_path.exists():
        return None
    with open(openspec_path) as f:
        for line in f:
            m = re.match(r'^project:\s*(.+)', line)
            if m:
                openspec_root = change_dir.parent.parent
                project_dir = (openspec_root / m.group(1).strip()).resolve()
                if project_dir.exists():
                    return project_dir
                return None
    return None


def _parse_schema_yaml(schema_path: Path) -> list[dict]:
    """Parse schema.yaml artifacts without requiring PyYAML.

    Returns list of dicts with keys: id, generates, instruction.
    Only parses the fields we need — not a full YAML parser.
    """
    if not schema_path.exists():
        return []

    text = schema_path.read_text()
    artifacts = []
    current = None
    in_instruction = False

    for line in text.splitlines():
        # New artifact entry (list item under artifacts:)
        m = re.match(r'^  - id:\s*(.+)', line)
        if m:
            if current:
                artifacts.append(current)
            current = {'id': m.group(1).strip(), 'generates': '', 'instruction': ''}
            in_instruction = False
            continue

        if current is None:
            continue

        # generates field
        m = re.match(r'^    generates:\s*(.+)', line)
        if m:
            current['generates'] = m.group(1).strip()
            in_instruction = False
            continue

        # instruction field (block scalar starts on next line)
        m = re.match(r'^    instruction:\s*>?\s*$', line)
        if m:
            in_instruction = True
            continue

        # Other 4-space field (description, template, requires, etc.) — ends instruction
        if re.match(r'^    \w', line) and not re.match(r'^      ', line):
            in_instruction = False
            continue

        # instruction content lines (6+ spaces indent under instruction:)
        if in_instruction and re.match(r'^      ', line) and current:
            current['instruction'] += line.strip() + '\n'
            continue

        # Empty line within instruction block preserves paragraph breaks
        if in_instruction and line.strip() == '' and current:
            current['instruction'] += '\n'
            continue

    if current:
        artifacts.append(current)

    # Clean up trailing whitespace in instructions
    for art in artifacts:
        art['instruction'] = art['instruction'].strip()

    return artifacts


def _extract_skills_from_instruction(instruction: str) -> list[str]:
    """Extract skill names from Invoke skill(s) lines in instruction text.

    Handles variants:
    - Invoke skill: `tokamak:writing-functional-specs`  (colon, single)
    - Invoke skill `tokamak:writing-y-statements`       (no colon, single)
    - Invoke skills: `tokamak:writing-technical-design`, `tokamak:writing-y-statements`  (plural, multiple)
    """
    skills = []
    for line in instruction.splitlines():
        if re.search(r'Invoke skills?', line, re.IGNORECASE):
            for m in re.finditer(r'`(tokamak:[^`]+)`', line):
                skill = m.group(1).strip()
                if skill not in skills:
                    skills.append(skill)
    return skills


def _match_generates(generates_pattern: str, filename: str) -> bool:
    """Check if a filename matches a generates pattern.

    Handles:
    - Exact match: "functional.md" matches "functional.md"
    - Glob match: "requirements/**/*.md" matches "requirements/x/requirements.feature.md"
    """
    if generates_pattern == filename:
        return True

    # Convert glob-style pattern to check path membership
    if '**' in generates_pattern or '*' in generates_pattern:
        pattern_path = PurePosixPath(generates_pattern)
        file_path = PurePosixPath(filename)

        # For "requirements/**/*.md", check if file is under "requirements/" and ends with .md
        pattern_parts = generates_pattern.split('/')
        file_parts = filename.split('/')

        # Simple prefix check: does the file path start with the pattern's root?
        if pattern_parts and file_parts:
            root = pattern_parts[0]
            if file_parts[0] == root:
                # Check suffix if pattern has a glob extension
                if generates_pattern.endswith('*.md') and filename.endswith('.md'):
                    return True
                if generates_pattern.endswith('*.yaml') and filename.endswith('.yaml'):
                    return True
                # Generic: file is under the root directory
                return len(file_parts) > 1

    return False


def load_schema_artifacts(change_dir: Path) -> dict[str, dict]:
    """Load per-artifact config from schema.yaml via .openspec.yaml.

    Returns dict mapping generates patterns to:
        {"instruction": str, "skills": list[str], "generates": str}

    Usage:
        artifacts = load_schema_artifacts(change_dir)
        config = lookup_artifact(artifacts, "functional.md")
        if config:
            print(config["instruction"])
            print(config["skills"])
    """
    # Read schema name from .openspec.yaml
    openspec_path = change_dir / '.openspec.yaml'
    if not openspec_path.exists():
        return {}

    schema_name = None
    with open(openspec_path) as f:
        for line in f:
            m = re.match(r'^schema:\s*(.+)', line)
            if m:
                schema_name = m.group(1).strip()
                break

    if not schema_name:
        return {}

    # Find schema.yaml — search from openspec root
    openspec_root = change_dir.parent.parent  # openspec/changes/<name>/ → openspec/
    schema_path = openspec_root / 'schemas' / schema_name / 'schema.yaml'
    if not schema_path.exists():
        return {}

    artifacts = _parse_schema_yaml(schema_path)
    result = {}
    for art in artifacts:
        skills = _extract_skills_from_instruction(art['instruction'])
        result[art['generates']] = {
            'instruction': art['instruction'],
            'skills': skills,
            'generates': art['generates'],
        }

    return result


def lookup_artifact(artifacts: dict[str, dict], filename: str) -> dict | None:
    """Find the artifact config matching a given filename.

    Handles exact matches and glob-pattern matching (e.g., requirements/**/*.md).
    """
    # Try exact match first
    if filename in artifacts:
        return artifacts[filename]

    # Try glob matching
    for pattern, config in artifacts.items():
        if _match_generates(pattern, filename):
            return config

    return None


# ---------------------------------------------------------------------------
# Gap parsing
# ---------------------------------------------------------------------------

def parse_gaps(gaps_md: str) -> list[dict]:
    """Parse gap entries from gaps.md markdown content.

    Returns list of dicts with keys: id, triage, decision, primary_file,
    description, severity, placement_result, title.
    """
    gaps: list[dict] = []
    current_gap: dict | None = None

    for line in gaps_md.splitlines():
        # Match gap header: ### GAP-XX: Title
        header_match = re.match(r'^###\s+(GAP-\d+):\s*(.*)', line)
        if header_match:
            if current_gap:
                gaps.append(current_gap)
            current_gap = {
                'id': header_match.group(1),
                'title': header_match.group(2).strip(),
                'triage': None,
                'decision': None,
                'primary_file': None,
                'description': None,
                'severity': None,
                'placement_result': None,
            }
            continue

        if current_gap is None:
            continue

        # Match fields
        triage_match = re.match(r'^-\s+\*\*Triage\*\*:\s*(.+)', line)
        if triage_match:
            current_gap['triage'] = triage_match.group(1).strip()
            continue

        decision_match = re.match(r'^-\s+\*\*Decision\*\*:\s*(.+)', line)
        if decision_match:
            current_gap['decision'] = decision_match.group(1).strip()
            continue

        primary_file_match = re.match(r'^-\s+\*\*Primary-file\*\*:\s*(.+)', line)
        if primary_file_match:
            current_gap['primary_file'] = primary_file_match.group(1).strip()
            continue

        description_match = re.match(r'^-\s+\*\*Description\*\*:\s*(.+)', line)
        if description_match:
            current_gap['description'] = description_match.group(1).strip()
            continue

        severity_match = re.match(r'^-\s+\*\*Severity\*\*:\s*(.+)', line)
        if severity_match:
            current_gap['severity'] = severity_match.group(1).strip()
            continue

        placement_result_match = re.match(
            r'^-\s+\*\*Placement-result\*\*:\s*(.+)', line
        )
        if placement_result_match:
            current_gap['placement_result'] = placement_result_match.group(1).strip()
            continue

    # Don't forget the last gap
    if current_gap:
        gaps.append(current_gap)

    return gaps


# ---------------------------------------------------------------------------
# Gap entry extraction
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Gap file write primitives
# ---------------------------------------------------------------------------

def _find_gap_range(lines: list[str], gap_id: str) -> tuple[int, int] | None:
    """Find the line range [start, end) for a gap entry in a gaps/resolved file.

    Returns (start_line, end_line) where start_line is the ### header
    and end_line is the line AFTER the last line of the entry.
    """
    start = None
    for i, line in enumerate(lines):
        if line.startswith(f'### {gap_id}:'):
            start = i
            continue
        if start is not None and (line.startswith('### ') or line.startswith('## ')):
            return (start, i)
    if start is not None:
        # Gap runs to end of file — trim trailing blank lines
        end = len(lines)
        while end > start and lines[end - 1].strip() == '':
            end -= 1
        return (start, min(end + 1, len(lines)))  # include one trailing blank, bounded
    return None


def write_gap_field(change_dir: Path, gap_id: str, field: str, value: str) -> None:
    """Update or add a field for a specific gap in gaps.md."""
    gaps_path = change_dir / 'gaps.md'
    content = gaps_path.read_text()
    lines = content.splitlines()
    gap_range = _find_gap_range(lines, gap_id)
    if gap_range is None:
        raise ValueError(f"Gap {gap_id} not found in {gaps_path}")

    start, end = gap_range
    field_pattern = re.compile(rf'^-\s+\*\*{re.escape(field)}\*\*:\s*')

    # Search for existing field within the gap
    for i in range(start, end):
        if field_pattern.match(lines[i]):
            lines[i] = f'- **{field}**: {value}'
            gaps_path.write_text('\n'.join(lines) + '\n')
            return

    # Field not found — insert after last field line (before blank/next entry)
    insert_at = start + 1
    for i in range(start + 1, end):
        if lines[i].startswith('- **'):
            insert_at = i + 1
    lines.insert(insert_at, f'- **{field}**: {value}')
    gaps_path.write_text('\n'.join(lines) + '\n')


def write_gap_fields(change_dir: Path, gap_id: str, fields: dict[str, str]) -> None:
    """Update or add multiple fields for a specific gap in gaps.md."""
    for field, value in fields.items():
        write_gap_field(change_dir, gap_id, field, value)


def clear_gap_field(change_dir: Path, gap_id: str, field: str) -> None:
    """Remove a field from a specific gap in gaps.md."""
    gaps_path = change_dir / 'gaps.md'
    content = gaps_path.read_text()
    lines = content.splitlines()
    gap_range = _find_gap_range(lines, gap_id)
    if gap_range is None:
        raise ValueError(f"Gap {gap_id} not found in {gaps_path}")

    start, end = gap_range
    field_pattern = re.compile(rf'^-\s+\*\*{re.escape(field)}\*\*:\s*')

    for i in range(start, end):
        if field_pattern.match(lines[i]):
            del lines[i]
            gaps_path.write_text('\n'.join(lines) + '\n')
            return


def append_gap_entry(change_dir: Path, gap_id: str, title: str,
                     severity: str, fields: dict[str, str]) -> None:
    """Append a new gap entry to gaps.md."""
    gaps_path = change_dir / 'gaps.md'
    content = gaps_path.read_text()

    # Build the entry text
    entry_lines = [f'### {gap_id}: {title}']
    for field, value in fields.items():
        entry_lines.append(f'- **{field}**: {value}')
    entry_text = '\n'.join(entry_lines)

    # Append at end of file with a blank line separator
    stripped = content.rstrip()
    gaps_path.write_text(stripped + '\n\n' + entry_text + '\n')


def move_gap_to_resolved(change_dir: Path, gap_id: str, status: str,
                         outcome: str, *,
                         superseded_by: str | None = None,
                         current_approach: str | None = None) -> None:
    """Move a gap from gaps.md to resolved.md with status and outcome.

    Extracts the full entry from gaps.md, adds Status and Outcome fields,
    appends it to resolved.md, and removes it from gaps.md.

    For superseded gaps, optional ``superseded_by`` and ``current_approach``
    record the supersession chain per managing-spec-gaps rules.
    """
    gaps_path = change_dir / 'gaps.md'
    resolved_path = change_dir / 'resolved.md'

    # Extract from gaps.md
    gaps_content = gaps_path.read_text()
    gaps_lines = gaps_content.splitlines()
    gap_range = _find_gap_range(gaps_lines, gap_id)
    if gap_range is None:
        raise ValueError(f"Gap {gap_id} not found in {gaps_path}")

    start, end = gap_range
    entry_lines = gaps_lines[start:end]

    # Determine severity from the entry
    severity = None
    for line in entry_lines:
        m = re.match(r'^-\s+\*\*Severity\*\*:\s*(.+)', line)
        if m:
            severity = m.group(1).strip()
            break

    if not severity:
        raise ValueError(f"Gap {gap_id} has no Severity field")

    # Add Status and Outcome fields to the entry
    # Insert after the last existing field line
    last_field_idx = 0
    for i, line in enumerate(entry_lines):
        if line.startswith('- **'):
            last_field_idx = i
    offset = 1
    entry_lines.insert(last_field_idx + offset, f'- **Status**: {status}')
    offset += 1
    if superseded_by:
        entry_lines.insert(last_field_idx + offset,
                           f'- **Superseded by**: {superseded_by}')
        offset += 1
    entry_lines.insert(last_field_idx + offset, f'- **Outcome**: {outcome}')
    offset += 1
    if current_approach:
        entry_lines.insert(last_field_idx + offset,
                           f'- **Current approach**: {current_approach}')

    # Remove from gaps.md
    # Also remove trailing blank line if present
    remove_end = end
    while remove_end < len(gaps_lines) and gaps_lines[remove_end].strip() == '':
        remove_end += 1
        break  # only remove one trailing blank
    del gaps_lines[start:remove_end]
    gaps_path.write_text('\n'.join(gaps_lines) + '\n')

    # Append to resolved.md
    if not resolved_path.exists():
        resolved_path.write_text('# Resolved Gaps\n\n')

    resolved_content = resolved_path.read_text()
    entry_text = '\n'.join(entry_lines)
    stripped = resolved_content.rstrip()
    resolved_path.write_text(stripped + '\n\n' + entry_text + '\n')


def next_gap_id(change_dir: Path) -> str:
    """Compute next available GAP-N id from gaps.md + resolved.md."""
    max_n = 0
    for filename in ('gaps.md', 'resolved.md'):
        filepath = change_dir / filename
        if not filepath.exists():
            continue
        for m in re.finditer(r'GAP-(\d+)', filepath.read_text()):
            n = int(m.group(1))
            if n > max_n:
                max_n = n
    return f'GAP-{max_n + 1}'


def format_detector_finding_as_gap(
    finding: dict, gap_id: str, critic_name: str
) -> tuple[str, str, dict[str, str]]:
    """Convert a detector JSON finding to gap markdown fields.

    Returns (title, severity, fields_dict) for use with append_gap_entry.
    """
    title = finding.get('title', finding.get('summary', 'Untitled finding'))
    severity = finding.get('severity', 'medium').lower()
    source = critic_name.strip().lower().replace(' ', '-')
    if not source.endswith('-detection'):
        source += '-detection'
    description = finding.get('description', finding.get('finding', ''))

    fields = {
        'Source': source,
        'Severity': severity,
        'Description': description,
    }
    return (title, severity, fields)


# ---------------------------------------------------------------------------
# Gap entry extraction
# ---------------------------------------------------------------------------

def read_gap_entries(change_dir: Path, gap_ids: list[str]) -> str:
    """Extract specific gap entries from gaps.md for inclusion in prompts."""
    gaps_path = change_dir / 'gaps.md'
    if not gaps_path.exists():
        return ""

    content = gaps_path.read_text()
    lines = content.splitlines()
    entries: list[str] = []
    capturing = False
    current_entry: list[str] = []

    for line in lines:
        if line.startswith('### GAP-'):
            if capturing and current_entry:
                entries.append('\n'.join(current_entry))
            gap_id = line.split(':')[0].replace('### ', '')
            if gap_id in gap_ids:
                capturing = True
                current_entry = [line]
            else:
                capturing = False
                current_entry = []
        elif capturing:
            # Stop at next heading of same or higher level
            if line.startswith('## ') or line.startswith('# '):
                entries.append('\n'.join(current_entry))
                capturing = False
                current_entry = []
            else:
                current_entry.append(line)

    if capturing and current_entry:
        entries.append('\n'.join(current_entry))

    return '\n\n'.join(entries)


# ---------------------------------------------------------------------------
# Subprocess command building and execution
# ---------------------------------------------------------------------------

def build_command(
    change_dir: Path,
    project_dir: Path | None,
    system_prompt: str,
    model: str,
    budget: float | None,
    tools: str = 'Read,Edit,Write',
    extra_dirs: list[Path] | None = None,
    session_id: str | None = None,
    resume: bool = False,
) -> list[str]:
    """Build a claude -p command for a subprocess.

    Args:
        change_dir: Change directory (always added via --add-dir).
        project_dir: Optional project directory (added via --add-dir).
        system_prompt: System prompt appended via --append-system-prompt.
        model: Model name (e.g., 'opus', 'sonnet', 'haiku').
        budget: Optional max budget in USD.
        tools: Comma-separated tool names (e.g., 'Read,Edit,Write').
        extra_dirs: Additional directories to add via --add-dir.
        session_id: Optional session ID for --session-id or --resume.
        resume: If True, use --resume instead of --session-id and omit
                --append-system-prompt.
    """
    claude = shutil.which('claude')
    if not claude:
        print("ERROR: claude CLI not found in PATH", file=sys.stderr)
        sys.exit(1)

    cmd = [claude, '-p']
    cmd.extend(['--model', model])
    cmd.extend(['--tools', tools])
    cmd.extend(['--permission-mode', 'bypassPermissions'])

    if resume and session_id:
        cmd.extend(['--resume', session_id])
    elif session_id:
        cmd.extend(['--session-id', session_id])
        cmd.extend(['--append-system-prompt', system_prompt])
    else:
        cmd.append('--no-session-persistence')
        cmd.extend(['--append-system-prompt', system_prompt])

    # Grant filesystem access
    cmd.extend(['--add-dir', str(change_dir)])
    if project_dir:
        cmd.extend(['--add-dir', str(project_dir)])
    if extra_dirs:
        for d in extra_dirs:
            cmd.extend(['--add-dir', str(d)])

    if budget is not None:
        cmd.extend(['--max-budget-usd', str(budget)])

    return cmd


async def _read_both(proc):
    """Read stdout and stderr concurrently and wait for process exit."""
    stdout, stderr = await asyncio.gather(
        proc.stdout.read(),
        proc.stderr.read(),
    )
    await proc.wait()
    return stdout, stderr


async def run_one_subprocess(
    name: str,
    cmd: list[str],
    prompt: str,
    timeout: int,
    semaphore: asyncio.Semaphore,
) -> dict:
    """Launch a single claude -p subprocess and collect output.

    On timeout, drains partial stdout before killing the process so that
    any work already emitted (e.g. solver proposals) is preserved for
    diagnostic purposes.
    """
    async with semaphore:
        print(f"[RUNNING] {name}", file=sys.stderr)

        env = {k: v for k, v in os.environ.items() if k != 'CLAUDECODE'}

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        # Send prompt and close stdin so the subprocess can start work
        proc.stdin.write(prompt.encode())
        await proc.stdin.drain()
        proc.stdin.close()

        try:
            stdout, stderr = await asyncio.wait_for(
                _read_both(proc),
                timeout=timeout,
            )

            if proc.returncode == 0:
                print(f"[SUCCESS] {name}", file=sys.stderr)
                output = stdout.decode().strip()
                report = try_parse_json(output)
                return {
                    'name': name,
                    'status': 'success',
                    'output': output,
                    'report': report,
                }
            else:
                stderr_text = stderr.decode().strip()
                stdout_text = stdout.decode().strip()
                if stderr_text:
                    error_msg = stderr_text
                else:
                    # claude CLI often writes errors to stdout, not stderr
                    error_msg = stdout_text[:500] or f"exit code {proc.returncode}"
                print(f"[FAILED] {name}: {error_msg}", file=sys.stderr)
                return {
                    'name': name,
                    'status': 'error',
                    'output': stdout.decode().strip(),
                    'error': error_msg,
                    'report': [],
                }
        except asyncio.TimeoutError:
            proc.kill()
            # Drain any partial stdout emitted before the kill
            partial = b''
            try:
                partial = await asyncio.wait_for(proc.stdout.read(), timeout=5)
            except (asyncio.TimeoutError, Exception):
                pass
            await proc.wait()

            output = partial.decode().strip()
            report = try_parse_json(output) if output else []
            status_note = 'timeout' if not output else 'timeout (partial output captured)'
            print(f"[TIMEOUT] {name}: {status_note} after {timeout}s", file=sys.stderr)
            return {
                'name': name,
                'status': 'error',
                'output': output,
                'error': f'{status_note} after {timeout}s',
                'report': report,
            }


def try_parse_json(text: str) -> list:
    """Try to extract a JSON list from subprocess output.

    Handles cases where the output contains markdown or other text
    surrounding the JSON.
    """
    # Try direct parse
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        return [parsed]
    except json.JSONDecodeError:
        pass

    # Try to find JSON in code blocks
    json_blocks = re.findall(r'```(?:json)?\s*\n(.*?)\n```', text, re.DOTALL)
    for block in json_blocks:
        try:
            parsed = json.loads(block)
            if isinstance(parsed, list):
                return parsed
            return [parsed]
        except json.JSONDecodeError:
            continue

    # Try to find a JSON array in the text
    bracket_match = re.search(r'\[.*\]', text, re.DOTALL)
    if bracket_match:
        try:
            parsed = json.loads(bracket_match.group())
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

    return []
