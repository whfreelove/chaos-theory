---
name: init-schemas
description: Initialize OpenSpec schemas in the current project. Copies bundled chaos-theory schemas from the ct plugin.
---

# Initialize OpenSpec Schemas

## Step 1: Check for existing schemas

```bash
ls openspec/schemas/ 2>/dev/null | head -1
```

## Step 2: Handle existing schemas

If Step 1 shows files exist, use AskUserQuestion:

- Question: "Existing schemas found at openspec/schemas/. Overwrite them?"
- Options:
  - "Overwrite" - Continue with copy
  - "Cancel" - Stop and report "Schemas unchanged"

## Step 3: Run the copy script

If no existing schemas OR user confirmed overwrite:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/init-schemas.sh" --force
```

The `--force` flag skips the script's interactive prompt since we already confirmed via AskUserQuestion.
