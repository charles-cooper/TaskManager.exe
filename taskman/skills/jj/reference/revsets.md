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
x..       non-ancestors of x (x:: ~ ::x)
..x       ancestors excluding root (::x ~ root())
x::y      DAG range: descendants of x that are ancestors of y
x..y      set range: ancestors of y excluding ancestors of x
~x        complement (not in x)
x & y     intersection
x ~ y     difference (in x but not y)
x | y     union
```

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
diff_contains(text)         # diff contains text
diff_contains(text, files)  # diff contains text in specific files
```

### State
```bash
empty()                     # no file changes
merges()                    # merge commits (2+ parents)
conflicts()                 # commits with conflicts
mutable()                   # mutable commits
immutable()                 # immutable commits
present(x)                  # x, filtering out missing commits
```

## String Patterns

Default is substring match. Prefix with:
```
exact:"string"              # exact match
glob:"pattern"              # shell wildcard (* ? [])
regex:"pattern"             # regex (matches substring)
substring:"string"          # explicit substring
```

Case-insensitive: append `-i` (e.g., `glob-i:"*.txt"`)

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

# Conflicted commits in branch
jj log -r 'main..@ & conflicts()'

# All commits not on any remote
jj log -r 'remote_bookmarks()..'

# Merge commits in history
jj log -r '::@ & merges()'

# Empty commits (for cleanup)
jj log -r 'empty() & mutable()'
```
