# Revsets Reference

Functional language for selecting commits.

## Symbols

```
@              working copy commit
root()         virtual root (ancestor of all)
trunk()        main branch/bookmark
<change-id>    commit by change ID (e.g., kntqzsqt)
<commit-id>    commit by SHA prefix
<bookmark>     bookmark target
<tag>          tag target
name@remote    remote bookmark (e.g., main@origin)
```

## Operators (by precedence)

```
x-        parents of x
x+        children of x
::x       ancestors of x (including x)
x::       descendants of x (including x)
x..       revisions not ancestors of x (= ~::x)
..x       ancestors of x (incl. x) excluding the root commit
::        all visible commits (= all())
..        all visible commits except the root commit
x::y      DAG range: descendants of x that are ancestors of y
x..y      set range: ancestors of y that are not ancestors of x
~x        complement (not in x)
x & y     intersection
x ~ y     difference (in x but not y)
x | y     union
```

Note: `(A | B)..` is `A.. & B..`, not `A.. | B..`.

## Functions

### Selection
```bash
all()                       # all visible commits
none()                      # empty set
visible()                   # visible commits (default scope)
hidden()                    # hidden commits
```

### Navigation
```bash
parents(x)                  # immediate parents
parents(x, N)               # parents up to depth N
children(x)                 # immediate children
children(x, N)              # children up to depth N
ancestors(x)                # all ancestors (same as ::x)
ancestors(x, N)             # ancestors up to depth N
descendants(x)              # all descendants (same as x::)
descendants(x, N)           # descendants up to depth N
```

### Structure
```bash
heads(x)                    # commits in x with no descendants in x
roots(x)                    # commits in x with no ancestors in x
connected(x)                # x::x (fill in gaps)
fork_point(x)               # common ancestor(s) of commits in x
latest(x, N)                # N most recent commits from x
```

### References
```bash
bookmarks()                 # all bookmark targets
bookmarks(pattern)          # matching bookmarks
remote_bookmarks()          # all remote bookmarks
remote_bookmarks(pat)       # matching remote bookmarks
remote_bookmarks(pat, remote=pat)  # with remote filter
tags()                      # all tags
tags(pattern)               # matching tags
git_refs()                  # all git refs
git_head()                  # git HEAD
```

### Filtering
```bash
author(pattern)             # by author name/email
mine()                      # by current user
committer(pattern)          # by committer
description(pattern)        # by commit message
files(pattern)              # touching files matching pattern
diff_lines(text, [files])   # diff contains matching text (renamed from diff_contains in 0.38)
diff_lines_added(text, [files])    # only the added side
diff_lines_removed(text, [files])  # only the removed side
```

### State
```bash
empty()                     # no file changes
merges()                    # merge commits (2+ parents)
conflicts()                 # commits with conflicts
divergent()                 # divergent changes (same change ID, multiple visible commits)
mutable()                   # mutable commits
immutable()                 # immutable commits
present(x)                  # x, filtering out missing commits
```

### References (additions)
```bash
remote_tags()               # all remote tags (tracked 0.38+)
remote_tags(pat, remote=pat)
```

## String Patterns

**Default is `glob:`** (not substring). Quotes optional.
```
exact:"string"              # exact match
glob:"pattern"              # shell wildcard (* ? [])  ← DEFAULT
regex:"pattern"             # regex (matches substring)
substring:"string"          # explicit substring
```

Case-insensitive: append `-i` (e.g., `glob-i:"fix*jpeg*"`).

Logical combinators inside a pattern argument: `~p`, `p & q`, `p | q`, `p ~ q`
(e.g., `bookmarks(~glob:"ci/*")`).

## Examples

```bash
# Unpushed commits
jj log -r 'mine() ~ remote_bookmarks()'

# Commits on feature branch
jj log -r 'main..@'

# Recent commits by author
jj log -r 'author("alice") & ancestors(@, 20)'

# Commits touching file
jj log -r 'files("src/main.rs")'

# Commits that add or remove a TODO under src/
jj log -r 'diff_lines("*TODO*", "src")'

# Conflicted commits in branch
jj log -r 'main..@ & conflicts()'

# All commits not on any remote
jj log -r 'remote_bookmarks()..'

# Merge commits in history
jj log -r '::@ & merges()'

# Empty commits (for cleanup)
jj log -r 'empty() & mutable()'
```
