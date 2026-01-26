# Conflict Handling

## Key Behavior

- Conflicts stored IN commits (operations never fail due to conflicts)
- Conflict markers written to working copy files
- Can commit and rebase on top of conflicted commits
- Resolve anytime, not just at conflict creation

## Conflict Marker Format

Default "diff" style:
```
<<<<<<< conflict 1 of 1
%%%%%%% changes from base to side A
-old line
+new line from side A
+++++++ side B
new line from side B
>>>>>>> conflict 1 of 1 ends
```

Shows:
- What changed from base to side A (diff format)
- What side B has (snapshot)

## Resolution Methods

### Method 1: Edit Markers Manually
```bash
# Edit file, remove markers, keep desired content
# If on resolution commit:
jj squash
```

### Method 2: Merge Tool
```bash
jj resolve              # launch configured merge tool
jj resolve PATH         # resolve specific file
```

### Method 3: Take One Side
```bash
jj restore --from @- PATH          # take from parent
jj restore --from SIDE_REV PATH    # take from specific side
```

## Workflow: Resolve Conflict in Descendant

When rebase creates conflict:
```bash
jj new CONFLICTED_COMMIT    # create commit on top
# edit files to resolve
jj diff                      # review resolution
jj squash                    # fold resolution into conflicted commit
```

## Check for Conflicts

```bash
jj log -r 'conflicts()'     # show conflicted commits
jj st                        # shows conflict status
```

## Materialized vs Stored

- **Stored**: jj tracks conflict state internally
- **Materialized**: markers in working copy files
- Editing markers alone doesn't resolve - jj tracks real state
- Use `jj squash` or `jj restore` to update stored state

## Multiple Conflicts

For multiple conflicts in one file, markers are numbered:
```
<<<<<<< conflict 1 of 3
...
>>>>>>> conflict 1 of 3 ends
...
<<<<<<< conflict 2 of 3
...
```

Resolve all before conflict is considered resolved.

## Config: Merge Tool

```toml
[ui]
merge-editor = "meld"  # or vimdiff, kdiff3, etc.
```
