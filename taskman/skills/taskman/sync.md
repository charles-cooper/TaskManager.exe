Checkpoint and advance the workspace bookmark in the `.agent-files/` jj repo.

Run: taskman sync "$ARGUMENTS"

1. Creates checkpoint with given reason (jj describe + new revision)
2. Moves this workspace's jj bookmark to current revision
3. Starts fresh working copy
4. If in a worktree workspace, squashes changes into the default workspace

Each jj workspace has its own bookmark (e.g., `default`, `feature-x`).
In worktrees, sync automatically merges changes back to the default workspace so files stay up-to-date in the main repo. If conflicts arise, instructions are printed for manual resolution.

Use periodically to mark progress in .agent-files history.
