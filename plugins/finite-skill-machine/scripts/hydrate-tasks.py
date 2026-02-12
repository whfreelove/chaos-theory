#!/usr/bin/env python3
"""
FSM (Finite Skill Machine) - Task hydration hook for Claude Code.

This PostToolUse hook on Skill reads a companion fsm.json file and writes
tasks directly to the task store.
"""

import json
import os
import sys
from pathlib import Path


def log(message: str) -> None:
    """Log message to stderr for debugging."""
    print(f"[fsm] {message}", file=sys.stderr)


def success_response() -> None:
    """Output success response and exit."""
    print(json.dumps({"continue": True}))
    sys.exit(0)


def error_exit(message: str) -> None:
    """Output error message and exit with failure."""
    log(f"ERROR: {message}")
    sys.exit(1)


def parse_stdin() -> dict:
    """Parse and validate stdin JSON from Claude Code hook."""
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        error_exit(f"Failed to parse stdin JSON: {e}")

    # Extract session_id
    session_id = data.get("session_id")
    if not session_id:
        error_exit("Missing required field: session_id")

    # Extract commandName from tool_response
    tool_response = data.get("tool_response", {})
    command_name = tool_response.get("commandName")
    if not command_name:
        error_exit("Missing required field: tool_response.commandName")

    cwd = data.get("cwd", os.getcwd())

    return {
        "session_id": session_id,
        "command_name": command_name,
        "cwd": cwd
    }


def get_installed_plugins_path() -> Path:
    """Get path to installed_plugins.json.

    Respects FSM_PLUGINS_FILE environment variable for testing.
    """
    plugins_file = os.environ.get("FSM_PLUGINS_FILE")
    if plugins_file:
        return Path(plugins_file)
    return Path.home() / ".claude" / "plugins" / "installed_plugins.json"


def parse_command_name(command_name: str) -> tuple[str | None, str]:
    """Parse command name into plugin name and skill name.

    Returns (plugin_name, skill_name) where plugin_name is None for non-plugin skills.
    """
    if ":" in command_name:
        parts = command_name.split(":", 1)
        return parts[0], parts[1]
    return None, command_name


def load_installed_plugins() -> tuple[str, list[dict] | dict] | None:
    """Load installed_plugins.json, returning format-tagged result or None.

    Returns:
        - ("v1", list[dict]) for v1 format (array)
        - ("v2", dict) for v2 format (object with version and plugins)
        - None if missing or malformed
    """
    plugins_path = get_installed_plugins_path()
    if not plugins_path.exists():
        return None

    try:
        with open(plugins_path) as f:
            data = json.load(f)

            # Format detection: v1 (array) vs v2 (object)
            if isinstance(data, list):
                # v1 format - emit deprecation notice
                log("DEPRECATION: installed_plugins.json uses legacy v1 format. Update to v2 format.")
                return ("v1", data)
            elif isinstance(data, dict):
                # v2 format candidate - validate structure
                version = data.get("version")
                if version is None:
                    error_exit("installed_plugins.json is malformed: missing 'version' field")
                elif version != 2:
                    error_exit(f"installed_plugins.json has unsupported version: {version}")
                else:
                    plugins = data.get("plugins")
                    if plugins is None:
                        error_exit("installed_plugins.json is malformed: missing 'plugins' field")
                    elif not isinstance(plugins, dict):
                        error_exit("installed_plugins.json is malformed: 'plugins' must be an object")
                    else:
                        # Valid v2 structure
                        return ("v2", data)
            else:
                # Unknown root type (defensive - should never happen with valid JSON)
                return None
    except (json.JSONDecodeError, OSError):
        return None


def cwd_matches_project_path(cwd: str, project_path: str) -> bool:
    """Check if cwd is equal to or under project_path."""
    cwd_path = Path(cwd).resolve()
    proj_path = Path(project_path).resolve()

    try:
        cwd_path.relative_to(proj_path)
        return True
    except ValueError:
        return False


