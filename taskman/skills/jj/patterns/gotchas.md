# Edge Cases & Gotchas

## Bookmarks Don't Auto-Move

Unlike git branches, jj bookmarks stay put when you create commits.

```bash
# WRONG expectation:
jj edit feature
jj new                        # bookmark still on old commit!

# CORRECT:
jj edit feature
# ... work ...
jj bookmark move feature --to @   # explicit move
```

Always move bookmarks explicitly after commits.

## Divergent Changes

Same change ID with multiple visible commits. Shows as:
```
◆  xyz (divergent)
│ ◆  xyz (divergent)
```

**Causes:**
- Concurrent edits in different workspaces
- `jj duplicate` without abandoning original
- Certain rebase scenarios

**Fix:**
```bash
jj abandon xyz                # abandon one
# or
jj squash -r xyz/0 --into xyz/1  # merge them
# or give new identity
jj describe -r xyz/0 --reset-author --no-edit
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

- `jj commit -m "msg"`: Finalizes current changes AND creates new empty working copy
- `jj new`: Creates new empty commit, current changes stay in @-

```bash
# If you want to "save" current state and continue:
jj commit -m "msg"            # @ is now new empty commit

# If you want to start fresh leaving current alone:
jj new @                      # @ is new, @- has your work
```

## Squash Direction

`jj squash` moves changes INTO parent (or --into target).

```bash
jj squash                     # @ contents → @- (parent)
jj squash --into REV          # @ contents → REV
```

To move parent INTO current (opposite direction):
```bash
jj squash -r @-               # @- contents → @
```

## Operation Restore vs Undo

- `jj undo`: Undoes last operation only
- `jj op restore OP_ID`: Restores to any point in history

```bash
jj op log                     # find operation ID
jj op restore abc123          # restore to that state
```

## Change ID vs Commit ID in Commands

Most commands accept both, but behavior differs on rewrite:
- Change ID: Points to current version after rewrites
- Commit ID: Points to specific (possibly obsolete) version

Prefer change IDs for ongoing work.
