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

**Sync at task boundaries:**
- `/continue` - session start, pull latest state
- `/handoff` - mid-task, push with detailed context
- `/complete` - task done, push and archive

**Last handoff tracking:** Agent records in STATUS.md: `Last handoff: <timestamp> (rev <id>)`

## CLI (taskman)

```bash
# Setup
taskman init                  # create .agent-files.git/ (bare) + .agent-files/ (clone)
taskman wt <name>             # create worktrees/<name>/ with git worktree + jj clone
taskman install-mcp <agent>   # install MCP config (claude, cursor, codex)
taskman install-skills        # install skill files to ~/.claude/commands/

# Operations (used by both MCP and skills)
taskman describe <reason>                     # create checkpoint
taskman sync <reason>                         # full sync workflow
taskman history-diffs <file> <start> [end]    # diffs across range
taskman history-batch <file> <start> [end]    # versions across range
taskman history-search <pattern> [file] [limit]  # search history

# MCP server
taskman stdio                 # run MCP server (stdio transport)
```

## Dual Interface: MCP + Skills

Both interfaces call the same CLI commands:

```
┌─────────────┐     ┌─────────────┐
│  MCP tools  │     │   Skills    │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └───────┬───────────┘
               ▼
        taskman CLI
               │
               ▼
         jj commands
```

**MCP Server**: Calls `taskman` subprocess, returns output
**Skills**: Markdown prompts that run `taskman` via Bash

Same operations available either way. MCP preferred when available (typed params, structured errors), skills as fallback.

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
- `history_search(pattern, file, limit)` - search using jj's `diff_contains()` revset

## Code Architecture

```
taskman/
├── core.py      # Core logic (describe, sync, history_*)
├── jj.py        # jj command utilities
├── server.py    # MCP server (imports core)
└── cli.py       # CLI (imports core)

~/.claude/commands/
├── continue.md      # Skill: resume work
├── handoff.md       # Skill: mid-task handoff
├── complete.md      # Skill: task done
├── describe.md      # Skill: runs `taskman describe`
├── sync.md          # Skill: runs `taskman sync`
├── history-diffs.md # Skill: runs `taskman history-diffs`
└── ...
```

```
┌─────────────────┐     ┌─────────────┐
│   MCP server    │     │    CLI      │
│   (in-process)  │     │ (subprocess)│
└────────┬────────┘     └──────┬──────┘
         │ import              │ import
         └──────────┬──────────┘
                    ▼
              taskman/core.py
                    │
                    ▼
              taskman/jj.py
                    │
                    ▼
               jj commands
                    ↑
            Skills (bash) ─── taskman CLI
```

MCP imports core directly (no subprocess overhead). Skills call CLI via bash.

## MCP API

Thin wrappers around sync core functions. FastMCP handles exceptions as tool errors automatically.

```python
from mcp.server.fastmcp import FastMCP
from taskman import core

mcp = FastMCP("taskman")

@mcp.tool()
def describe(reason: str) -> str:
    """Create named checkpoint."""
    return core.describe(reason)

@mcp.tool()
def sync(reason: str) -> str:
    """Full sync: describe, fetch, rebase, push."""
    return core.sync(reason)

@mcp.tool()
def history_diffs(file: str, start_rev: str, end_rev: str = "@") -> str:
    """Get all diffs for file across revision range."""
    return core.history_diffs(file, start_rev, end_rev)

@mcp.tool()
def history_batch(file: str, start_rev: str, end_rev: str = "@") -> str:
    """Fetch file content at all revisions in range."""
    return core.history_batch(file, start_rev, end_rev)

@mcp.tool()
def history_search(pattern: str, file: str = None, limit: int = 20) -> str:
    """Search history for pattern in diffs."""
    return core.history_search(pattern, file, limit)
```

## Skills

Skill files call CLI (which imports core):

**describe.md:**
```markdown
Run: taskman describe "$ARGUMENTS"
```

**sync.md:**
```markdown
Run: taskman sync "$ARGUMENTS"
If conflicts, resolve with Edit, then run again.
```

**history-diffs.md / history-batch.md / history-search.md:**
```markdown
Run: taskman <command> $ARGUMENTS
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

**`/handoff` (mid-task):** Comprehensive to avoid repeating mistakes.
- Attempts: what was tried, what failed
- Summary: current state, learnings, next steps
- Notes: breadcrumbs (file:line references)

**`/complete` (task done):** Brief, archives the task.
- Mark task complete, move to _archive/
- Pointer to next task (if any)

**Breadcrumbs principle:** Include enough to reconstruct, not everything.

## Error Handling

Bubble up jj errors to agent. No complex handling - agent decides.

## jj Gotchas

1. **Stale working copy**: If operation interrupted, fix with `jj workspace update-stale`
2. **Conflicted commits in git**: Appear as `.jjconflict-*/` directories
3. **Change IDs**: Stored in non-standard git headers, may not survive pure-git ops

## MCP Configuration Locations

**Claude Code:**
- Global: `~/.claude.json`
- Project: `.mcp.json`
- Format: JSON with `mcpServers` key

```json
{
  "mcpServers": {
    "taskman": {
      "type": "stdio",
      "command": "taskman",
      "args": ["stdio"]
    }
  }
}
```

**Cursor:**
- Global: `~/.cursor/mcp.json`
- Project: `.cursor/mcp.json`
- Format: JSON with `mcpServers` key (same structure as Claude)

**Codex:**
- Global: `~/.codex/config.toml`
- Format: TOML with `mcp_servers` key (underscore, not hyphen)

```toml
[mcp_servers.taskman]
command = "taskman"
args = ["stdio"]
```