def find_plugin_install_path_v2(plugin_name: str, cwd: str, plugins_dict: dict) -> str | None:
    """Find the install path for a plugin in v2 format, respecting scope precedence.

    v2 format uses plugin@marketplace keys with entry arrays.
    Scope precedence: local > project > user
    """
    # Find matching key by splitting on @ and comparing plugin name
    matched_entries = None
    for key in plugins_dict:
        key_plugin_name = key.split("@", 1)[0]
        if key_plugin_name == plugin_name:
            matched_entries = plugins_dict[key]
            break

    if matched_entries is None:
        return None  # No match → fall through

    # Separate by scope and filter by project path
    local_entries = []
    project_entries = []
    user_entries = []

    for entry in matched_entries:
        scope = entry.get("scope", "user")
        project_path = entry.get("projectPath", "")
        install_path = entry.get("installPath", "")

        if not install_path:
            continue  # Skip entries without installPath

        if scope == "local":
            if project_path and cwd_matches_project_path(cwd, project_path):
                local_entries.append(install_path)
        elif scope == "project":
            if project_path and cwd_matches_project_path(cwd, project_path):
                project_entries.append(install_path)
        elif scope == "user":
            user_entries.append(install_path)

    # Return by precedence
    if local_entries:
        return local_entries[0]
    if project_entries:
        return project_entries[0]
    if user_entries:
        return user_entries[0]

    return None


def find_plugin_install_path(plugin_name: str, cwd: str, plugins: list[dict]) -> str | None:
    """Find the install path for a plugin, respecting scope precedence.

    Scope precedence: local > project > user
    """
    # Filter entries matching this plugin
    matching = []
    for entry in plugins:
        name = entry.get("name", "")
        # Match plugin@version format
        if name.startswith(f"{plugin_name}@"):
            matching.append(entry)

    if not matching:
        return None

    # Separate by scope and filter by project path
    local_entries = []
    project_entries = []
    user_entries = []

    for entry in matching:
        scope = entry.get("scope", "user")
        project_path = entry.get("projectPath", "")
        install_path = entry.get("installPath", "")

        if not install_path:
            continue

        if scope == "local":
            if project_path and cwd_matches_project_path(cwd, project_path):
                local_entries.append(install_path)
        elif scope == "project":
            if project_path and cwd_matches_project_path(cwd, project_path):
                project_entries.append(install_path)
        elif scope == "user":
            user_entries.append(install_path)

    # Return by precedence
    if local_entries:
        return local_entries[0]
    if project_entries:
        return project_entries[0]
    if user_entries:
        return user_entries[0]

    return None


def find_fsm_json_in_plugin(install_path: str, skill_name: str) -> Path | None:
    """Find fsm.json in plugin's skills or commands directory."""
    install = Path(install_path)

    # Check skills directory first
    skills_path = install / "skills" / skill_name / "fsm.json"
    if skills_path.exists():
        return skills_path

    # Check commands directory
    commands_path = install / "commands" / skill_name / "fsm.json"
    if commands_path.exists():
        return commands_path

    return None


def get_user_skills_root() -> Path:
    """Get root directory for user skills.

    Respects FSM_USER_SKILLS_ROOT environment variable for testing.
    """
    user_root = os.environ.get("FSM_USER_SKILLS_ROOT")
    if user_root:
        return Path(user_root)
    return Path.home() / ".claude" / "skills"


def find_fsm_json_non_plugin(skill_name: str, cwd: str) -> Path | None:
    """Find fsm.json for non-plugin skills (project or user directory)."""
    # Check project directory first
    project_path = Path(cwd) / ".claude" / "skills" / skill_name / "fsm.json"
    if project_path.exists():
        return project_path

    # Check user directory
    user_path = get_user_skills_root() / skill_name / "fsm.json"
    if user_path.exists():
        return user_path

    return None


