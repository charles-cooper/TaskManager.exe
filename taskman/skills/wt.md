Set up .agent-files in a git worktree.

Run: taskman wt $ARGUMENTS

- No arguments: clone .agent-files into current directory (for existing worktrees)
- `taskman wt <name>`: create worktree for existing branch <name>
- `taskman wt <name> --new`: create worktree + new branch at worktrees/<name>/

Use when working in a git worktree that doesn't have .agent-files yet.
