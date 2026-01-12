---
name: taskman
description: Agent memory and task management CLI. Use this skill when you need to persist context across sessions, track tasks, hand off work, or store temporary agent scratch data. Provides the `taskman` CLI for init, sync, describe, and history operations.
---

# Taskman

Version-controlled agent memory and task management. The `.agent-files/` directory is scratch space for ANY agent work that should persist across sessions - task tracking, memory, handoffs, notes, or temporary files.

## Structure

```
.agent-files/
  STATUS.md           # Task index, current session state
  LONGTERM_MEM.md     # Architecture knowledge (months+)
  MEDIUMTERM_MEM.md   # Patterns, gotchas (weeks)
  tasks/
    TASK_<slug>.md    # Active tasks
    _archive/         # Completed tasks
  (any other scratch files)
```

**STATUS.md**: Operational state - task index, current focus, blockers, next steps. Update, don't overwrite.

**LONGTERM_MEM.md**: System architecture, component relationships. Rarely changes.

**MEDIUMTERM_MEM.md**: Reusable patterns and gotchas. NOT session logs.

**Task files**: One per user-facing work unit. Use checklist items for sub-work.

**Scratch space**: Store any temporary agent work here - it's version-controlled separately from the main repo.

## Progressive Disclosure

Store breadcrumbs (pointers), not content. Recover on-demand via Read/Bash/WebFetch.

```
<slug>: <recovery-instruction>
```

Examples: `auth-flow: src/auth/login.ts:45-80` | `build-status: run `make build`` | `prev-attempt: jj diff -r @--`

Store inline only: decisions, key insights, non-reproducible errors.

See `/handoff` for writing breadcrumbs, `/continue` for expanding them.

## Commands

| Command | Use when |
|---------|----------|
| /continue | Resuming work from a previous session |
| /handoff | Saving context mid-task for next session |
| /complete | Finishing and archiving a task |
| /sync | Syncing .agent-files with origin |
| /describe | Creating a named checkpoint |
| /history-search | Searching history for patterns |
| /history-diffs | Viewing diffs across revisions |
| /history-batch | Fetching file content at revisions |
| /wt | Setting up .agent-files in a git worktree |

When a command is invoked, read the corresponding `.md` file in this skill directory for detailed instructions.

## jj Snapshotting

jj does NOT auto-snapshot on file changes alone. A jj command must be run to trigger a snapshot. Run `jj st` periodically (after edits or batches of edits) to capture history. Without this, intermediate states are lost.

## Important

`.agent-files/` should never be committed. Add it to `.gitignore`.