def find_fsm_json(command_name: str, cwd: str) -> Path | None:
    """Locate fsm.json for the given command name."""
    plugin_name, skill_name = parse_command_name(command_name)

    if plugin_name:
        # Plugin-style command
        result = load_installed_plugins()

        if result is None:
            # installed_plugins.json missing or malformed - fail-closed
            error_exit(f"Skill '{command_name}' not found - installed_plugins.json is missing or malformed")

        format_type, registry_data = result

        if format_type == "v1":
            # v1 format: registry_data is a list
            install_path = find_plugin_install_path(plugin_name, cwd, registry_data)

            if install_path:
                fsm_path = find_fsm_json_in_plugin(install_path, skill_name)
                if fsm_path:
                    return fsm_path

            # Plugin not found in valid installed_plugins.json - fall back to non-plugin lookup
            return find_fsm_json_non_plugin(skill_name, cwd)
        elif format_type == "v2":
            # v2 format: registry_data is a dict with version and plugins
            plugins_dict = registry_data.get("plugins", {})
            install_path = find_plugin_install_path_v2(plugin_name, cwd, plugins_dict)

            if install_path:
                fsm_path = find_fsm_json_in_plugin(install_path, skill_name)
                if fsm_path:
                    return fsm_path

            # Plugin not found in valid installed_plugins.json - fall back to non-plugin lookup
            return find_fsm_json_non_plugin(skill_name, cwd)
    else:
        # Non-plugin skill
        return find_fsm_json_non_plugin(skill_name, cwd)


def load_fsm_json(path: Path) -> list[dict]:
    """Load and parse fsm.json file."""
    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        error_exit(f"Malformed JSON in {path}: {e}")
    except OSError as e:
        error_exit(f"Failed to read {path}: {e}")

    if not isinstance(data, list):
        error_exit(f"fsm.json must be an array of tasks, got {type(data).__name__}")

    return data


def validate_fsm_tasks(tasks: list[dict], fsm_path: Path) -> list[str]:
    """Validate fsm.json tasks and return list of errors."""
    errors = []
    seen_ids = set()
    valid_ids = set()

    # First pass: collect all valid IDs and check required fields
    for i, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append(f"Task {i}: must be an object, got {type(task).__name__}")
            continue

        task_id = task.get("id")
        if task_id is None:
            errors.append(f"Task {i}: missing required field 'id'")
        elif not isinstance(task_id, int):
            errors.append(f"Task {i}: 'id' must be a number, got {type(task_id).__name__}")
        else:
            if task_id in seen_ids:
                errors.append(f"Task {i}: duplicate id {task_id}")
            else:
                seen_ids.add(task_id)
                valid_ids.add(task_id)

        subject = task.get("subject")
        if subject is None:
            errors.append(f"Task {i}: missing required field 'subject'")
        elif not isinstance(subject, str):
            errors.append(f"Task {i}: 'subject' must be a string, got {type(subject).__name__}")

    # Second pass: validate dependency references
    for i, task in enumerate(tasks):
        if not isinstance(task, dict):
            continue

        for field in ["blockedBy", "blocks"]:
            refs = task.get(field, [])
            if not isinstance(refs, list):
                errors.append(f"Task {i}: '{field}' must be an array")
                continue

            for ref in refs:
                if not isinstance(ref, int):
                    errors.append(f"Task {i}: '{field}' contains non-integer: {ref}")
                elif ref not in valid_ids:
                    errors.append(f"Task {i}: '{field}' references non-existent id {ref}")

    return errors


ALLOWED_STATUSES = {"completed", "pending"}


