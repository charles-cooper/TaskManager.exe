# TaskManager.exe Design

## Overview

A version-controlled task management system for AI agents. Agents use familiar file editing tools; versioning and sync happen transparently via jj (jujutsu).

**Design philosophy:** Dumb store + automation for things agents forget. Intelligence is wielded by the agent, not baked into the system.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Agent                                    │
│                           │                                      │
│              ┌────────────┴────────────┐                        │
│              ▼                         ▼                        │
│         Edit tool                 MCP Server                    │
│         (file ops)                (history/sync)                │
│              │                         │                        │
│              └────────────┬────────────┘                        │
│                           ▼                                      │
│                    .agent-files/                                │
│                    (jj + git colocate)                          │
│                           │                                      │
│                      push/pull                                  │
│                           ▼                                      │
│                  .agent-files.git/                              │
│                    (bare origin)                                │
└─────────────────────────────────────────────────────────────────┘
```

**Components:**

1. **Agent**: Uses Edit tool for file modifications, MCP tools for history/sync
2. **MCP Server**: FastMCP, in-process, stdio. Wraps jj commands.
3. **.agent-files/**: Working clone (jj + git colocate)
4. **.agent-files.git/**: Bare origin at repo root for worktree sync

## Repo Structure

**Single repo (no worktrees):**
```
repo/
├── .agent-files.git/          # bare origin
├── .agent-files/              # working clone
│   ├── STATUS.md
│   ├── LONGTERM_MEM.md
│   ├── MEDIUMTERM_MEM.md
│   └── tasks/
│       ├── TASK_<slug>.md
│       └── _archive/
└── <project files>
```

**With worktrees:**
```
repo/
├── .agent-files.git/          # bare origin (shared)
├── .agent-files/              # clone for root
├── worktree-a/
│   └── .agent-files/          # clone
└── worktree-b/
    └── .agent-files/          # clone
```

All clones push/pull to `.agent-files.git/`. Symmetric model - no special cases.

## Task File Format

```markdown
# TASK: <title>

## Meta
Status: planned|in_progress|blocked|complete
Priority: P0|P1|P2
Created: YYYY-MM-DD
Completed: YYYY-MM-DD (when done)

## Problem
<what, why, user impact>

## Design
<decisions, alternatives rejected>

## Checklist
- [ ] item
- [x] completed item

## Attempts
<!-- append-only, raw log of what was tried -->
### Attempt 1 (YYYY-MM-DD HH:MM)
Approach: ...
Result: ...

## Summary
<!-- distilled on handoff, rewritten to stay lean -->
Current state: ...
Key learnings: ...
Next steps: ...

## Notes
<gotchas, breadcrumbs, file references>
```

**Attempts vs Summary:**
- **Attempts**: Raw, append-only. Agent logs what they try as they go.
- **Summary**: Distilled on handoff. Compressed learnings, kept lean.

Agent writes both. Version history is safety net for bad distillation.

## Versioning Model

**jj with git colocate:**
- jj for working copy model (auto-snapshot)
- git for push/pull to bare origin
- `--colocate` means jj and git share .git directory

**Auto-snapshot behavior:**
- jj snapshots working copy on any jj command
- No explicit trigger needed
- Agent edits files → next MCP call triggers snapshot as side effect

**Named commits:**
- `describe(reason)` creates named checkpoint
- Everything between describe() calls is one logical unit (implicit batching)
- No explicit "atomic batch" API needed

## Sync Model

**Sync at task boundaries only:**
- Session start: pull
- `/continue`: pull
- `/handoff`: push
- Task complete: push

Mid-session work is local only. Conflicts are rare (different agents on different tasks).

**Last handoff tracking:**
- Agent records in STATUS.md: `Last handoff: <timestamp> (rev <id>)`
- No jj bookmarks or magic files needed
- `/continue` reads STATUS.md to find what changed since

## CLI (taskman)

```bash
taskman init                  # create .agent-files.git/ (bare) + .agent-files/ (clone)
taskman wt                    # in worktree: clone from root's .agent-files.git/

taskman install claude        # install MCP config for Claude Code
taskman install cursor        # install for Cursor
taskman install codex         # install globally (codex doesn't support per-project)
taskman install <agent>       # etc.
```

**MCP server installation:**
- Per-project by default (in-process server)
- Global install for agents that don't support per-project (e.g., codex)

## MCP API

### History Queries

```python
@mcp.tool()
async def history_log(file: str = None, limit: int = 50) -> str:
    """Get commit log summary for navigation.

    Args:
        file: Relative path, or None for all files
        limit: Max revisions to show

    Returns: List of revisions with timestamps, messages, files changed.
    """

