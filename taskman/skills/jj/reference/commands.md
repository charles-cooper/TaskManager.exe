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
jj squash                   # fold @ into parent (@- contents absorb @)
jj squash -i                # interactive (select hunks)
jj squash -r REV            # fold REV into its parent
jj squash --from SRC        # fold SRC into @  (default --into is @)
jj squash --from SRC --into DST   # fold SRC into DST
jj squash --into REV        # fold @ into specific ancestor REV
jj split                    # split @ interactively
jj split -r REV             # split specific commit
jj diffedit -r REV          # edit diff of any commit in editor
jj abandon REV              # delete commit (descendants rebased)
jj duplicate REV            # copy commit
jj duplicate REV -d DST     # copy to destination (--onto alias)
jj metaedit -r REV --update-change-id   # new identity (fix divergence)
jj arrange [REVSETS]        # TUI to reorder/abandon commits interactively (0.39+)
```

## Rebasing

`-d`/`--destination` is an alias for `--onto/-o`.

```bash
jj rebase -s SRC -d DST          # rebase SRC + descendants onto DST
jj rebase -r REV -d DST          # rebase single commit (extracts from chain)
jj rebase -b BOOKMARK -d DST     # rebase bookmark's ancestors onto DST
jj rebase -r C -B B              # --insert-before (alias: --before)
jj rebase -r C -A B              # --insert-after  (alias: --after)
jj rebase -s SRC -d DST --simplify-parents   # drop redundant parents (0.39+)
```

## Bookmarks

```bash
jj bookmark list            # list all (alias: jj b l)
jj bookmark list --tracked  # only tracked (-t)
jj bookmark create NAME -r REV
jj bookmark set NAME -r REV # create or move (by name)
jj bookmark move NAME --to REV
jj bookmark move --from OLD_REV --to NEW_REV   # move by current location
jj bookmark advance [NAMES] # auto-move closest ancestor bookmark(s) to @ (0.39+)
jj bookmark delete NAME     # mark for deletion; pushes as deletion
jj bookmark forget NAME     # drop locally without propagating deletion
jj bookmark track NAME --remote=origin
jj bookmark untrack NAME --remote=origin
jj bookmark rename OLD NEW  # --overwrite-existing replaces an existing name (0.39+)
```

## File Operations

```bash
jj file list                # tracked files
jj file list -r REV         # files at revision
jj file show PATH           # print contents (-r REV for other revs)
jj file annotate PATH       # blame/annotate
jj file search PATTERN      # search file contents
jj file untrack PATHS       # stop tracking (keep files)
jj file track PATHS         # start tracking
jj file chmod x PATH        # make executable
jj file chmod n PATH        # remove executable
jj restore                  # restore @ from parent(s)
jj restore --from REV       # restore from specific commit
jj restore PATH             # restore specific path
```

## Undo & Operations

```bash
jj undo                     # undo last operation
jj redo                     # redo an undone operation
jj op log                   # operation history (also shows originating workspace, 0.40+)
jj op revert [OP]           # invert a specific (non-latest) operation
jj op restore OP_ID         # restore to previous state
jj op diff OP1 OP2          # diff between operations
jj --at-op=OP_ID log        # view at point in time
```

`jj op undo` was removed in 0.39 — use `jj undo`/`jj redo` or `jj op revert`.

## Workspace

```bash
jj workspace root [--name NAME]   # root of current/named workspace (0.38+ for --name)
jj workspace add PATH             # add workspace (uses relative link 0.39+)
jj workspace forget [WS...]       # forget workspaces (default: current)
jj workspace list                 # list workspaces
jj workspace update-stale         # snapshot + recover stale wc (see gotchas.md)
```

## Other

```bash
jj evolog -r REV            # evolution of a change across rewrites (obslog is an alias)
jj parallelize REV...       # make commits siblings instead of chain
jj revert -r REV            # create commit that undoes REV
jj absorb                   # auto-squash fixups into the relevant mutable ancestors
jj fix                      # run formatters on commits
                            # (0.40+: per-tool line-range via fix.tools.<name>.line-range-arg)
jj metaedit -r REV          # modify metadata without touching content
jj interdiff --from A --to B  # diff between the diffs of A and B
jj next / jj prev           # move @ to child / parent
jj bisect                   # bisect to find a bad revision
jj sign -r REV / jj unsign -r REV   # cryptographic signatures
jj util snapshot            # force-snapshot the working copy (scripts; replaces debug snapshot)
jj util gc                  # prune obsolete objects/ops older than 2 weeks (configurable)
```
