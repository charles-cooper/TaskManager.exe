# TaskManager.exe

Version-controlled task management for AI agents. Agents use familiar file editing tools; versioning and sync happen transparently via [jj (jujutsu)](https://martinvonz.github.io/jj/).

## Problem

AI agents using file-based task systems lose work when:
- Multiple agents edit the same file
- Context resets mid-task and overwrites with stale state
- No history to recover from
- **Agents go in circles** - after context reset, they repeat mistakes because they don't know what was already tried

## Installation

Requires Python 3.11+ and [jj](https://martinvonz.github.io/jj/latest/install/).

```bash
pipx install taskmanager-exe
# or
uvx taskmanager-exe
```

## Quick Start

```bash
# Initialize in your repo
taskman init

# Install MCP server config
taskman install-mcp claude    # or: cursor, codex

# Install Claude Code skills (optional)
taskman install-skills
```

To create a worktree (from main repo):
```bash
taskman wt my-feature    # creates worktrees/my-feature/ + clones .agent-files
```

To add .agent-files to an existing worktree (recovery):
```bash
taskman wt               # clones .agent-files into current directory
```

## How It Works

```
Agent
  │
  ├── Edit tool ────────► .agent-files/ (jj repo)
  │   (file ops)                │
  │                        push/pull
  ├── MCP Server ───────────────┼──────────────────►
  │   (batch/sync)              ▼
  │                     .agent-files.git/ (bare origin)
  └── Skills ───────────────────┘
      (CLI wrapper)
```

- Agents edit files with their normal Edit tool
- jj auto-snapshots every change (no explicit commit needed)
- MCP tools or Skills handle sync and history queries
- Bare git origin serializes concurrent access across worktrees

## CLI Commands

```bash
taskman init                    # create .agent-files.git/ + .agent-files/
taskman wt <name>               # create worktree (from main repo)
taskman wt                      # add .agent-files to existing worktree
taskman install-mcp <agent>     # install MCP config (claude, cursor, codex)
taskman install-skills          # install skill files to ~/.claude/commands/
taskman uninstall-mcp <agent>   # remove MCP config
taskman uninstall-skills        # remove skill files

taskman describe <reason>       # create named checkpoint
taskman sync <reason>           # full sync: describe + fetch + rebase + push
taskman history-diffs <file> <start> [end]    # diffs across revision range
taskman history-batch <file> <start> [end]    # file content at each revision
taskman history-search <pattern> [file] [limit]  # search history

taskman stdio                   # run MCP server (stdio transport)
```

## MCP Tools

When installed via `taskman install-mcp`, these tools are available:

| Tool | Description |
|------|-------------|
| `describe(reason)` | Create named checkpoint |
| `sync(reason)` | Full sync workflow |
| `history_diffs(file, start, end)` | Aggregate diffs across range |
| `history_batch(file, start, end)` | File content at all revisions |
| `history_search(pattern, file, limit)` | Search history for pattern |

## Skills

When installed via `taskman install-skills`, these Claude Code skills are available:

| Skill | Description |
|-------|-------------|
| `/continue` | Resume work - pull + read STATUS.md |
| `/handoff` | Mid-task handoff - sync + detailed context |
| `/complete` | Task done - sync + archive |
| `/describe <reason>` | Create named checkpoint |
| `/sync <reason>` | Full sync workflow |
| `/history-diffs <file> <start> [end]` | Diffs across range |
| `/history-batch <file> <start> [end]` | File content at revisions |
| `/history-search <pattern> [--file] [--limit]` | Search history |

Skills wrap the CLI and work without MCP support.

## Direct jj Commands

Agents can also use jj directly for simple operations:

```bash
jj status                    # current state
jj log                       # view history
jj diff                      # see changes
jj restore --from <rev> <file>  # restore file from revision
```

## Task File Structure

```
.agent-files/
  STATUS.md           # Task index, session state
  LONGTERM_MEM.md     # Architecture (months+)
  MEDIUMTERM_MEM.md   # Patterns, gotchas (weeks)
  tasks/
    TASK_<slug>.md    # Individual tasks
    _archive/         # Completed tasks
```

## Sync Model

Sync at task boundaries:
- `/continue` - session start, pull latest state
- `/handoff` - mid-task, push with detailed context
- `/complete` - task done, push and archive

On conflict, agent resolves with Edit tool, then syncs again.

## License

MIT
