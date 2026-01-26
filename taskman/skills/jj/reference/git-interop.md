# Git Interoperability

## Colocated Mode (Default)

`.jj/` and `.git/` coexist. Both `jj` and `git` commands work. Git sees detached HEAD (normal).

```bash
jj git init                 # init new repo (creates both .jj and .git)
jj git init --no-colocate   # jj-only (uses git as backend internally)
```

## Commands

```bash
jj git clone URL [DIR]      # clone repo
jj git fetch                # fetch all remotes
jj git fetch --remote NAME  # fetch specific remote
jj git push --bookmark B    # push bookmark B
jj git push --all           # push all tracked bookmarks
jj git push --change ID     # auto-create+push bookmark for change
jj git remote add NAME URL
jj git remote remove NAME
jj git remote list
jj git import               # import git refs into jj
jj git export               # export jj state to git refs
```

## Bookmark Tracking

```bash
# Track remote bookmark (sync on fetch)
jj bookmark track main --remote=origin

# Stop tracking
jj bookmark untrack main --remote=origin

# Auto-track in config:
# [remotes.origin]
# auto-track-bookmarks = "*"
```

## Push Workflow

```bash
# Create and push feature
jj new main
# ... make changes ...
jj describe -m "feat: add thing"
jj bookmark create feature -r @
jj git push --bookmark feature

# After more commits
jj bookmark move feature --to @
jj git push --bookmark feature
```

## Quick Push with --change

```bash
# Auto-creates bookmark "push-<change-prefix>" and pushes
jj git push --change CHANGE_ID
```

## Fork Workflow (Multiple Remotes)

```bash
jj git clone --remote upstream URL
jj git remote add origin FORK_URL

# Configure in .jj/repo/config.toml:
# [git]
# fetch = "upstream"
# push = "origin"

# Or fetch from both:
# fetch = ["upstream", "origin"]
```

## Syncing with Git

In colocated repos, jj auto-syncs with git. If needed:

```bash
jj git import    # pull git refs → jj
jj git export    # push jj state → git refs
```

## Git Commands That Work

In colocated repos, git commands work but:
- Git sees detached HEAD
- Use `git switch` if needed for git-specific operations
- Prefer jj commands for normal workflow
