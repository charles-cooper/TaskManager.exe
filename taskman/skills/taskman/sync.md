Sync working copy and update workspace bookmark.

Run: taskman sync "$ARGUMENTS"

1. Creates checkpoint with given reason
2. Moves workspace's bookmark to current revision
3. Starts fresh working copy

Each workspace has its own bookmark (e.g., `default`, `feature-x`).
Use periodically to mark progress in .agent-files history.
