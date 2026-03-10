---
name: jj
description: Jujutsu version control system. Use when working with jj repositories, commits, bookmarks, rebasing, conflicts, or git operations in jj context. Triggers on jj commands, revsets, or VCS workflows in jj-managed repos.
---

# Jujutsu (jj)

Git-compatible VCS with cleaner model. Working copy IS a commit (`@`). No staging area. Conflicts stored in commits. Full undo via operation log.

## Changes Are Never Lost

jj snapshots the repo state on **every operation**. Botched merge, bad rebase, accidental abandon — the previous state is always recoverable:

```bash
jj op log              # find the operation before the mistake
jj op restore OP_ID    # restore to that state
```

**NEVER assume changes are lost after a failed operation.** Before re-doing work or panicking, check `jj op log` and restore. See [patterns/gotchas.md](patterns/gotchas.md) (Operation Restore vs Undo) for details.

## Quick Reference

```bash
jj st                    # status
jj log                   # history
jj new [REV]             # new commit on REV
jj commit -m "msg"       # finalize @ + new working copy
jj describe -m "msg"     # set message (any commit with -r)
jj edit REV              # make REV the working copy
jj squash                # fold @ into parent
jj split                 # split @ interactively
jj diff                  # show changes
jj rebase -s SRC -d DST  # rebase SRC+descendants onto DST
jj abandon REV           # delete commit
jj undo                  # undo last operation
jj git fetch             # fetch from remote
jj git push --bookmark B # push bookmark B
```

## Core Concepts

### Change ID vs Commit ID
- **Change ID**: Stable 12-letter ID (k-z), survives rewrites. Prefer this.
- **Commit ID**: SHA hash, changes on modification.

### Working Copy = Commit
Working copy is commit `@`. Changes auto-amend it. No staging.

### Bookmarks
Named pointers like git branches but **don't auto-move**. Always:
```bash
jj bookmark move NAME --to @
```

### Revision Shortcuts
```
@       working copy
@-      parent
@--     grandparent
::@     ancestors
@::     descendants
main..@ between main and @
```

## Detailed Reference

**Commands**: See [reference/commands.md](reference/commands.md) for full command documentation

**Revsets**: See [reference/revsets.md](reference/revsets.md) for revset operators and functions

**Git Interop**: See [reference/git-interop.md](reference/git-interop.md) for git clone, fetch, push workflows

**Conflicts**: See [reference/conflicts.md](reference/conflicts.md) for conflict markers and resolution

**Configuration**: See [reference/config.md](reference/config.md) for settings and config files

## Patterns & Workflows

**Common Workflows**: See [patterns/workflows.md](patterns/workflows.md) for git-to-jj translation and common patterns

## Gotchas

### update-stale Clobbers Unsaved Edits

`jj workspace update-stale` resets the working directory to match `@` **without snapshotting first**. If you have unsaved edits and the working copy became stale, they are **permanently lost**.

Dangerous sequence:
1. Edit files in working copy
2. `@` moves via `--ignore-working-copy` or another workspace (no snapshot taken)
3. `jj workspace update-stale` → **edits gone, unrecoverable**

**Mitigation**: Always `jj st` before operations that might cause staleness. This triggers a snapshot, making edits recoverable via `jj op restore`.

### Snapshotting Is Not Automatic

jj does NOT snapshot on file changes alone — a jj command must run to trigger it. Run `jj st` periodically after edits. Without this, intermediate states are lost and `update-stale` or workspace switches will clobber them.

### Bookmarks Don't Auto-Move

Unlike git branches, jj bookmarks stay put. Always move explicitly:
```bash
jj bookmark move feature --to @
```

### Squash/Rebase Across Workspaces

**NEVER squash or rebase commits that are ancestors of other workspaces.** Rewrites shared history → conflict cascade through every descendant.

```bash
# WRONG: squash branch into shared ancestor
jj squash --from feature      # rewrites @- → conflicts everywhere

# CORRECT: merge via new commit
jj new @ feature -m "merge"   # parents untouched
```

Recovery: `jj op log` + `jj op restore <op_id>`, redo as merge.

### Divergent Changes

Same change ID with multiple visible commits. Fix:
```bash
jj abandon xyz                # abandon one
# or
jj squash -r xyz/0 --into xyz/1  # merge them
```

### git push Requires Bookmarks

`jj git push` without bookmarks is a no-op. Create/move bookmark first:
```bash
jj bookmark create NAME -r @
jj git push --bookmark NAME
```

### Operation Restore vs Undo

- `jj undo`: last operation only
- `jj op restore OP_ID`: any point in history

**NEVER assume changes are lost.** Check `jj op log` first.

See [patterns/gotchas.md](patterns/gotchas.md) for extended gotchas (immutable commits, large files, conflict resolution, etc.)

## Git Translation (Quick)

```bash
git status       → jj st
git diff         → jj diff
git commit -a    → jj commit -m "msg"
git commit --amend → jj squash
git stash        → jj new @-
git checkout -b  → jj new main && jj bookmark create NAME
git rebase       → jj rebase -s SRC -d DST
git log --graph  → jj log
```

## Help

```bash
jj help              # general
jj help COMMAND      # command help
jj help -k revsets   # topics: revsets, templates, filesets, config
```
