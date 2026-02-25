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

### GAP-70: Manual test procedure references wrong script directory
- **Source**: Implicit Gap Detection-detection
- **Severity**: medium
- **Description**: The manual-test-procedure in .sections/infra.yaml (line 25) instructs testers to invoke 'plugins/finite-skill-machine/scripts/block-skill-internals.sh'. GAP-50 established the correct path as 'plugins/finite-skill-machine/hooks/block-skill-internals.sh' and updated spec.yaml. The .sections file retains 'scripts/' instead of 'hooks/'. The project's plugin pattern places hook scripts in hooks/ alongside hooks.json (visible in the tokamak plugin structure), not in scripts/. A tester following the sectional file would look in the wrong directory. Source: implicit-detection
- **Triage**: delegate
- **Decision**: Deprecate GAP-70. The concern is based on an incorrect premise: GAP-50's outcome text claims it added 'plugins/finite-skill-machine/hooks/block-skill-internals.sh' to the manual-test-procedure, but all codebase evidence confirms the correct path is 'plugins/finite-skill-machine/scripts/block-skill-internals.sh'. The actual script file, hooks.json configuration, project infra.md deployment unit list, and the established plugin directory pattern (hooks/ for configuration, scripts/ for executables) all confirm scripts/ is correct. Both spec.yaml (line 246) and .sections/infra.yaml (line 25) already reference 'scripts/' — there is no discrepancy between the files, and no incorrect path to fix. GAP-50's outcome description is inaccurate but immutable per gap lifecycle principles; the artifact state is authoritative.
- **Primary-file**: spec.yaml

