Mid-task handoff - save context for your next session.

Usage: `/handoff <agent-slug> [reason]` (e.g., `/handoff alice EOD`, `/handoff feature-x blocked on review`)

1. Use /remember skill and update memories/topics as applicable

2. Batch context loading before writing:
   - Read STATUS.md, the current task file, relevant topics, and existing handoff files together
   - Decide all memory/task/handoff updates before editing
   - Apply independent edits/writes in as few tool calls as possible so related state stays consistent

3. Update/create handoffs/HANDOFF_<slug>.md with:
   - Current focus (what task, what aspect)
   - Summary: current state, key learnings, next steps
   - Breadcrumbs: pointers to recoverable information
   - Blockers (if any)
   - IMPORTANT: Preserve all user intent from this and previous sessions — goals, preferences, constraints, corrections — and use judgment as to how to frame it. Make sure to phrase it in a way which is preserved across automated handoffs.

4. Update the current task file with:
   - Attempts: what was tried, what failed (approach + outcome only)
   - Notes: **breadcrumbs only** - pointers to recoverable information
   - Budget: update Spent tokens if tracking

5. If you discovered reusable knowledge, save to topics/ (see /remember)

6. If there are handoff files that are obsolesced (e.g., the handoff from the beginning of the session that has been superseded by a new handoff that you just created), move them to _archive/ and update in STATUS index

7. Run: taskman sync "handoff: <slug> - <reason>"

8. Update STATUS.md task index only if task status/priority changed (shared state)


## Handoff File Format

```markdown
# HANDOFF: <slug>
updated: YYYY-MM-DD HH:MM
commit: <sha or jj change-id>
focus: TASK_foo.md - <aspect>

## context
<what you were doing, where you left off>

## next
1. ...

## breadcrumbs
<slug>: <instruction>
```

The `commit:` field anchors the handoff to a specific repo state. Use `git rev-parse --short HEAD` or `jj log -r @ --no-graph -T 'change_id.short()'`.

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