def check_active_tasks(task_dir: Path, command_name: str) -> None:
    """Check if re-invocation is safe for the invoking skill.

    Aborts if matching tasks have statuses outside the allowlist
    or mixed statuses within the allowlist.
    """
    matching_tasks = find_skill_tasks(task_dir, command_name)
    if not matching_tasks:
        return  # Empty set is vacuously uniform — no tasks to protect

    # Collect statuses from matching tasks
    task_statuses = []
    for task_file in matching_tasks:
        data = json.loads(task_file.read_text())
        task_id = int(data["id"])
        status = data["status"]
        task_statuses.append((task_id, status))

    # Check allowlist and uniformity
    statuses = {s for _, s in task_statuses}
    task_ids = [tid for tid, _ in task_statuses]

    # Abort if any status outside allowlist OR mixed statuses within allowlist
    if not statuses <= ALLOWED_STATUSES or len(statuses) > 1:
        error_exit(json.dumps({
            "tasks": task_ids,
            "message": "Related active task(s) must be resolved and verified first."
        }))


def get_task_directory(session_id: str) -> Path:
    """Get the task directory for the given session.

    Respects FSM_TASK_ROOT environment variable for testing.
    """
    task_root = os.environ.get("FSM_TASK_ROOT")
    if task_root:
        return Path(task_root) / session_id
    return Path.home() / ".claude" / "tasks" / session_id


def find_max_preserved_task_id(task_dir: Path, command_name: str) -> int:
    """Find the maximum task ID among preserved tasks (not targeted for deletion)."""
    max_id = 0

    if not task_dir.exists():
        return max_id

    for task_file in task_dir.glob("*.json"):
        # Handle non-numeric filenames
        try:
            stem = task_file.stem
            task_id = int(stem)
        except ValueError:
            continue  # Non-numeric filename, not a task file

        # Read and validate task file (fail-fast on errors)
        try:
            with open(task_file) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            error_exit(f"Failed to read task file {task_file.name}: invalid JSON - {e}")
        except OSError as e:
            error_exit(f"Failed to read task file {task_file.name}: {e}")

        # Validate structure
        if not isinstance(data, dict):
            error_exit(f"Malformed task file {task_file.name}: must be an object")
        if "id" not in data or "status" not in data or "metadata" not in data:
            error_exit(f"Malformed task file {task_file.name}: missing required fields")

        metadata = data.get("metadata", {})
        # Skip only tasks matching the invoking skill (targeted for deletion)
        # Other skills' FSM tasks are preserved and included in max ID
        if isinstance(metadata, dict) and metadata.get("fsm") == command_name:
            continue  # Skip tasks targeted for deletion

        max_id = max(max_id, task_id)

    return max_id


def translate_ids(tasks: list[dict], base_id: int) -> list[dict]:
    """Translate local IDs to actual IDs."""
    # Build translation map
    id_map = {}
    for task in tasks:
        local_id = task["id"]
        actual_id = base_id + local_id
        id_map[local_id] = actual_id

    # Translate tasks
    translated = []
    for task in tasks:
        new_task = dict(task)
        new_task["id"] = id_map[task["id"]]

        # Translate blockedBy
        if "blockedBy" in new_task:
            new_task["blockedBy"] = [id_map[ref] for ref in new_task["blockedBy"]]

        # Translate blocks
        if "blocks" in new_task:
            new_task["blocks"] = [id_map[ref] for ref in new_task["blocks"]]

        translated.append(new_task)

    return translated


def build_task_file(task: dict, command_name: str) -> dict:
    """Build a task file in Claude Code's native format."""
    # Merge fsm metadata with any custom metadata
    metadata = dict(task.get("metadata", {}))
    metadata["fsm"] = command_name

    return {
        "id": str(task["id"]),  # ID must be a string
        "subject": task["subject"],
        "description": task.get("description", ""),
        "activeForm": task.get("activeForm", ""),
        "owner": task.get("owner", ""),
        "status": task.get("status", "pending"),
        "blocks": [str(ref) for ref in task.get("blocks", [])],
        "blockedBy": [str(ref) for ref in task.get("blockedBy", [])],
        "metadata": metadata
    }


