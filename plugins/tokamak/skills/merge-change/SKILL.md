---
name: merge-change
description: Merge change artifacts into project documentation with lifecycle tracking. Use when specs are ratified and ready to merge.
---

# merge-change

Apply completed change artifacts into existing project-level documentation.

## When to Use

When `specs-status` is `ratified` or `merging`, merge the change's artifacts (functional.md, requirements, technical.md, infra.md, integration.feature.md) into the project's living documentation. The PreToolUse hook validates this state; the PostToolUse hook auto-transitions `ratified → merging` on invocation.

## Inputs

**Input**: `$0` is the change name. If empty, check conversation context.

- **Change path**: Derived as `openspec/changes/<change-name>/`
- **Project path**: Read from `.openspec.yaml` `project` field — a bare directory name resolved under `openspec/` (set during `new-change`)

If not provided, detect from context:
- Change path: most recently ratified or in-progress change
- Project path: fall back to directory matching the project name under `openspec/`

## Step 0: Validate state and resolve project

Read `specs-status` and verify it is `ratified` or `merging` (redundant with hook gate, but serves as instruction-level safety):

```bash
current=$("${CLAUDE_PLUGIN_ROOT}/scripts/change_status.sh" read "openspec/changes/$0" specs-status)
```

If not `ratified` or `merging`, inform the user what state the change is in and what needs to happen first. The PostToolUse hook auto-transitions `ratified → merging` on skill invocation, so by the time this runs, status will be `merging`.

Read the project path from `.openspec.yaml`:

```bash
project=$("${CLAUDE_PLUGIN_ROOT}/scripts/change_status.sh" read "openspec/changes/$0" project)
```

If empty, fall back to context detection (scan `openspec/` for a directory matching the change context). If ambiguous, ask the user. Use the resolved project path throughout the merge process.

## Process

1. Read change artifacts to determine which files have substantive content
2. Dispatch one Sonnet subagent per artifact type that has changes (use Task tool with `model: "sonnet"`)
3. Each subagent reads: change artifact + existing project artifact + merge rules below
4. Each subagent writes: updated project artifact
5. Present summary of all changes to user for review

### Subagent Dispatch Pattern

```
Task tool (sonnet):
  description: "Merge <artifact-type> into project"
  prompt: |
    Read the change artifact at <change-path>/<file>
    Read the existing project artifact at <project-path>/<file>
    Apply the merge rules below, then write the updated file.

    CRITICAL: When transferring names, identifiers, slugs, tags, or code references
    from source artifacts, copy them exactly. Never reconstruct from memory.

    [artifact-specific merge rules from below]
```

Dispatch all subagents in parallel — they operate on independent files.

If merge rules require user triage (e.g., Out of Scope items), the orchestrating agent must complete triage BEFORE dispatching the affected subagent. Ask each triage item individually — never batch multiple items into one question.

## Merge Rules by Artifact Type

### functional.md

Read the change's functional.md and the project's functional.md.

- **Capabilities**: New capabilities from the change → append to project Capabilities list
- **Scope**: Change scope additions → append to project Scope section
- **Out of Scope**: (individual question per item) Triage each item with the user; NEVER ASK MULTIPLE OUT-OF-SCOPE ITEMS IN ONE QUESTION:
  - Permanent boundary → add to project Out of Scope
  - Temporary gap → add to project Current Limitations
  - Future intent → add to project Planned Future Work
- **Known Risks**: Change risks → append to project Known Risks. Remove risks that the change resolved.
- **Overview**: Integrate change "What Changes" content into project Overview. The project Overview describes the full system, not just the latest change.
- **Current Limitations**: Review change for resolved limitations → remove from project Current Limitations

### requirements (per capability file)

Read the change's `requirements/<slug>/requirements.feature.md` and the project's equivalent.

