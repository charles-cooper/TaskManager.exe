# Configuration

## Config Locations (precedence order)

1. CLI: `--config key=value`
2. Repo: `.jj/repo/config.toml`
3. User: `~/.config/jj/config.toml` or `~/.jjconfig.toml`
4. Built-in defaults

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
auto-track-bookmarks = "*"              # track all
# auto-track-bookmarks = ["main", "develop"]  # specific only
```

## Colors

```toml
[colors]
"error" = "red"
"warning" = "yellow"
"hint" = "cyan"
```
