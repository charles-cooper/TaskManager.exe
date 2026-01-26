Mid-task handoff - save context for your next session.

Usage: `/handoff <agent-slug> [reason]` (e.g., `/handoff alice EOD`, `/handoff feature-x blocked on review`)

1. Update/create handoffs/HANDOFF_<slug>.md with:
   - Current focus (what task, what aspect)
   - Summary: current state, key learnings, next steps
   - Breadcrumbs: pointers to recoverable information
   - Blockers (if any)

2. Update the current task file with:
   - Attempts: what was tried, what failed (approach + outcome only)
   - Notes: **breadcrumbs only** - pointers to recoverable information
   - Budget: update Spent tokens if tracking

3. If you discovered reusable knowledge, save to topics/ (see /remember)

4. Run: taskman sync "handoff: <slug> - <reason>"

5. Update STATUS.md task index only if task status/priority changed (shared state)

## Handoff File Format

```markdown
# HANDOFF: <slug>
updated: YYYY-MM-DD HH:MM

## Focus
Currently working on: TASK_foo.md
Aspect: <specific part>

## Context
<what you were doing, where you left off>

## Next Steps
1. ...
2. ...

## Breadcrumbs
<slug>: <recovery instruction>
```

## Breadcrumb Principle

**Store pointers, not content.** Next session recovers on-demand.

Bad (bloat):
```markdown
The auth flow works like this: [50 lines]
The error was: [20 lines of stack trace]
```

Good (progressive disclosure):
```markdown
auth-flow: src/auth/login.ts:45-80
error-repro: run `make test-auth` (fails line 23)
perf-findings: TOPIC_api.md#latency
```

## Writing Breadcrumbs

Format: `<slug>: <recovery-instruction> [(context)]`

Recovery: file→read, command→bash, url→curl/WebFetch

**What to store inline** (not as breadcrumbs): decisions, key insights, non-reproducible errors.

Goal: next session can reconstruct context efficiently without loading unrelated context / walls of text.

## HOW+WHY > WHAT

Capture reasoning paths, not just conclusions:
- Bad: `fixed the bug`
- Good: `bug-fix: TOPIC_checkpoint.md#sizing (depth off-by-one)`
