## Linear Integration

This repo's issues are tracked in Linear under team **WHF**. Your assigned project is in `.claude/linear-project`.

### Your Project

**Before any Linear interaction**, read `.claude/linear-project` (line 1 = project slug, line 2 = project name). Do not list issues or query the team without reading this file first. If the file does not exist, you have no project assigned — ask the user.

View your project and its latest updates:

```bash
linear project view <project-id>
linear project-update list <project-id>
```

### Your Issues

List issues for your assigned project:

```bash
linear issue list --team WHF --project "<project name>" --sort priority --no-pager
```

### Before Starting an Issue

View the issue to check for instructions from the PM:

```bash
linear issue view WHF-<id>
```

Look for comments prefixed with `@agent:` — these are directives from the PM. Follow them before proceeding.

### When You Finish an Issue

First, re-read the issue (`linear issue view WHF-<id>`) and verify each acceptance criterion or checklist item against what you actually built. Do not claim completion without checking.

You **cannot** update issue state — your API token is scoped to read + create comments only. Do not attempt `linear issue update`. Instead, comment on the issue with the `@pm:` prefix — **the PM only sees comments that start with `@pm:`**:

```bash
linear issue comment add WHF-<id> --body "@pm: Done — implemented X, Y, Z. PR #<n>."
```

Comments without the `@pm:` prefix will be missed. The PM agent will update the issue state after reading your comment.

### When You're Blocked

If you need a decision, clarification, or are stuck on something outside your scope, comment on the issue:

```bash
linear issue comment add WHF-<id> --body "@pm: Blocked — need clarification on the auth flow."
```

Keep it to one comment. If the PM replies and you need to respond again, that's the limit — after 2 turns, tell the user to handle it directly in the PM session.

After an escalation is resolved, the PM will post a summary comment with the decision and next steps. Check for `@agent:` comments before resuming work.

### Gotchas

- `--sort` is required on `issue list` — use `--sort priority`
- Use `--no-pager` on `issue list` to prevent interactive output
- The flag is `--state`, not `--status` (e.g. `--state backlog`, `--state started`)
- **Do not use `linear issue update`** — your token cannot update issues. Comment with `@pm:` instead.
- **Never commit `.claude/linear-project`** — it is worktree-local and should be excluded via global gitignore. If you see it staged or tracked, unstage it with `git reset HEAD .claude/linear-project`. If it keeps appearing, ask the user to add `.claude/linear-project` to their global gitignore (`~/.config/git/ignore`)