- **ADDED rules/scenarios**: Append to project's `## Requirements` section under the matching Feature
- **MODIFIED rules/scenarios**: Replace the matching `@slug:Y` or `@slug:Y.Z` block in the project file with the updated version from the change
- **REMOVED rules**: Delete the matching `@slug:Y` block from the project file
- **RENAMED rules**: Update `@slug` tags throughout the project file

If the change adds a new capability (new file), create the project file from the template and populate with the ADDED content.

Strip delta headers (ADDED/MODIFIED/REMOVED/RENAMED) — project files use flat `## Requirements` structure.

### technical.md

Read the change's technical.md and the project's technical.md.

- **Context**: Merge relevant context additions. Remove outdated context.
- **Objectives**: Change objectives may not be project objectives. Only add if they represent permanent system goals. Most change objectives are transient.
- **Architecture diagrams**: Update to reflect the new system state. Diagrams should show current architecture, not change diffs.
- **Components**: New components → append. Modified components → update in place.
- **Interfaces**: New interfaces → append. Modified interfaces → update in place.
- **Decisions**: Append new decisions with `[change-slug]` provenance tag. Do not modify existing decisions — they are historical records.
- **Risks**: Append new risks. Remove risks that the change mitigated.

### infra.md

Read the change's infra.md and the project's infra.md.

- **Deployment**: Merge deployment changes into project Deployment section. Update environment configs, rollout strategy to reflect current state.
- **Testing Strategy**: Add new test patterns and coverage mappings. Update the requirements coverage table with new `@slug:Y.Z` entries.
- **Observability**: Append new logging, metrics, and alert definitions.
- **Migration**: Do NOT merge migration content — it's change-specific, not project-level.

### integration.feature.md

Read the change's integration.feature.md and the project's equivalent.

Apply same rules as requirements:
- **ADDED scenarios**: Append to project's `## Integration Scenarios` section
- **MODIFIED scenarios**: Replace matching `@integration:Y.Z` block
- **REMOVED scenarios**: Delete matching block

Strip delta headers. Project file uses flat `## Integration Scenarios` structure.

## Edge Cases

### First merge into empty project

If the project directory doesn't exist or a specific artifact file is missing:
1. Create from the project schema template (greenfield or brownfield)
2. Then apply the change content as if merging into an empty document
3. The subagent receives: template + change artifact

### Change modifies unknown capability

If a change modifies a capability not present in project docs:
- Flag to user: "Change modifies `<slug>` which doesn't exist in project docs"
- Ask: create it from the change content, or skip?

### Change removes a capability

If a change removes a capability entirely:
- Confirm with user before removing from all project docs
- Remove: capability from functional.md, requirements file, component/interface references in technical.md, coverage mappings in infra.md

### Conflicting content

If the change contradicts existing project docs (e.g., a decision that conflicts with an existing one):
- Flag the conflict to the user
- Present both versions
- Let the user decide which to keep

## Verification

After all subagents complete:
1. Confirm all dispatched subagents wrote their files
2. Read back every updated project artifact (read all files in parallel in one message)
3. Cross-check each updated artifact against the original change artifact:
   - Verify names, identifiers, slugs, and tags were transcribed exactly (not paraphrased or substituted)
   - Verify no content from the change was dropped or truncated
   - Verify no content from the existing project artifact was accidentally removed
   - Verify delta headers (ADDED/MODIFIED/REMOVED/RENAMED) were stripped where required
4. If any discrepancy is found, fix the file directly — do not re-dispatch a subagent
5. Present a summary: which files were updated, key changes per file, any corrections made in step 4
6. Ask user to review before considering the merge complete

## Completion

After the user approves the merge, write the terminal status:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/change_status.sh" write "openspec/changes/$0" specs-status merged
```

Report the new state and suggest next steps based on `code-status`:
- If `code-status: implemented` or `n/a` → both tracks terminal, suggest `Skill(tokamak:archive-change, args: "$0")`
- If `code-status: ready` or `in-progress` → suggest `Skill(tokamak:implement-change, args: "$0")` to complete implementation first
