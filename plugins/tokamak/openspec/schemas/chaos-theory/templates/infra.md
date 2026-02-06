## Context

<!-- Current infrastructure state relevant to this deployment.
Reference existing topology, environments, SLAs.
DO NOT propose infrastructure changes here - those belong in technical.md. -->

## Objectives

<!-- Measurable operational outcomes for THIS change.
Format: `OBJ-<slug>`: <outcome statement>
Examples: deployment success criteria, test coverage targets, latency validation -->

## Deployment

<!-- How this change deploys to EXISTING infrastructure.
Environment configs, feature flags, rollout sequence.

Use Mermaid to show deployment FLOW (not topology changes):
- Which services get updated in what order
- Feature flag rollout stages
- Environment promotion path -->

## Testing Strategy

<!-- Integration and E2E testing approach for THIS change.
Unit testing belongs in technical.md.

- Test environments: where E2E tests run
- Test data: seeding, isolation, cleanup
- Requirements coverage: which @slug:Y.Z scenarios become E2E tests
- CI/CD integration: when tests run, what blocks deployment -->

## Observability

<!-- Logging, metrics, alerts for NEW components in this change.
Not infrastructure-wide observability changes.

- New log events and their levels
- New metrics and dashboard panels
- Alert thresholds and runbook links -->

## Migration

<!-- OPTIONAL. Include only if this change requires careful deployment sequencing.

- Rollout strategy (canary, blue-green, feature flag)
- Rollback triggers and procedure
- Data migration steps if applicable -->
