Checkpoint and advance the workspace bookmark in the `.agent-files/` jj repo.

Run: taskman sync "$ARGUMENTS"

1. Creates checkpoint with given reason (jj describe + new revision)
2. Moves this workspace's jj bookmark to current revision
3. Starts fresh working copy

Each jj workspace has its own bookmark (e.g., `default`, `feature-x`).
Since `.agent-files/` is a single jj repo shared across workspaces (see SKILL.md#Architecture), synced commits are visible in `jj log` from any workspace — no push/pull needed. To incorporate another workspace's changes, use merge commits (`jj new @ other-workspace`). **Do not squash or rebase across workspace boundaries** — this rewrites ancestor commits shared by other workspaces, causing conflict cascades.

Use periodically to mark progress in .agent-files history.
