# Common Workflows

## Git to jj Translation

| Git | jj |
|-----|-----|
| `git status` | `jj st` |
| `git diff` | `jj diff` |
| `git diff --staged` | (not needed - no staging) |
| `git add -p && commit` | `jj split` or `jj commit -i` |
| `git commit` | `jj commit -m "msg"` |
| `git commit --amend` | `jj squash` or just edit (auto-amends) |
| `git commit --amend -p` | `jj squash -i` |
| `git stash` | `jj new @-` (creates sibling) |
| `git stash pop` | `jj edit STASHED` then `jj squash` |
| `git checkout -b topic` | `jj new main` (+ `jj bookmark create`) |
| `git switch branch` | `jj edit COMMIT` |
| `git rebase B A` | `jj rebase -b A -d B` |
| `git reset --hard` | `jj abandon` (commit) / `jj restore` (files) |
| `git reset --soft HEAD~` | `jj squash` |
| `git cherry-pick` | `jj duplicate REV -o @` (--onto) |
| `git revert` | `jj revert -r REV` |
| `git log --graph` | `jj log` |
| `git blame` | `jj file annotate PATH` |
| `git reflog` | `jj op log` |
| `git rebase -i` (reorder) | `jj arrange` (TUI, 0.39+) or `jj rebase -r C -B/-A B` |

## Starting New Work

```bash
jj new main                   # start on main
# ... work ...
jj describe -m "feat: thing"  # add message
jj bookmark create feature -r @
jj git push --bookmark feature
```

## "Stash" and Switch Context

```bash
# "Stash" current work
jj new @-                     # current becomes sibling, you're on parent

# Work on something else
jj new other-commit

# Return to stashed work
jj edit STASHED_CHANGE_ID
```

## Amend Any Commit (Not Just HEAD)

```bash
# Option 1: Edit directly
jj edit ANCESTOR
# make changes (auto-amends)
jj new                        # back to new commit

# Option 2: New commit then squash
jj new ANCESTOR
# make changes
jj squash                     # fold into ancestor
# descendants auto-rebased
```

## Split a Commit

```bash
jj split                      # interactive, current commit
jj split -r REV               # split specific commit
```

## Reorder Commits

```bash
# A-B-C-D → A-C-B-D (move C before B)
jj rebase -r C -B B           # --insert-before (alias: --before)

# A-B-C-D → A-B-D-C (move C after D)
jj rebase -r C -A D           # --insert-after  (alias: --after)

# Or interactively (0.39+):
jj arrange [REVSETS]          # TUI to reorder/abandon/swap commits
```

## Extract Commit from Middle

```bash
# A-B-C-D, extract B to put elsewhere
jj rebase -r B -d elsewhere   # B moved, C now on A
```

## Create Merge Commit

```bash
jj new A B                    # merge A and B
```

## Undo Anything

```bash
jj undo                       # undo last operation
jj op log                     # see history
jj op restore OP_ID           # restore to any point
```

## PR Workflow

```bash
# Initial PR
jj new main
# ... work ...
jj describe -m "feat: thing"
jj bookmark create feature -r @
jj git push --bookmark feature  # auto-tracks the bookmark (0.38+)
# create PR on GitHub

# Address review (in-place amend)
jj edit feature               # if not already there
# edits auto-amend feature's commit; bookmark follows the rewrite — no manual move needed
jj git push --bookmark feature  # force-with-lease semantics

# Address review (stack a new commit first, then fold)
jj new feature
# ... fixups ...
jj squash                     # fold into feature; bookmark follows
jj git push --bookmark feature
```

## Keep Branch Updated with Main

```bash
jj git fetch
jj rebase -b feature -d main@origin
jj bookmark move feature --to @
jj git push --bookmark feature
```

## Working on Multiple Features

```bash
# Create features as siblings
jj new main
jj describe -m "feature A"
jj bookmark create feat-a -r @

jj new main                   # another branch from main
jj describe -m "feature B"
jj bookmark create feat-b -r @

# Switch between them
jj edit feat-a
jj edit feat-b
```
