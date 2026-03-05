Manage git worktrees with jj workspaces for .agent-files.

`.agent-files/` is a single jj repo (see SKILL.md#Architecture). Each project worktree gets its own jj workspace — a separate working copy of the same repo. Commits are visible across workspaces via `jj log` (no push/pull), but must be merged to combine changes.

## Create Worktree

Run: `taskman wt $ARGUMENTS`

- No arguments: create jj workspace in current directory (for existing worktrees)
- `taskman wt <name>`: create worktree + jj workspace for existing branch `<name>`
- `taskman wt <name> --new`: create worktree + new branch + jj workspace at `worktrees/<name>/`

## List Worktrees

Run: `taskman wt-list`

Shows all worktrees with health status:
- `git:ok` / `git:orphaned` / `git:missing`
- `jj-ws:ok` / `jj-ws:orphaned` / `jj-ws:missing`
- `bm:exists` (bookmark present)

Orphaned = entry exists but path is gone.

## Remove Worktree

Run: `taskman wt-rm <name> [--force]`

Cleans up:
1. Removes git worktree (`git worktree remove`)
2. Forgets jj workspace (`jj workspace forget`)
3. **Auto-merges** changes into default workspace
4. Deletes bookmark on clean merge

**Must run from outside the target worktree.** If in worktree, command errors with exact cd command to run.

Use `--force` for git worktrees with uncommitted files.

After `wt-rm`, intelligently merge .agent-files from the removed worktree:
- Review conflicts (don't blindly `--ours`/`--theirs`)
- Combine STATUS.md task lists, keep all active tasks
- Merge memory files (MEDIUMTERM/LONGTERM), dedupe, keep all learnings
- Preserve all attempt records in TASK_*.md
- For HANDOFF_*.md, keep newer context but check older for unique info

## Resolving Merge Conflicts

Merge conflicts are **common** in .agent-files because multiple sessions edit the same files (STATUS.md, MEDIUMTERM_MEM.md, etc).

**⚠️ DO NOT use `--ours` or `--theirs` blindly - you WILL lose accumulated knowledge.**

### Resolution process

```bash
cd .agent-files
jj resolve            # interactive resolution
# OR edit conflict markers manually
jj diff               # verify result
jj describe -m "resolved conflicts from wt-<name>"
```

### Guidelines by file type

**STATUS.md**: Merge task lists from both sides. Keep all active tasks, update completion status.

**MEDIUMTERM_MEM.md / LONGTERM_MEM.md**: Combine entries from both sides. Dedupe if identical. Keep all learnings - can prune later.

**HANDOFF_*.md**: Usually one side is newer - keep the more recent context, but check for unique info in older version.

**TASK_*.md**: Merge attempt histories, checklists. Don't lose any attempt records.

### Principle

**Err on the side of keeping information.** Duplicate content is easy to prune later. Lost knowledge is gone forever.

## Prune Orphans

Run: `taskman wt-prune`

Automatically cleans up orphaned state:
- Stale git worktree entries (path deleted manually)
- jj workspaces with missing working copies
- Bookmarks matching orphaned workspaces

Use after manual `rm -rf worktrees/<name>/` or partial cleanup.
