---
name: validate-specs
description: Use when OpenSpec artifacts need validation before proceeding. Use after creating or updating functional.md, technical.md, specs, or tasks.yaml.
---

# Artifact Validation

Validates OpenSpec artifacts through critique and resolution workflow.

## Workflow

1. Invoke `tokamak:critique-specs` skill
2. Invoke `tokamak:resolve-gaps` skill
