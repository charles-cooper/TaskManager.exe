# Edge Cases & Gotchas

## `jj workspace update-stale`

Not data-destroying, but easy to misread. Here's what it actually does (see `cli/src/cli_util.rs::recover_stale_working_copy` in jj 0.40):

1. Load the repo at the working copy's **last known op** (the stale one).
2. **Snapshot the current working-copy contents onto that stale op** → any unsaved edits are captured as a commit on the stale branch of the op graph.
3. Reload the repo at the current head op (where `@` was moved, e.g. by another workspace).
4. Update files on disk to match the desired `@`.
5. Snapshot again (picks up any git refs etc.).

If the working copy's last op was garbage-collected (`jj op abandon` + `jj util gc`), step 1 falls back to `create_and_check_out_recovery_commit`, which parents your current files onto the current op's wc commit. Still no data loss.

**With `snapshot.auto-update-stale = true`**, any snapshotting command triggers the same path automatically.

### How not to misread `jj op log` after update-stale

The op log afterwards has a branching shape:
```
@  <update-stale op>           <- your desired @ now checked out
├─╮ <snapshot on stale op>   <- YOUR EDITS landed here
│ │
│ ╯ <old stale op>           <- the op the working copy was stuck on
│
╰── <current head op>         <- where @ had been moved to
```
`jj op log` renders the full DAG by default, but with many ops the side branch scrolls off. Follow the graph edges — the branch merging back into `@` is the snapshot op that holds your edits.

### Recovery

- To inspect the captured edits: `jj --at-op=<snapshot-op-id> diff` or `jj --at-op=<snapshot-op-id> log`.
- To get them back: `jj op restore <snapshot-op-id>` then cherry-pick / merge into the desired `@`.
- To just abandon the stale branch: `jj undo` right after update-stale rewinds it.

### When to prefer manual recovery instead

If the divergence is large or confusing, it's often cleaner to:
1. `jj op log` to find a known-good op **before** the concurrent move.
2. `jj op restore OP_ID` to roll back.
3. Re-apply intended changes explicitly.



## Snapshotting Is Not Automatic

jj only snapshots the working copy when a jj command runs. File saves, editor autosaves, external tools — none trigger a snapshot. Run `jj st` periodically to capture intermediate states. For scripts, `jj util snapshot` triggers a snapshot without other side effects (replaces the undocumented `jj debug snapshot`, deprecated in 0.39).

## Bookmark Auto-Move: Follows Rewrites, Not New Children

Unlike git branches (which follow HEAD), jj bookmarks bind to a **change ID**:

- **Auto-moves** when the commit is rewritten in place (editing @, amend, rebase, squash-into).
- **Does NOT follow** when you run `jj new` to create a child.

```bash
# Auto-move (rewrite): bookmark stays pinned to the change as it evolves
jj edit feature
# ... edits auto-amend feature's commit → bookmark moves with it

# No auto-move (new child): bookmark is left on the parent
jj new feature                     # bookmark `feature` stays on @-, not @
jj bookmark move feature --to @    # move it yourself
# or
jj bookmark advance feature        # advance closest ancestor bookmark to @
```

Also: deleting a bookmarked commit (via `jj abandon`) deletes the bookmark. Use `jj abandon --retain-bookmarks` to move them to the parent instead.

## Divergent Changes

Same change ID with multiple visible commits. Shows as:
```
◆  xyz (divergent)
│ ◆  xyz (divergent)
```

Find them all with `jj log -r 'divergent()'`. A bare change-id revset errors on a divergent change; disambiguate with `xyz/0`, `xyz/1` ("change offset") syntax.

**Causes:**
- Concurrent edits in different workspaces
- `jj duplicate` without abandoning original
- Certain rebase scenarios

**Fix:**
```bash
jj abandon xyz/0                        # abandon one side
# or fold one side into the other:
jj squash --from xyz/0 --into xyz/1
# or give one side a fresh change-id so they stop colliding:
jj metaedit -r xyz/0 --update-change-id
```

## Conflicted Bookmarks

Shows as `main??`. Happens when local and remote diverge unexpectedly.

```bash
# See conflict
jj bookmark list

# Fix by choosing version
jj bookmark move main --to main@origin  # take remote
# or
jj bookmark move main --to LOCAL_REV    # take local
```

## Immutable Commits Error

```
Error: Commit XXXXX is immutable
```

