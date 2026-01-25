"""Migration from old clone/push model to jj workspaces model."""

import shutil
from pathlib import Path

from taskman.jj import run_jj


def _has_stale_remote(repo_path: Path) -> bool:
    """Check if repo has origin remote pointing to .agent-files.git."""
    try:
        _, remote_out, _ = run_jj(["git", "remote", "list"], repo_path)
        for line in remote_out.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0] == "origin":
                if ".agent-files.git" in parts[1]:
                    return True
    except RuntimeError:
        pass
    return False


def _find_worktrees_to_migrate(worktrees_dir: Path) -> tuple[list[str], list[str]]:
    """Find worktrees that need migration or repair.

    Returns:
        (worktree_clones, worktree_broken)
        - clones: .jj/repo is directory (old standalone repo)
        - broken: .jj/repo missing (incomplete migration)
    """
    worktree_clones: list[str] = []
    worktree_broken: list[str] = []

    if not worktrees_dir.exists():
        return worktree_clones, worktree_broken

    for wt_dir in worktrees_dir.iterdir():
        if wt_dir.is_dir():
            wt_agent = wt_dir / ".agent-files"
            if wt_agent.exists():
                jj_repo_path = wt_agent / ".jj" / "repo"
                if jj_repo_path.is_dir():
                    # Old clone has .jj/repo as directory
                    worktree_clones.append(wt_dir.name)
                elif not jj_repo_path.is_file():
                    # Missing or broken .jj/repo = incomplete migration
                    worktree_broken.append(wt_dir.name)

    return worktree_clones, worktree_broken


def _sync_worktrees_to_bare(
    worktree_clones: list[str],
    worktrees_dir: Path,
    agent_files: Path,
) -> None:
    """Push worktree commits to bare repo, then fetch into main."""
    for name in worktree_clones:
        wt_agent = worktrees_dir / name / ".agent-files"
        try:
            run_jj(["git", "push", "--all"], wt_agent)
        except RuntimeError:
            pass  # May fail if nothing to push

    # Fetch into main so it has all commits
    try:
        run_jj(["git", "fetch"], agent_files)
    except RuntimeError:
        pass


def _remove_stale_remote(agent_files: Path, bare: Path) -> bool:
    """Remove origin remote if it points to old bare repo. Returns True if removed."""
    try:
        _, remote_out, _ = run_jj(["git", "remote", "list"], agent_files)
        for line in remote_out.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0] == "origin":
                remote_path = Path(parts[1])
                # Match exact path or any .agent-files.git reference
                if (remote_path == bare or
                    (bare.exists() and remote_path.resolve() == bare.resolve()) or
                    ".agent-files.git" in str(remote_path)):
                    run_jj(["git", "remote", "remove", "origin"], agent_files)
                    return True
    except RuntimeError:
        pass
    return False


def _get_existing_workspaces(agent_files: Path) -> set[str]:
    """Get set of existing workspace names."""
    existing: set[str] = set()
    try:
        _, ws_out, _ = run_jj(["workspace", "list"], agent_files)
        for line in ws_out.splitlines():
            # Format: "name: revid description"
            if ":" in line:
                existing.add(line.split(":")[0].strip())
    except RuntimeError:
        pass
    return existing


def _create_git_file_for_workspace(workspace_path: Path, main_repo_path: Path) -> None:
    """Create .git file in workspace pointing to main repo's .git directory.

    WHY THIS EXISTS:
    jj workspaces created with `jj workspace add` only get a .jj/ directory
    with a pointer to the main repo's .jj/repo. They do NOT get a .git
    directory or file.

    This means raw git commands (git status, git log, git diff, etc.) fail
    with "fatal: not a git repository" in linked workspaces, even though
    the main repo is colocated with git.

    This is arguably a UX bug in jj - it colocates with git in the main repo
    but doesn't extend that to linked workspaces.

    WORKAROUND:
    We create a .git file (not directory) containing a gitdir pointer to the
    main repo's .git directory. This is the same mechanism git worktrees use.

    Example contents: "gitdir: /path/to/main/.git"

    This allows raw git commands to work in linked workspaces, which is
    important for users who mix jj and git commands, or for tools that
    shell out to git.
    """
    main_git = main_repo_path / ".git"
    if main_git.is_dir():
        workspace_git = workspace_path / ".git"
        workspace_git.write_text(f"gitdir: {main_git}\n")


