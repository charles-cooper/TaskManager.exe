# Commands Reference

## Status & Viewing

```bash
jj st                       # status
jj diff                     # diff of @
jj diff -r REV              # diff of specific commit
jj diff --from A --to B     # diff between commits
jj show REV                 # full commit details
jj log                      # history (default view)
jj log -r REVSET            # filtered history
jj log -r ::@               # ancestors (like git log)
jj log -r 'all()'           # everything
jj evolog                   # evolution of @ across rewrites
jj evolog -r REV            # evolution of specific commit
```

## Creating & Editing Commits

```bash
jj new                      # empty commit on @
jj new REV                  # empty commit on REV
jj new A B                  # merge commit (parents A and B)
jj commit -m "msg"          # finalize @ and create new working copy
jj describe -m "msg"        # set message on @
jj describe -r REV -m "msg" # set message on specific commit
jj edit REV                 # make REV the working copy
```

## Rewriting History

```bash
jj squash                   # fold @ into parent
jj squash -i                # interactive (select hunks)
jj squash --into REV        # fold @ into specific ancestor
jj split                    # split @ interactively
jj split -r REV             # split specific commit
jj diffedit -r REV          # edit diff of any commit in editor
jj abandon REV              # delete commit (descendants rebased)
jj duplicate REV            # copy commit
jj duplicate REV -d DST     # copy to destination
```

## Rebasing

```bash
jj rebase -s SRC -d DST     # rebase SRC + descendants onto DST
jj rebase -r REV -d DST     # rebase single commit (extracts from chain)
jj rebase -b BOOKMARK -d DST  # rebase bookmark's ancestors
jj rebase -r C --before B   # insert C before B
jj rebase -r C --after B    # insert C after B
```

## Bookmarks

```bash
jj bookmark list            # list all (alias: jj b l)
jj bookmark create NAME -r REV
jj bookmark move NAME --to REV
jj bookmark delete NAME
jj bookmark track NAME --remote=origin
jj bookmark untrack NAME --remote=origin
jj bookmark rename OLD NEW
```

## File Operations

```bash
jj file list                # tracked files
jj file list -r REV         # files at revision
jj file annotate PATH       # blame/annotate
jj file untrack PATHS       # stop tracking (keep files)
jj file track PATHS         # start tracking
jj file chmod x PATH        # make executable
jj file chmod n PATH        # remove executable
jj restore                  # restore @ from parent
jj restore --from REV       # restore from specific commit
jj restore PATH             # restore specific file
```

## Undo & Operations

```bash
jj undo                     # undo last operation
jj op log                   # operation history
jj op restore OP_ID         # restore to previous state
jj op diff OP1 OP2          # diff between operations
jj --at-op=OP_ID log        # view at point in time
```

## Workspace

```bash
jj workspace root           # show workspace root
jj workspace add PATH       # add workspace at PATH
jj workspace forget [WS]    # forget workspace
jj workspace list           # list workspaces
jj workspace update-stale   # update stale workspace
```

## Other

```bash
jj obslog -r REV            # obsolete log (predecessor history)
jj parallelize REV...       # make commits siblings instead of chain
jj revert -r REV            # create commit that undoes REV
jj absorb                   # auto-squash fixups into relevant commits
jj fix                      # run formatters on commits
```