Default immutable: trunk, tags, untracked remote bookmarks.

**Fix:**
```bash
jj --ignore-immutable COMMAND  # override once

# Or configure:
# [revset-aliases]
# 'immutable_heads()' = 'trunk()'  # less restrictive
```

## Empty Commits Are Normal

Commits with no file changes are valid. Most merge commits appear "empty" (diff vs auto-merged parents).

```bash
jj log -r 'empty()'           # find them if needed
jj abandon EMPTY_REV          # remove if unwanted
```

## Large File Limit

Default 1MB limit for new files (anti-footgun).

```
Error: New file PATH is too large
```

**Fix:**
```bash
# In config:
# [snapshot]
# max-new-file-size = "10MiB"

# Or track specifically:
jj file track PATH
```

## Git HEAD Detached

In colocated repos, git shows "detached HEAD". This is **normal** for jj.

If you need to run git commands:
```bash
git switch --detach           # acknowledge detached state
# or
git switch main               # temporarily attach
```

## Working Copy Conflicts

Conflict markers in files are materialized view. jj tracks conflict state internally.

**Don't:**
- Just delete markers and expect resolution
- Edit markers without squashing

**Do:**
```bash
# Edit file to resolve
jj squash                     # update internal state
# or
jj resolve                    # use merge tool
```

## Restore vs Abandon

- `jj restore`: Reverts file content (from parent or --from REV)
- `jj abandon`: Deletes entire commit

```bash
jj restore PATH               # revert specific files
jj abandon @                  # delete current commit entirely
```

## Commit vs New

- `jj commit -m "msg"`: Describes current `@` and creates a new empty child (like `jj describe + jj new`). Bookmarks do NOT move forward.
- `jj new`: Creates a new empty child commit; whatever was on `@` stays at `@-`.

```bash
# Save current state and continue with a fresh wc commit:
jj commit -m "msg"            # @ is now a new empty commit; previous state at @-

# Start a sibling leaving @ alone:
jj new @-                     # @ is new, previous work is at sibling
```

## Squash Direction

The `-r`, `--from`, and `--into` flags all have specific meanings. Mixing them up is a common mistake.

```bash
jj squash                     # @ contents → @-   (default: --from @ --into @-)
jj squash --into REV          # @ contents → REV  (must be an ancestor of @)
jj squash -r REV              # REV contents → REV's parent
jj squash --from SRC          # SRC contents → @
jj squash --from SRC --into DST   # SRC contents → DST
```

There is no `jj squash -r @-` shortcut for "pull @- into @". Use `--from @- --into @`.

## Squash/Rebase Across Workspaces

**Avoid rewriting commits that are ancestors of another workspace's `@`.** Rewriting a shared ancestor changes its commit ID; other workspaces' descendants get auto-rebased onto the new version (may conflict), and their working copies become stale.

```bash
# RISKY: rewrites @- if @- is a shared ancestor
jj squash                        # default --into @-
jj squash --into @-              # same
jj edit @- && <edits>            # amends @-

# SAFER: merge via a new commit (no ancestor is rewritten)
jj new @ feature -m "merge"      # new merge commit
jj bookmark set default -r @
```

**Rule: prefer merge commits over rewrites of shared ancestors when multiple workspaces exist.**

Recovery: `jj op log` + `jj op restore <op_id>` to before the rewrite, then redo as a merge.

## Operation Restore vs Undo vs Revert

- `jj undo` / `jj redo`: undo/redo the *last* operation (LIFO).
- `jj op revert [OP]`: create a **new** operation that applies the inverse of an earlier one. Later operations stay; replaces the removed `jj op undo` (0.39).
- `jj op restore OP_ID`: rewind the repo state to that operation, discarding everything after.
- `jj --at-op=OP_ID <cmd>`: run a read-only command as if at that op (no snapshot).

```bash
jj op log                     # find operation ID; shows full op DAG, incl. divergent branches;
                              # workspace name shown (0.40+)
jj op restore abc123          # rewind
jj op revert abc123           # invert just that one op, preserving later ops
```

Default op-log retention is **2 weeks**; `jj util gc` prunes older ops + their unreachable objects.

## Change ID vs Commit ID in Commands

Most commands accept both, but behavior differs on rewrite:
- Change ID: Points to current version after rewrites
- Commit ID: Points to specific (possibly obsolete) version

Prefer change IDs for ongoing work.
