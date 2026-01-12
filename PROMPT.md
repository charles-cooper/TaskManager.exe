# TaskManager.exe

Build a task management system for AI agents.

## Problem

AI agents using file-based task systems lose work when:
- Multiple agents edit the same file
- Agent context resets mid-task and overwrites with stale state
- No history to recover from
- **Agents go in circles** - after context reset, they repeat the same mistakes because they don't know what was already tried

## Use Cases

### Single agent, single repo
Agent works on tasks, context resets periodically. Need to preserve what was tried.

### Multiple agents, worktrees
Multiple agents work in different git worktrees of same repo. Each has own `.agent-files/` that should sync with others. Agents shouldn't trample each other's work.

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

## Attempts
<!-- append-only log of what was tried -->
### Attempt 1 (YYYY-MM-DD HH:MM)
Approach: ...
Result: ...

## Summary
<!-- distilled on handoff, kept lean -->
Current state: ...
Key learnings: ...
Next steps: ...

## Notes
<gotchas, breadcrumbs>
```

**Effort tracking:** Tasks should support effort estimation using tokens (measurable) rather than time (unmeasurable for agents).

## Requirements

### Core
- Version every file change automatically
- Expose history queries via API (raw git is too heavy, agents forget to use it)
- MCP server (in-process, stdio transport). Recommend FastMCP but open to alternatives.
- Agents should keep using Edit tool for file ops (familiar, low friction)

### Handoff Requirements

Need two handoff modes with different verbosity:
- **Mid-task handoff**: Comprehensive context to avoid next session repeating mistakes
- **Task complete handoff**: Brief pointer to next task (avoid memory bloat)

### Breadcrumbs Principle

Don't include all context in handoffs. Include enough that a clean session can reconstruct what's needed - references with short summaries, not full content.

### Backing Store Options

**jj (jujutsu):**
- Working copy is always a commit (automatic snapshotting)
- Simpler model than git (no staging area)

**git:**
- Ubiquitous
- Heavier (commit messages, staging area)

**Alternative:** Each `.agent-files/` is a cloned repo that agents push/pull. Downside: commit messages and merge conflicts burn tokens.

### Edit Tool Compatibility

Agents know the Edit tool well. Ideal: keep using Edit, get versioning "for free."

Options:
1. MCP tools for everything (agents learn new API)
2. Edit tool + background auto-commit watcher
3. Edit passthrough via MCP
4. Just use git directly (heavy)

## Open Design Questions

1. jj vs git?
2. MCP API for writes, or let agents use Edit?
3. How to surface history to agents who forget to query it?
4. Atomic multi-file commits - needed?
5. What triggers commit? (every write, debounced, explicit)
6. Worktree sync model - workspaces vs clones?
