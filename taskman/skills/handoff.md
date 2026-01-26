Mid-task handoff - save detailed context for next session.

1. Update the current task file with:
   - Attempts: what was tried, what failed (approach + outcome only)
   - Summary: current state, key learnings, next steps
   - Notes: **breadcrumbs only** - pointers to recoverable information
   - Budget: update Spent tokens if tracking

2. If you discovered reusable knowledge, save to topics/ (see /remember)

3. Run: taskman sync "handoff: $ARGUMENTS"

4. Update STATUS.md with handoff context (brief pointer to task file)

## Breadcrumb Principle

**Store pointers, not content.** Next session recovers on-demand.

Bad (bloat):
```markdown
## Notes
The auth flow works like this:
[50 lines]
The error was:
[20 lines of stack trace]
```

Good (progressive disclosure):
```markdown
## Notes
auth-flow: src/auth/login.ts:45-80
error-repro: run `make test-auth` (fails line 23)
perf-findings: TOPIC_api.md#latency
```

## Writing Breadcrumbs

Format: `<slug>: <recovery-instruction> [(context)]`

Recovery: file→read, command→bash, url→curl/WebFetch

**What to store inline** (not as breadcrumbs): decisions, key insights, non-reproducible errors.

Goal: next session can reconstruct context efficiently without loading unrelated context / walls of text

## HOW+WHY > WHAT

Capture reasoning paths, not just conclusions:
- Bad: `fixed the bug`
- Good: `bug-fix: TOPIC_checkpoint.md#sizing (depth off-by-one)`
