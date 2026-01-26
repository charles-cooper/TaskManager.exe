---
name: taskman
description: Agent memory and task management CLI. Use this skill when you need to persist context across sessions, track tasks, hand off work, or store temporary agent scratch data. Provides the `taskman` CLI for init, sync, describe, and history operations.
---

# Taskman

Version-controlled agent memory and task management. The `.agent-files/` directory is **local scratch space** for agent work that persists across sessions - task tracking, memory, handoffs, notes, or temporary files. It is tracked separately from the main repo and should NEVER be referenced from tracked files or commit messages.

## Structure

```
.agent-files/
  STATUS.md           # Task index, current session state
  LONGTERM_MEM.md     # Architecture knowledge (months+)
  MEDIUMTERM_MEM.md   # Patterns, learnings, index for memory topics
  topics/
    TOPIC_<slug>.md   # Topic-specific knowledge (agent-organized)
  tasks/
    TASK_<slug>.md    # Active tasks
    _archive/         # Completed tasks
```

**STATUS.md**: Operational state - task index, current focus, blockers, next steps.

**LONGTERM_MEM.md**: System architecture, component relationships. Rarely changes.

**MEDIUMTERM_MEM.md**: Reusable patterns and learnings. Index pointing to topics. NOT session logs

**topics/**: Topic files. Agent organizes as needed. Use TOPIC_<slug>.md for findability.

**Task files**: One per user-facing work unit. See Task Format below.

## Topic-Based Memory

MEDIUMTERM_MEM.md should be an index, not a dump. When content grows:
- Extract related entries to topics/TOPIC_<slug>.md
- Keep MEDIUMTERM as index + cross-cutting patterns only

### Topic File Format

Agent-optimized, dense:

```markdown
# <topic>
updated: YYYY-MM-DD

## <entry>
problem: <one line>
fix: <one line>
check: <command to verify>
refs: <file:line, other.md#section>
```

Agents can adapt structure as needed. The key properties:
- **Dense**: keywords over prose (`problem:` not "The problem we encountered was...")
- **Validation paths**: `check:` field - how to verify this still holds
- **Refs**: Enable reconstruction, not just reference

### Index Format

```markdown
# Memory Index

## Topics
| slug | description | updated |
|------|-------------|---------|
| jj-gotchas | jj CLI pitfalls | 2024-01-26 |

## Cross-Cutting
<patterns spanning topics - keep lean>
```

### Example Organizations

Agents can create subdirectories as needed:

```
topics/
  TOPIC_jj_gotchas.md       # flat - simple topics
  TOPIC_release_workflow.md
  
  perf/                     # grouped - related investigations
    TOPIC_checkpoint_sizing.md
    TOPIC_api_latency.md
  
  reviews/                  # council/subagent outputs
    TOPIC_api_redesign.md
  
  design/                   # design explorations, prototypes
    TOPIC_new_sync_model.md
  
  decisions/                # architectural decision records
    TOPIC_async_vs_sync.md
```

Example groupings (not prescriptive - organize however makes sense):
- `perf/` - benchmarks, optimization experiments
- `reviews/` - council outputs, code review findings
- `design/` - design explorations, API sketches, prototypes
- `decisions/` - why we chose X over Y
- `bugs/` - root cause analyses, postmortems

Heuristic: keep flat until 5+ related files, then group.

## Task Format

```markdown
# TASK: <title>

## Meta
Status: planned|in_progress|blocked|complete
Priority: P0|P1|P2
Created: YYYY-MM-DD
Completed: YYYY-MM-DD

## Problem
<what, why>

## Design
<decisions, alternatives rejected>

## Checklist
- [ ] item
- [x] completed item

## Attempts
### Attempt N (YYYY-MM-DD HH:MM)
Approach: ...
Result: ...

## Summary
Current state: ...
Key learnings: ...
Next steps: ...

## Notes
<breadcrumbs - pointers to recoverable info>

## Budget (optional)
Estimate: <tokens> (planning: X, impl: Y, validation: Z)
Variance: low|med|high
Intervention: autonomous|checkpoints|steering|collaborative
Spent: <tokens>
```

Budget uses tokens (measurable) not time. Variance = estimate spread (low=tight, high=wide). Intervention = human engagement pattern, not duration.

**Scratch space**: .agent-files/ can store any temporary agent work - it's version-controlled separately from the main repo.

## Progressive Disclosure

**Store pointers, not content.** Recover on-demand via read/bash/curl.

Format: `<slug>: <recovery-instruction>`

Examples:
- `auth-flow: src/auth/login.ts:45-80`
- `build-status: run make build`
- `prev-attempt: jj diff -r @--`
- `issue: github.com/org/repo/issues/123` (curl/WebFetch)

**HOW > WHAT**: Breadcrumbs should enable reconstruction, not just reference.
- Bad: `fixed checkpoint bug`
- Good: `checkpoint-bug: TOPIC_perf.md#sizing (off-by-one in depth calc)`

**Include validation paths**: How to verify a conclusion still holds.

**Store inline only**: Decisions, key insights, non-reproducible errors.

See `/handoff` for writing breadcrumbs, `/continue` for expanding them.

## Commands

| Command | Use when |
|---------|----------|
| /continue | Resuming work from a previous session |
| /handoff | Saving context mid-task for next session |
| /remember | Persisting learnings to memory/topics |
| /compact | Memory maintenance, pruning, reorganizing |
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

`.agent-files/` is local scratch space, tracked separately from the main repo.

- Add `.agent-files/` to `.gitignore`
- **NEVER reference .agent-files content from tracked files or commit messages**
- Treat as untracked local work - may contain session-specific context, internal task names, or scratch notes that don't belong in the project history
