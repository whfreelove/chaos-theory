#!/usr/bin/env bash
# Dashboard: show lifecycle status of all OpenSpec changes
# Usage: change_dashboard.sh [--archive] [changes-root]

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CHANGE_STATUS="${SCRIPT_DIR}/change_status.sh"

# --- Parse arguments ---
show_archive=false
changes_root=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --archive)
      show_archive=true
      shift
      ;;
    *)
      changes_root="$1"
      shift
      ;;
  esac
done

[[ -z "$changes_root" ]] && changes_root="openspec/changes"

# --- Build schema name → version cache ---
# Call openspec once, parse with jq, read version from each schema.yaml
schema_json=$(openspec schema which --json --all 2>/dev/null || echo "[]")

version_cache=""
while IFS=$'\t' read -r sname spath; do
  [[ -z "$sname" ]] && continue
  v=$(grep '^version:' "${spath}/schema.yaml" 2>/dev/null | head -1 | sed 's/^version: *//')
  version_cache+="${sname}	${v:--}"$'\n'
done < <(echo "$schema_json" | jq -r '.[] | [.name, .path] | @tsv')

lookup_version() {
  local match
  match=$(echo "$version_cache" | grep "^${1}	" | head -1 | cut -f2)
  echo "${match:--}"
}

# --- Collect change directories ---
change_dirs=()

if [[ -d "$changes_root" ]]; then
  for d in "$changes_root"/*/; do
    [[ -d "$d" ]] || continue
    [[ "$(basename "$d")" == "archive" ]] && continue
    change_dirs+=("$d")
  done
fi

if [[ "$show_archive" == true ]] && [[ -d "${changes_root}/archive" ]]; then
  for d in "${changes_root}/archive"/*/; do
    [[ -d "$d" ]] || continue
    change_dirs+=("$d")
  done
fi

# --- Print table ---
echo "| CHANGE | PROJECT | SCHEMA | VERSION | SPECS-STATUS | CODE-STATUS | CREATED |"
echo "|--------|---------|--------|---------|--------------|-------------|---------|"

# Track projects referenced by active changes (for footer)
active_projects=()

if [[ ${#change_dirs[@]} -eq 0 ]]; then
  echo "No active changes found."
else
  for d in "${change_dirs[@]}"; do
    d="${d%/}"
    name=$(basename "$d")

    project_raw=$("$CHANGE_STATUS" read "$d" project)
    schema=$("$CHANGE_STATUS" read "$d" schema)
    specs_status=$("$CHANGE_STATUS" read "$d" specs-status)
    code_status=$("$CHANGE_STATUS" read "$d" code-status)
    created=$("$CHANGE_STATUS" read "$d" created)

    version=$(lookup_version "$schema")

    if [[ -n "$project_raw" ]]; then
      project=$(basename "$project_raw")
      active_projects+=("$project_raw")
    else
      project="-"
    fi
    [[ -z "$schema" ]] && schema="-"
    [[ -z "$specs_status" ]] && specs_status="-"
    [[ -z "$code_status" ]] && code_status="-"
    [[ -z "$created" ]] && created="-"

    echo "| $name | $project | $schema | $version | $specs_status | $code_status | $created |"
  done
fi

# --- Projects footer ---
openspec_root=$(dirname "$changes_root")
idle_projects=()

if [[ -d "$openspec_root" ]]; then
  for pd in "$openspec_root"/*/; do
    [[ -d "$pd" ]] || continue
    pdname=$(basename "$pd")
    # Skip changes/ and schemas/ — they aren't projects
    [[ "$pdname" == "changes" || "$pdname" == "schemas" ]] && continue

    # Check if any active change references this project
    found=false
    for ap in "${active_projects[@]+"${active_projects[@]}"}"; do
      if [[ "$(basename "$ap")" == "$pdname" ]]; then
        found=true
        break
      fi
    done
    if [[ "$found" == false ]]; then
      idle_projects+=("$pdname")
    fi
  done

  if [[ ${#idle_projects[@]} -gt 0 ]]; then
    echo ""
    IFS=', '; echo "Projects without active changes: ${idle_projects[*]}"
  elif [[ $(ls -1d "$openspec_root"/*/ 2>/dev/null | grep -vcE '(changes|schemas)/') -gt 0 ]]; then
    echo ""
    echo "All projects have active changes."
  fi
fi