@mcp.tool()
async def history_batch(file: str, start_rev: str, end_rev: str = "@") -> str:
    """Fetch file content at all revisions in range.

    Args:
        file: Relative path
        start_rev: Older revision
        end_rev: Newer revision (default: current)

    Returns: All versions in range, concatenated with revision headers.
    Efficient for agent to search through many versions in one call.
    """

@mcp.tool()
async def history_diffs(file: str, start_rev: str, end_rev: str = "@") -> str:
    """Get diffs for a file across revision range.

    Args:
        file: Relative path
        start_rev: Older revision
        end_rev: Newer revision (default: current)

    Returns: Concatenated diffs with revision headers.
    More compact than full versions for tracing changes.
    """

@mcp.tool()
async def history_search(
    pattern: str,
    file: str = None,
    mode: str = "contains",
    limit: int = 20
) -> str:
    """Search history for pattern (regex).

    Args:
        pattern: Regex to search for
        file: Specific file, or None for all files
        mode: "contains" | "added" | "removed"
        limit: Max results

    Returns: Matching revisions with context snippets
    """

@mcp.tool()
async def history_restore(file: str, rev: str) -> str:
    """Restore file to previous revision.

    Args:
        file: Relative path
        rev: jj revision spec

    Returns: Confirmation with new content preview
    """

# TABLED: history_at(file, revisions: list[str])
# Agent can use jj/git show directly for single file at specific revision.
# MCP value is batching; single fetches don't need wrapper.
```

### Versioning Operations

```python
@mcp.tool()
async def describe(reason: str) -> str:
    """Create named checkpoint with description.

    Call to mark meaningful state. Everything since last describe()
    is grouped as one logical unit.

    Args:
        reason: Description of current state

    Returns: Revision ID
    """

@mcp.tool()
async def sync(reason: str) -> str:
    """Describe, pull, resolve conflicts, push.

    Args:
        reason: Description of changes being synced

    Returns: Sync status (success, conflicts to resolve, or error)

    If conflicts exist, returns conflict markers for agent to resolve.
    Agent edits files to resolve, then calls sync() again.
    """
```

### Handoff Operations

```python
@mcp.tool()
async def handoff_detailed(task: str) -> str:
    """Prepare detailed handoff for mid-task context switch.

    Use when stopping mid-task. Agent should populate:
    - Attempts section: what was tried, what failed
    - Summary section: current state, key learnings, next steps
    - Notes section: breadcrumbs (file:line references)

    System provides recent change summary to help agent write handoff.

    Args:
        task: Task slug (e.g., "foo" for TASK_foo.md)

    Returns: Handoff checklist and recent activity summary
    """

@mcp.tool()
async def handoff_next_task(completed_task: str, next_task: str) -> str:
    """Brief handoff after task completion.

    Use when task is done. Keeps context minimal.

    Args:
        completed_task: Task just finished
        next_task: Task to work on next

    Returns: Confirmation
    """
```

## Sync Protocol

### Pull (session start, /continue)

```
1. jj git fetch
2. jj rebase -d main@origin
3. If conflicts:
   - Leave conflict markers in files
   - Return list of conflicted files
   - Agent resolves with Edit
   - Agent calls sync() to retry
```

### Push (/handoff, task complete)

```
1. jj describe -m "<reason>"
2. jj git push
3. If rejected (remote ahead):
   - Pull first
   - Retry push
```

## Conflict Resolution

jj conflict markers in files:

```
<<<<<<<
local changes
%%%%%%%
=======
remote changes
>>>>>>>
```

Agent sees on next file read, resolves with Edit, calls `sync()` to complete.

## Handoff Types

### handoff_detailed (mid-task)

For stopping mid-task. Comprehensive to avoid next session repeating mistakes.

Agent populates:
- **Attempts**: What was tried, what failed, why
- **Summary**: Current state, key learnings, recommended next steps
- **Notes**: Breadcrumbs (file:line references, relevant commits)

**Breadcrumbs principle:** Include enough context to reconstruct, not everything. References with short summaries, not full content.

### handoff_next_task (task complete)

For moving to next task. Brief to avoid memory bloat.

- Mark current task complete
- Update STATUS.md with next task
- Minimal context (next task file has what's needed)

## Context Injection on /continue

When agent runs `/continue`:

1. Pull latest from origin
2. Read STATUS.md to find current task and last handoff timestamp
3. Auto-inject into prompt:
   - Task file content (including Summary section)
   - Changes since last handoff (from jj log)
   - Any unresolved conflicts
4. Agent has full context to resume

## Error Handling

Bubble up jj errors to agent. No complex error handling - agent decides how to proceed.

## Open Questions

- Exact jj revision syntax for API (@ vs HEAD vs commit IDs) - need to verify jj docs
- MCP server config file format for different agents
