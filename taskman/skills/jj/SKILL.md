---
name: jj
description: Jujutsu version control system. Use when working with jj repositories, commits, bookmarks, rebasing, conflicts, or git operations in jj context. Triggers on jj commands, revsets, or VCS workflows in jj-managed repos.
---

# Jujutsu (jj)

Git-compatible VCS with cleaner model. Working copy IS a commit (`@`). No staging area. Conflicts stored in commits. Full undo via operation log.

Targets jj **0.40** (see ~/jj/docs for source of truth).

## Changes Are Rarely Lost

jj snapshots the repo state on **every operation**. Botched merge, bad rebase, accidental abandon — the previous state is recoverable for as long as the operation log retains it (default: 2 weeks, pruned by `jj util gc`):

```bash
jj op log              # find the operation before the mistake
jj op restore OP_ID    # restore to that state
```

**Don't assume changes are lost after a failed operation.** Before re-doing work or panicking, check `jj op log` and restore. Caveat: **unsnapshotted** working-copy edits (file changes since the last jj command) aren't in the op log — see [gotchas](patterns/gotchas.md#snapshotting-is-not-automatic).

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
jj rebase -s SRC -d DST  # rebase SRC+descendants onto DST (-d is alias for --onto)
jj abandon REV           # delete commit
jj undo                  # undo last operation
jj op revert [OP]        # revert a specific (non-latest) operation
jj git fetch             # fetch from remotes
jj git push              # push tracking bookmarks in remote_bookmarks(remote)..@
jj git push --bookmark B # push specific bookmark
```

## Core Concepts

### Change ID vs Commit ID
- **Change ID**: Stable 12-letter ID (k-z), survives rewrites. Prefer this.
- **Commit ID**: SHA hash, changes on modification.

### Working Copy = Commit
Working copy is commit `@`. Changes auto-amend it. No staging.

### Bookmarks
Named pointers like git branches, with a different auto-move policy:
- **Follow rewrites**: amending/rebasing the bookmark's commit moves the bookmark automatically (bookmarks track change IDs).
- **Don't follow new children**: `jj new` on top of a bookmark does *not* advance it.

Move manually when extending a branch:
```bash
jj bookmark move NAME --to @
# or auto-pick the closest ancestor bookmark:
jj bookmark advance          # heads(::@ & bookmarks()) → @
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

### `jj workspace update-stale` — use with care

Not actually data-loss prone, but easy to misread. See [patterns/gotchas.md](patterns/gotchas.md#jj-workspace-update-stale) for the full walkthrough. TL;DR: it snapshots current edits onto the stale op, then checks out the desired `@`. Your edits survive — but they now live on a side branch in the op log, which is easy to mistake for "lost".

### Snapshotting Is Not Automatic

jj does NOT snapshot on file changes alone — a jj command must run to trigger it. Run `jj st` periodically after edits to capture intermediate states in the operation log.

### Bookmarks Don't Follow New Children

Bookmarks follow **rewrites** of their target (auto-amend, rebase) but not **new commits on top**:
```bash
jj edit feature
# edits auto-amend feature commit → bookmark moves with it
jj new
# bookmark still on the PARENT, not on the new @
jj bookmark move feature --to @   # or: jj bookmark advance feature
```

### Squash/Rebase Across Workspaces

**Avoid rewriting commits that are ancestors of other workspaces' `@`.** Rewrites the shared commit → other workspaces' working copies become stale, and their descendant commits rebase onto the new version (potential conflicts).

```bash
# RISKY: squash @ into @- if @- is another workspace's ancestor
jj squash                     # rewrites @-

# SAFER: merge via a new commit instead of rewriting
jj new @ feature -m "merge"   # parents untouched
```

Recovery: `jj op log` + `jj op restore <op_id>`, redo as merge.

### Divergent Changes

Same change ID with multiple visible commits. A bare `xyz` errors on divergent changes — disambiguate with `xyz/0`, `xyz/1`. Fix:
```bash
jj abandon xyz/0                       # abandon one side
# or fold one side into the other:
jj squash --from xyz/0 --into xyz/1
# or give one side a fresh change-id:
jj metaedit -r xyz/0 --update-change-id
```

### git push Pushes Tracking Bookmarks

`jj git push` (no args) pushes **tracking bookmarks** in `remote_bookmarks(remote=<remote>)..@`. If nothing in that range is a tracking bookmark, nothing gets pushed. Common pattern:
```bash
jj bookmark create NAME -r @    # or: jj bookmark set NAME -r @
jj git push --bookmark NAME     # also auto-tracks the bookmark (0.38+)
```

### Operation Restore vs Undo vs Revert

- `jj undo` / `jj redo`: undo/redo the last operation
- `jj op revert [OP]`: create a new operation that inverts an earlier one (replaces the removed `jj op undo`)
- `jj op restore OP_ID`: rewind the repo to any point in history

Before assuming changes are lost: check `jj op log`. Unsnapshotted edits are the one exception (see above).

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
