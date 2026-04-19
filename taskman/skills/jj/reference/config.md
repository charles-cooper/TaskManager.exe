# Configuration

## Config Locations (precedence order)

1. CLI: `--config key=value`
2. Repo / workspace config (stored **outside** the repo since 0.38, under `$XDG_CONFIG_HOME/jj/repos/<hash>/`). Legacy `.jj/repo/config.toml` / `.jj/workspace-config.toml` are auto-migrated on first access.
3. User: `~/.config/jj/config.toml` or `~/.jjconfig.toml`
4. Built-in defaults

Use `jj config path --repo` / `--user` to print the actual file path. Edit via `jj config edit --repo` / `--user` — do not hand-create `.jj/repo/config.toml` in new repos.

## Config Commands

```bash
jj config list              # show all config
jj config list --user       # user config only
jj config list --repo       # repo config only
jj config get ui.pager      # get specific key
jj config set --user KEY VALUE
jj config set --repo KEY VALUE
jj config edit --user       # open in editor
jj config edit --repo
jj config path --user       # show config file path
```

## Common Settings

```toml
[user]
name = "Your Name"
email = "you@example.com"

[ui]
pager = "less -FRX"
diff-editor = ":builtin"        # or "meld", "vimdiff"
merge-editor = "meld"
color = "auto"                   # auto, always, never
default-command = "log"          # command when no args

[git]
push = "origin"                  # default push remote
fetch = ["origin", "upstream"]   # remotes to fetch

[snapshot]
max-new-file-size = "1MiB"       # limit for auto-tracking
```

## Revset Aliases

```toml
[revset-aliases]
'trunk()' = 'main@origin'
'mine()' = 'author(exact:"your@email.com")'
'wip' = 'description(glob:"wip*")'
```

## Template Aliases

```toml
[template-aliases]
'format_timestamp(ts)' = 'ts.ago()'
```

## Immutability

```toml
[revset-aliases]
# Default: trunk + tags + untracked remote bookmarks
'immutable_heads()' = 'builtin_immutable_heads()'

# Custom: also protect release branches
'immutable_heads()' = 'builtin_immutable_heads() | tags() | remote_bookmarks(glob:"release-*")'
```

## Command Aliases

```toml
[aliases]
l = ["log", "-r", "(main..@)::"]
d = ["diff"]
s = ["st"]
```

## Auto-tracking Bookmarks

```toml
[remotes.origin]
auto-track-bookmarks = "*"              # track all remote bookmarks on fetch
# auto-track-bookmarks = ["main", "develop"]  # specific only

# Only auto-track bookmarks that YOU create locally (0.38+):
auto-track-created-bookmarks = "*"
```

## `jj bookmark advance` Defaults (0.39+)

```toml
[revsets]
bookmark-advance-from = 'heads(::to & bookmarks())'  # closest ancestor bookmark
bookmark-advance-to   = '@'                          # target
```

## Colors

```toml
[colors]
"error" = "red"
"warning" = "yellow"
"hint" = "cyan"
```
