# Gaps

<!-- GAP TEMPLATE:
### GAP-XX: Title
- **Source**: <kebab-case with type suffix, e.g., functional-critic, implicit-detection>
- **Severity**: high|medium|low
- **Description**: ...
- **Triage**: check-in|delegate|defer-release|defer-resolution (added by resolve workflow)
- **Decision**: ... (added by resolve workflow)

CRITIQUE adds: ID, Source, Severity, Description
RESOLVE adds: Triage, Decision

New gaps from critique should NOT have Triage or Decision fields.

See tokamak:managing-spec-gaps for triage and status semantics.
-->

### GAP-67: Denial Given clauses use imprecise FSM_BYPASS taxonomy
- **Source**: Implicit Gap Detection-detection
- **Severity**: medium
- **Description**: SCN-denial-grep (line 60), SCN-denial-contains-bypass-instructions (line 75), and SCN-denial-removes-plugin-advice (line 83) in .sections/requirements.yaml use 'FSM_BYPASS is not set' in their Given clauses. GAP-47 established a two-term taxonomy: 'not present in the shell environment' vs 'exported as an empty string.' GAP-58 updated all three clauses to 'FSM_BYPASS is not present in the shell environment' in spec.yaml, but .sections/requirements.yaml was not updated. 'Not set' is ambiguous — it could mean 'not present' (correct) or 'not assigned a value' (which includes empty string, conflating with SCN-bypass-empty-string's distinct precondition). An implementer could use a check that treats unset and empty-string identically, undermining the scenario separation established by GAP-13 and GAP-47. Same divergence class as GAP-64/65/66. Source: implicit-detection
- **Triage**: delegate
- **Decision**: Replace 'FSM_BYPASS is not set' with 'FSM_BYPASS is not present in the shell environment' in three Given clauses in .sections/requirements.yaml: SCN-denial-grep (line 60), SCN-denial-contains-bypass-instructions (line 75), and SCN-denial-removes-plugin-advice (line 83). Aligns the sectional file with the corrected spec.yaml text established by GAP-58. 'Not set' is ambiguous — it could mean 'not present' or 'not assigned a value' (including empty string). The precise taxonomy term 'not present in the shell environment' distinguishes unambiguously from 'exported as an empty string', preserving the scenario separation established by GAP-13 and GAP-47. Same divergence class and resolution pattern as GAP-64, GAP-65, and GAP-66.
- **Primary-file**: .sections/requirements.yaml

### GAP-68: INT-deny-response lacks JSON example in sectional file
- **Source**: Implicit Gap Detection-detection
- **Severity**: medium
- **Description**: INT-deny-response in .sections/technical.yaml documents fields using dot notation (hookSpecificOutput.permissionDecision, etc.) alongside a flat systemMessage field, but provides no concrete JSON object showing the nesting structure. GAP-55 (high severity) identified that field paths conflicted with verification preamble references, and its resolution added an example JSON object to spec.yaml showing systemMessage at root level and hookSpecificOutput as a nested object. The .sections/technical.yaml was not updated with this example, leaving the same structural ambiguity that GAP-55 was created to resolve — an implementer reading the sectional file could place systemMessage inside hookSpecificOutput or permissionDecision at root level. Source: implicit-detection
- **Triage**: delegate

### GAP-69: CMP routing mechanism omitted from sectional technical file
- **Source**: Implicit Gap Detection-detection
- **Severity**: medium
- **Description**: CMP-block-skill-internals responsibilities in .sections/technical.yaml (line 32-33) say 'Extract target path from tool-specific input fields (file_path for Read, pattern for Glob, path for Grep) and pattern-match against protected file names' but do not specify how the script determines which tool type is invoking it. GAP-57 expanded this responsibility in spec.yaml to 'Determine tool type via tool_input key presence (not tool_name) and extract the target path from the matched field.' The .sections file was not updated. An implementer reading only the sectional file has no indication that tool_name-based routing is incorrect and could implement it, causing the per-tool field extraction to select the wrong field when tool_name does not align with tool_input key structure. Source: implicit-detection
- **Triage**: delegate

### GAP-70: Manual test procedure references wrong script directory
- **Source**: Implicit Gap Detection-detection
- **Severity**: medium
- **Description**: The manual-test-procedure in .sections/infra.yaml (line 25) instructs testers to invoke 'plugins/finite-skill-machine/scripts/block-skill-internals.sh'. GAP-50 established the correct path as 'plugins/finite-skill-machine/hooks/block-skill-internals.sh' and updated spec.yaml. The .sections file retains 'scripts/' instead of 'hooks/'. The project's plugin pattern places hook scripts in hooks/ alongside hooks.json (visible in the tokamak plugin structure), not in scripts/. A tester following the sectional file would look in the wrong directory. Source: implicit-detection
- **Triage**: delegate
- **Decision**: Deprecate GAP-70. The concern is based on an incorrect premise: GAP-50's outcome text claims it added 'plugins/finite-skill-machine/hooks/block-skill-internals.sh' to the manual-test-procedure, but all codebase evidence confirms the correct path is 'plugins/finite-skill-machine/scripts/block-skill-internals.sh'. The actual script file, hooks.json configuration, project infra.md deployment unit list, and the established plugin directory pattern (hooks/ for configuration, scripts/ for executables) all confirm scripts/ is correct. Both spec.yaml (line 246) and .sections/infra.yaml (line 25) already reference 'scripts/' — there is no discrepancy between the files, and no incorrect path to fix. GAP-50's outcome description is inaccurate but immutable per gap lifecycle principles; the artifact state is authoritative.
- **Primary-file**: spec.yaml