def find_skill_tasks(task_dir: Path, command_name: str) -> list[Path]:
    """Find all tasks matching the given skill's command_name."""
    fsm_tasks = []

    if not task_dir.exists():
        return fsm_tasks

    for task_file in task_dir.glob("*.json"):
        # Read and validate task file (fail-fast on errors)
        try:
            with open(task_file) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            error_exit(f"Malformed task file {task_file.name}: invalid JSON - {e}")
        except OSError as e:
            error_exit(f"Failed to read task file {task_file.name}: {e}")

        # Validate structure - malformed files could hide active tasks
        if not isinstance(data, dict):
            error_exit(f"Malformed task file {task_file.name}: must be an object, got {type(data).__name__}")

        if "id" not in data or not isinstance(data["id"], str):
            error_exit(f"Malformed task file {task_file.name}: missing or invalid 'id' field")

        if "status" not in data or not isinstance(data["status"], str):
            error_exit(f"Malformed task file {task_file.name}: missing or invalid 'status' field")

        if "metadata" not in data or not isinstance(data["metadata"], dict):
            error_exit(f"Malformed task file {task_file.name}: missing or invalid 'metadata' field")

        metadata = data["metadata"]
        # Filter by fsm value match instead of key existence
        # Non-string fsm values (None, int, "") naturally don't match any command_name
        if metadata.get("fsm") == command_name:
            fsm_tasks.append(task_file)

    return fsm_tasks


def delete_skill_tasks(task_dir: Path, command_name: str) -> None:
    """Delete tasks matching the invoking skill's command_name."""
    fsm_tasks = find_skill_tasks(task_dir, command_name)

    for task_file in fsm_tasks:
        try:
            task_file.unlink()
            log(f"Deleted FSM task: {task_file.name}")
        except OSError as e:
            error_exit(
                f"Failed to delete task {task_file.name}: {e}. "
                f"Manual cleanup required at {task_dir}/"
            )


def write_tasks(task_dir: Path, tasks: list[dict], command_name: str) -> None:
    """Write task files to the task directory."""
    # Ensure directory exists
    task_dir.mkdir(parents=True, exist_ok=True)

    for task in tasks:
        task_file = build_task_file(task, command_name)
        task_path = task_dir / f"{task_file['id']}.json"

        try:
            with open(task_path, "w") as f:
                json.dump(task_file, f, indent=2)
            log(f"Created task: {task_path.name}")
        except OSError as e:
            error_exit(
                f"Failed to write task {task_path.name}: {e}. "
                f"Manual cleanup required at {task_dir}/"
            )


def main() -> None:
    """Main entry point for the FSM hook."""
    # Parse stdin
    input_data = parse_stdin()
    session_id = input_data["session_id"]
    command_name = input_data["command_name"]
    cwd = input_data["cwd"]

    log(f"Processing skill: {command_name}")

    # Locate fsm.json
    fsm_path = find_fsm_json(command_name, cwd)

    if fsm_path is None:
        # No fsm.json found - no-op
        log("No fsm.json found, skipping task hydration")
        success_response()

    log(f"Found fsm.json: {fsm_path}")

    # Load and validate fsm.json
    tasks = load_fsm_json(fsm_path)
    errors = validate_fsm_tasks(tasks, fsm_path)

    if errors:
        error_exit("Validation failed:\n  " + "\n  ".join(errors))

    # Get task directory
    task_dir = get_task_directory(session_id)

    # Check if re-invocation is safe (active task guard)
    check_active_tasks(task_dir, command_name)

    # Find max ID among preserved tasks (non-matching FSM tasks + manual tasks)

    # Find max ID among preserved tasks (non-matching FSM tasks + manual tasks)
    max_id = find_max_preserved_task_id(task_dir, command_name)

    # Translate IDs
    translated_tasks = translate_ids(tasks, max_id)

    # Delete existing FSM tasks and write new ones
    delete_skill_tasks(task_dir, command_name)
    write_tasks(task_dir, translated_tasks, command_name)

    log(f"Hydrated {len(translated_tasks)} tasks")
    success_response()


if __name__ == "__main__":
    main()
