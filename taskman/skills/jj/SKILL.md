---
name: jj
description: Jujutsu version control system. Use when working with jj repositories, commits, bookmarks, rebasing, conflicts, or git operations in jj context. Triggers on jj commands, revsets, or VCS workflows in jj-managed repos.
---

# Jujutsu (jj)

Git-compatible VCS with cleaner model. Working copy IS a commit (`@`). No staging area. Conflicts stored in commits. Full undo via operation log.

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

**Edge Cases**: See [patterns/gotchas.md](patterns/gotchas.md) for gotchas and troubleshooting

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