def _migrate_worktree(
    name: str,
    worktrees_dir: Path,
    agent_files: Path,
    existing_workspaces: set[str],
) -> None:
    """Migrate a single worktree clone to jj workspace."""
    wt_agent = worktrees_dir / name / ".agent-files"

    # Remove existing workspace if present (from partial migration)
    if name in existing_workspaces:
        run_jj(["workspace", "forget", name], agent_files)

    # Remove the old clone
    shutil.rmtree(wt_agent)

    # Create jj workspace
    run_jj(["workspace", "add", "--name", name, str(wt_agent)], agent_files)

    # Create .git file so raw git commands work (see _create_git_file_for_workspace)
    _create_git_file_for_workspace(wt_agent, agent_files)

    # Create bookmark matching workspace name (ignore if exists)
    try:
        run_jj(["bookmark", "create", name, "-r", f"{name}@"], wt_agent)
    except RuntimeError:
        pass  # Bookmark may already exist


def migrate() -> str:
    """Migrate from old clone/push model to jj workspaces model.

    Old model: .agent-files.git/ (bare) + .agent-files/ (clone)
    New model: .agent-files/ (main workspace) + workspaces via jj workspace add

    Steps:
    1. Verify old model exists (.agent-files.git/) or stale state
    2. Sync worktree commits to bare (preserve data)
    3. Remove origin remote pointing to bare repo
    4. Remove .agent-files.git/ (no longer needed)
    5. Migrate worktree clones to jj workspaces
    6. Repair broken worktrees from incomplete migrations

    The .agent-files/ clone becomes the main workspace automatically.
    """
    cwd = Path.cwd()
    bare = cwd / ".agent-files.git"
    agent_files = cwd / ".agent-files"

    if not agent_files.exists():
        return "Error: .agent-files/ not found - cannot migrate"

    # Check if there's anything to migrate
    has_bare = bare.exists()
    has_stale_remote = _has_stale_remote(agent_files) if not has_bare else False

    worktrees_dir = cwd / "worktrees"
    worktree_clones, worktree_broken = _find_worktrees_to_migrate(worktrees_dir)
    has_worktree_issues = bool(worktree_clones) or bool(worktree_broken)

    if not has_bare and not has_stale_remote and not has_worktree_issues:
        return "No migration needed - .agent-files.git/ not found"

    # Sync worktree clones to bare before deleting (preserve their commits)
    result = ["Migration complete:"]
    if bare.exists() and worktree_clones:
        _sync_worktrees_to_bare(worktree_clones, worktrees_dir, agent_files)

    # Remove stale remote
    removed_remote = _remove_stale_remote(agent_files, bare)

    # Remove the bare repo if it exists
    if bare.exists():
        shutil.rmtree(bare)
        result.append(f"  - Removed {bare}")
    if removed_remote:
        result.append("  - Removed origin remote")
    result.append(f"  - {agent_files} is now the main workspace")

    # Get existing workspaces to handle duplicates
    existing_workspaces = _get_existing_workspaces(agent_files)

    # Migrate worktree clones and fix broken worktrees
    migrated: list[str] = []
    repaired: list[str] = []
    failed: list[tuple[str, str]] = []

    for name in worktree_clones:
        try:
            _migrate_worktree(name, worktrees_dir, agent_files, existing_workspaces)
            migrated.append(name)
        except Exception as e:
            failed.append((name, str(e)))

    for name in worktree_broken:
        try:
            _migrate_worktree(name, worktrees_dir, agent_files, existing_workspaces)
            repaired.append(name)
        except Exception as e:
            failed.append((name, str(e)))

    # Format output
    if migrated:
        result.append("")
        result.append("Migrated worktrees:")
        for name in migrated:
            result.append(f"  - worktrees/{name}/.agent-files -> workspace '{name}'")

    if repaired:
        result.append("")
        result.append("Repaired worktrees:")
        for name in repaired:
            result.append(f"  - worktrees/{name}/.agent-files -> workspace '{name}'")

    if failed:
        result.append("")
        result.append("Failed to migrate:")
        for name, err in failed:
            result.append(f"  - worktrees/{name}: {err}")

    return "\n".join(result)
