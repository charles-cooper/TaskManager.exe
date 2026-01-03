# TaskManager.exe

Build a task management system for AI agents.

## Problem

AI agents using file-based task systems lose work when:
- Multiple agents edit the same file
- Agent context resets mid-task and overwrites with stale state
- No history to recover from

## Task System Structure

```
.agent-files/
  STATUS.md           # Task index, current session state, blockers, next steps
  LONGTERM_MEM.md     # Architecture knowledge (stable for months)
  MEDIUMTERM_MEM.md   # Patterns, gotchas (stable for weeks)
  HANDOFF_<slug>.md   # Handoff prompts between sessions
  tasks/
    TASK_<slug>.md    # Individual tasks with status, checklist, notes
    _archive/         # Completed tasks
```

**Task file format:**
```markdown
# TASK: <title>

## Meta
Status: planned|in_progress|blocked|complete
Priority: P0|P1|P2
Created: YYYY-MM-DD

## Problem
<what, why>

## Design
<decisions, alternatives>

## Checklist
- [ ] item
- [x] completed item

## Notes
<gotchas>
```

## Requirements

### Core
- Version every file change automatically
- Expose history queries via API (raw git is too heavy, agents forget to use it)
- MCP server (in-process, stdio transport). Recommend FastMCP but open to alternatives.

### API Shape
- `status_update`, `status_history`
- `task_create`, `task_edit`, `task_delete`, `task_history`
- `memory_update`, `memory_history`
- `restore(file, rev)`, `diff(file, rev1, rev2)`

### Backing Store Options

**jj (jujutsu):**
- Working copy is always a commit (automatic snapshotting)
- Simpler model than git (no staging area)

**git:**
- Ubiquitous
- Heavier (commit messages, staging area)

**Alternative:** Each `.agent-files/` is a cloned git repo that agents push/pull. Downside: commit messages and merge conflicts burn tokens.

### Edit Tool Compatibility

Agents know the Edit tool well. Ideal: keep using Edit, get versioning "for free."

Options:
1. MCP tools for everything (agents learn new API)
2. Edit tool + background auto-commit watcher
3. Edit passthrough via MCP
4. Just use git directly (heavy)

### Atomic Batches

Sometimes want multiple files updated as one logical change. Maybe doesn't matter with full history.

## Open Design Questions

1. jj vs git?
2. MCP API for writes, or let agents use Edit?
3. How to surface history to agents who forget to query it?
4. Atomic multi-file commits - needed?
5. What triggers commit? (every write, debounced, explicit)
