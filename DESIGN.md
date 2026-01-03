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
│         (file ops)                (batch/sync ops)              │
│              │                         │                        │
│              ▼                         ▼                        │
│         raw jj commands           compound workflows            │
│              │                         │                        │
│              └────────────┬────────────┘                        │
│                           ▼                                      │
│                    .agent-files/                                │
│                       (jj repo)                                 │
│                           │                                      │
│                      push/pull                                  │
│                           ▼                                      │
│                  .agent-files.git/                              │
│                    (bare origin)                                │
└─────────────────────────────────────────────────────────────────┘
```

**Components:**

1. **Agent**: Uses Edit tool for files, raw jj for simple ops, MCP for batch/compound ops
2. **MCP Server**: FastMCP, in-process, stdio. Only for things that need scripting.
3. **.agent-files/**: jj repo (can be colocated or non-colocated with git)
4. **.agent-files.git/**: Bare git origin for worktree sync

**Why clones instead of jj workspaces?**

jj workspaces share a commit graph immediately (no push/pull). But:
- No natural "source of truth" - all workspaces are peers
- Race conditions when multiple agents sync simultaneously
- Bare origin provides serialization: first push wins, second must pull first
- Explicit sync boundaries via push/pull match our session model

## Repo Structure

```
repo/
├── .agent-files.git/          # bare origin (shared across worktrees)
├── .agent-files/              # jj clone
│   ├── .jj/                   # jj internals (includes git at .jj/repo/store/git)
│   ├── STATUS.md
│   ├── LONGTERM_MEM.md
│   ├── MEDIUMTERM_MEM.md
│   └── tasks/
│       ├── TASK_<slug>.md
│       └── _archive/
├── worktree-a/.agent-files/   # another jj clone
└── worktree-b/.agent-files/   # another jj clone
```

All clones push/pull to `.agent-files.git/`.

**Colocate vs non-colocate:** Either works. Non-colocated repos store git internally at `.jj/repo/store/git`. Push/pull works identically. Colocate only needed if you want git tools to work directly.

## Task File Format

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
<!-- append-only, raw log -->
### Attempt 1 (YYYY-MM-DD HH:MM)
Approach: ...
Result: ...

## Summary
<!-- distilled on handoff, kept lean -->
Current state: ...
Key learnings: ...
Next steps: ...

## Notes
<breadcrumbs, file:line references>
```

## Versioning Model

**jj configuration:**
```toml
[ui]
conflict-marker-style = "git"
```

**Auto-snapshot:** jj snapshots working copy at start of any jj command. No explicit trigger needed.

**Revision syntax:**
- `@` = working copy commit
- `@-` = parent, `@--` = grandparent
- `bookmark..@` = range from bookmark to working copy

## Sync Model

**Sync at task boundaries only:**
- Session start: pull
- `/continue`: pull
- `/handoff`: push
- Task complete: push

**Last handoff tracking:** Agent records in STATUS.md: `Last handoff: <timestamp> (rev <id>)`

## CLI (taskman)

```bash
taskman init                  # create .agent-files.git/ (bare) + .agent-files/ (clone)
taskman wt                    # in worktree: clone from root's .agent-files.git/
taskman install <agent>       # install MCP config for agent (claude, cursor, codex, etc.)
```

## What Agents Use Directly vs MCP

**Use jj directly (no wrapper needed):**
```bash
jj status                           # see current state
jj log                              # view history
jj log -r 'bookmark..@'             # changes since bookmark
jj restore --from <rev> <file>      # restore file
jj op log                           # operation history
jj op restore <id>                  # restore to operation
jj diff                             # see changes
jj git fetch                        # fetch only
jj git push                         # push only
```

**Use MCP tools (need scripting/batching):**
- `describe(reason)` - important checkpoint, ensures snapshot first
- `sync(reason)` - compound: describe + fetch + rebase + push + conflict check
- `history_diffs(file, start, end)` - aggregate diffs across range
- `history_batch(file, start, end)` - fetch multiple file versions
- `history_search(pattern, file, mode)` - search with added/removed modes

## MCP API

```python
@mcp.tool()
async def describe(reason: str) -> str:
    """Create named checkpoint.

    Ensures working copy is snapshotted, then describes current commit.
    Everything since last describe() is one logical unit.

    Args:
        reason: Description of current state

    Returns: Revision ID
    """

@mcp.tool()
async def sync(reason: str) -> str:
    """Full sync: describe, fetch, rebase, push.

    Args:
        reason: Description of changes being synced

    Returns: Status (success, conflicts to resolve, or error)

    If conflicts, returns markers. Agent resolves with Edit, calls sync() again.
    """

@mcp.tool()
async def history_diffs(file: str, start_rev: str, end_rev: str = "@") -> str:
    """Get all diffs for file across revision range.

    Aggregates diffs from multiple revisions in one call.

    Args:
        file: Relative path
        start_rev: Older revision
        end_rev: Newer revision (default: @)

    Returns: Concatenated diffs with revision headers
    """

@mcp.tool()
async def history_batch(file: str, start_rev: str, end_rev: str = "@") -> str:
    """Fetch file content at all revisions in range.

    Returns multiple versions in one call for efficient history search.

    Args:
        file: Relative path
        start_rev: Older revision
        end_rev: Newer revision (default: @)

    Returns: All versions concatenated with revision headers
    """

@mcp.tool()
async def history_search(
    pattern: str,
    file: str = None,
    mode: str = "contains",
    limit: int = 20
) -> str:
    """Search history for pattern.

    Args:
        pattern: Regex to search
        file: Specific file, or None for all
        mode: "contains" | "added" | "removed"
        limit: Max results

    Returns: Matching revisions with context
    """
```

## Sync Protocol

**sync() implementation:**
```
1. jj describe -m "<reason>"     # snapshot + describe
2. jj git fetch                  # get remote changes
3. jj rebase -d main@origin      # rebase onto remote
4. check jj status for conflicts
   - if conflicts: return conflict info, agent resolves, calls sync() again
5. jj git push                   # push to origin
   - if rejected: return error (remote changed, need to sync again)
```

## Conflict Resolution

With `ui.conflict-marker-style = "git"`:

```
<<<<<<< side A
local changes
||||||| base
original content
=======
remote changes
>>>>>>> side B
```

Agent resolves with Edit, calls `sync()` to complete.

## Handoff Types

**handoff_detailed (mid-task):** Comprehensive to avoid repeating mistakes.
- Attempts: what was tried, what failed
- Summary: current state, learnings, next steps
- Notes: breadcrumbs (file:line references)

**handoff_next_task (task complete):** Brief pointer to next task.

**Breadcrumbs principle:** Include enough to reconstruct, not everything.

## Error Handling

Bubble up jj errors to agent. No complex handling - agent decides.

## jj Gotchas

1. **Stale working copy**: If operation interrupted, fix with `jj workspace update-stale`
2. **Conflicted commits in git**: Appear as `.jjconflict-*/` directories
3. **Change IDs**: Stored in non-standard git headers, may not survive pure-git ops
