"""Shared helpers for research notebooks."""
import json
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ClaudeResult:
    """Result from a claude -p invocation."""
    output: dict            # parsed JSON from --output-format json
    session_id: str         # the session UUID used
    returncode: int         # subprocess exit code
    stderr: str             # stderr output (diagnostics)


def run_claude(
    prompt: str,
    *,
    plugin_dir: Path | None = None,
    session_id: str | None = None,
) -> ClaudeResult:
    """Run claude -p with --session-id + --output-format json.

    Args:
        prompt: The prompt to send to claude -p.
        plugin_dir: Optional plugin directory to load via --plugin-dir.
        session_id: Optional session ID. Generated if not provided.

    Returns:
        ClaudeResult with parsed output, session_id, returncode, stderr.
    """
    if session_id is None:
        session_id = str(uuid.uuid4())

    cmd = ["claude", "-p", prompt, "--session-id", session_id, "--output-format", "json"]
    if plugin_dir is not None:
        cmd.extend(["--plugin-dir", str(plugin_dir)])

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = json.loads(result.stdout) if result.stdout.strip() else {"error": result.stderr}

    return ClaudeResult(
        output=output,
        session_id=session_id,
        returncode=result.returncode,
        stderr=result.stderr,
    )
