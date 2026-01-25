Set up .agent-files workspace in a git worktree.

Run: taskman wt $ARGUMENTS

- No arguments: create .agent-files workspace in current directory (for existing worktrees)
- `taskman wt <name>`: create worktree + .agent-files workspace for existing branch <name>
- `taskman wt <name> --new`: create worktree + new branch + .agent-files workspace at worktrees/<name>/

Workspaces share the same jj repo (like git branches). Each has its own working copy.
No push/pull needed - commits are immediately visible across workspaces via `jj log`.

Use when working in a git worktree that doesn't have .agent-files yet.
