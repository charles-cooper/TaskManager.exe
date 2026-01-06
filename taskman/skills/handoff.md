Mid-task handoff - save detailed context for next session.

1. Update the current task file with:
   - Attempts: what was tried, what failed (brief - just approach + outcome)
   - Summary: current state, key learnings, next steps
   - Notes: **breadcrumbs only** - pointers to recoverable information

2. Run: taskman sync "handoff: $ARGUMENTS"

3. Update STATUS.md with handoff context (brief pointer to task file)

## Breadcrumb Principle

**Store pointers, not content.** The next session can recover information on-demand.

Bad (context pollution):
```markdown
## Notes
The authentication flow works like this:
[50 lines of code]
The error message was:
[20 lines of stack trace]
```

Good (progressive disclosure):
```markdown
## Notes
auth-flow: src/auth/login.ts:45-80
error-repro: run `make test-auth` (fails on line 23)
prev-diff: jj diff -r @--
related-issue: github.com/org/repo/issues/123
```

## Writing Breadcrumbs

Format: `<slug>: <recovery-instruction> [(context)]`

Recovery: file→Read, command→Bash, url→WebFetch

**Store inline** (not as breadcrumbs): decisions, key insights, non-reproducible errors.

Goal: next session reconstructs context in 2-3 tool calls, not by reading walls of text.
