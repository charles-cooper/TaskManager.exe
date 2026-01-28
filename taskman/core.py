import json
import shutil
import subprocess
from pathlib import Path
import tomllib

from taskman.jj import run_jj, find_agent_files_dir


def _run_cmd(args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(
        args,
        cwd=str(cwd) if cwd is not None else None,
        text=True,
        capture_output=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _run_cmd_check(args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    code, out, err = _run_cmd(args, cwd=cwd)
    if code != 0:
        cmd_str = " ".join(args)
        raise RuntimeError(
            f"command failed ({code}): {cmd_str}\nstdout:\n{out}\nstderr:\n{err}"
        )
    return code, out, err


def _agent_files_cwd() -> Path:
    return find_agent_files_dir()


def _current_rev_id(cwd: Path) -> str:
    _, out, _ = run_jj(
        ["log", "--no-graph", "-r", "@", "-T", "change_id.short()"],
        cwd,
    )
    return out.strip()


def _rev_list_for_revset(revset: str, cwd: Path) -> list[str]:
    _, out, _ = run_jj(
        ["log", "--no-graph", "-r", revset, "-T", 'change_id.short() ++ "\\n"'],
        cwd,
    )
    return [line.strip() for line in out.splitlines() if line.strip()]


def _revset_has_revs(revset: str, cwd: Path) -> bool:
    return bool(_rev_list_for_revset(revset, cwd))


def _rev_list(start_rev: str, end_rev: str, cwd: Path) -> list[str]:
    if _revset_has_revs(start_rev, cwd):
        revset = f"{start_rev}::{end_rev}"
    else:
        revset = f"::{end_rev}"
    return _rev_list_for_revset(revset, cwd)


def _escape_revset_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', "\\\"")


def describe(reason: str) -> str:
    """Create named checkpoint.

    1. jj status (trigger snapshot)
    2. jj describe -m "<reason>"
    3. jj new (start fresh working copy)

    Returns: Revision ID and confirmation
    """
    cwd = _agent_files_cwd()
    run_jj(["status"], cwd)
    run_jj(["describe", "-m", reason], cwd)
    rev = _current_rev_id(cwd)
    # Start fresh working copy so subsequent edits don't modify the checkpoint.
    # (jj auto-snapshots before all commands, so @ already contains our changes)
    run_jj(["new"], cwd)
    return f"checkpoint {rev}: {reason}"


def _current_workspace_name(cwd: Path) -> str:
    """Get the current workspace name."""
    _, out, _ = run_jj(
        ["log", "--no-graph", "-r", "@", "-T", 'self.working_copies().map(|wc| wc.name()).join(",")'],
        cwd,
    )
    # Output is the workspace name(s) for the current working copy
    return out.strip() or "default"


def sync(reason: str) -> str:
    """Sync working copy: describe, update workspace bookmark.

    1. jj describe -m "<reason>"
    2. jj bookmark set <workspace> -r @ (move workspace bookmark forward)
    3. jj new (start fresh working copy)

    Each workspace has its own bookmark matching its name.

    Returns: Step-by-step status
    """
    cwd = _agent_files_cwd()
    steps: list[str] = []

    run_jj(["describe", "-m", reason], cwd)
    rev = _current_rev_id(cwd)
    steps.append(f"rev: {rev}")

    # Get current workspace name for bookmark
    workspace = _current_workspace_name(cwd)

    # Move workspace bookmark to current revision
    try:
        run_jj(["bookmark", "set", workspace, "-r", "@"], cwd)
        steps.append(f"bookmark: {workspace} -> @")
    except RuntimeError:
        # Create if doesn't exist
        try:
            run_jj(["bookmark", "create", workspace, "-r", "@"], cwd)
            steps.append(f"bookmark: created {workspace}")
        except RuntimeError:
            steps.append("bookmark: failed")

    run_jj(["new"], cwd)
    return "\n".join(steps)


def history_diffs(file: str, start_rev: str, end_rev: str = "@") -> str:
    """Get all diffs for file across revision range.

    1. Get revisions: jj log --no-graph -r "{start}::{end}" -T 'change_id.short()'
    2. For each: jj diff -r {rev} -- {file}
    3. Concatenate with === {rev} === headers
    """
    cwd = _agent_files_cwd()
    revs = _rev_list(start_rev, end_rev, cwd)
    if not revs:
        return "No revisions found in range."

    sections: list[str] = []
    for rev in revs:
        sections.append(f"=== {rev} ===")
        _, out, _ = run_jj(["diff", "-r", rev, "--", file], cwd)
        sections.append(out.rstrip())

    return "\n".join(sections).rstrip()


def history_batch(file: str, start_rev: str, end_rev: str = "@") -> str:
    """Fetch file content at all revisions in range.

    1. Get revisions (same as history_diffs)
    2. For each: jj file show -r {rev} {file}
    3. Concatenate with === {rev} === headers
    """
    cwd = _agent_files_cwd()
    revs = _rev_list(start_rev, end_rev, cwd)
    if not revs:
        return "No revisions found in range."

    sections: list[str] = []
    for rev in revs:
        try:
            _, out, _ = run_jj(["file", "show", "-r", rev, file], cwd)
        except RuntimeError as exc:
            if "no such path" in str(exc).lower():
                sections.append(f"=== {rev} ===")
                sections.append("(file does not exist at this revision)")
                continue
            raise
        sections.append(f"=== {rev} ===")
        sections.append(out.rstrip())

    return "\n".join(sections).rstrip()


def history_search(pattern: str, file: str | None = None, limit: int = 20) -> str:
    """Search history for pattern in diffs using jj's diff_contains().

    Uses: jj log -r 'diff_contains("{pattern}")' --limit {limit}
    Or with file: jj log -r 'diff_contains("{pattern}", "{file}")' --limit {limit}

    Supports jj pattern syntax: exact:, glob:, regex:, substring:
    Examples:
      history_search("TODO")                    # glob (default)
      history_search("regex:fix.*bug")          # regex
      history_search("exact:FIXME", "src/")     # exact match in src/

    Returns: Matching revisions with commit info
    """
    cwd = _agent_files_cwd()
    escaped_pattern = _escape_revset_value(pattern)
    if file is None:
        revset = f'diff_contains("{escaped_pattern}")'
    else:
        escaped_file = _escape_revset_value(file)
        revset = f'diff_contains("{escaped_pattern}", "{escaped_file}")'
    _, out, _ = run_jj(["log", "-r", revset, "--limit", str(limit)], cwd)
    return out.rstrip()


# Setup functions

def init() -> str:
    """Create .agent-files/ as a jj workspace.

    1. jj git init .agent-files
    2. Create initial files: STATUS.md, LONGTERM_MEM.md, MEDIUMTERM_MEM.md, tasks/
    3. jj describe -m "initial setup"

    No bare repo needed - workspaces share the same jj repo directly.
    For remote backup, add a git remote later with: jj git remote add origin <url>
    """
    cwd = Path.cwd()
    agent_files = cwd / ".agent-files"

    if agent_files.exists():
        raise FileExistsError(".agent-files already exists")

    run_jj(["git", "init", str(agent_files)], cwd)

    # Set default author for agent commits
    run_jj(["config", "set", "--repo", "user.name", "Agent"], agent_files)
    run_jj(["config", "set", "--repo", "user.email", "agent@localhost"], agent_files)

    (agent_files / "tasks").mkdir(parents=True, exist_ok=True)
    for filename in ["STATUS.md", "LONGTERM_MEM.md", "MEDIUMTERM_MEM.md"]:
        path = agent_files / filename
        path.touch(exist_ok=True)

    run_jj(["describe", "-m", "initial setup"], agent_files)
    # Create bookmark matching workspace name (jj default is "default")
    run_jj(["bookmark", "create", "default", "-r", "@"], agent_files)
    # Start fresh working copy
    run_jj(["new"], agent_files)

    return "Initialized .agent-files"


def _find_main_agent_files(start: Path | None = None) -> Path:
    """Find the main .agent-files workspace (the one with .jj/ directory).

    Searches upward from start (default: cwd). A main workspace has a .jj/
    directory, while linked workspaces have a .jj file pointing to the main.
    """
    current = Path.cwd() if start is None else Path(start)
    if current.is_file():
        current = current.parent

    while True:
        candidate = current / ".agent-files"
        if candidate.is_dir():
            jj_repo_path = candidate / ".jj" / "repo"
            if jj_repo_path.is_dir():
                # This is a standalone repo (main workspace)
                return candidate
            elif jj_repo_path.is_file():
                # This is a linked workspace - read the pointer to find main
                # .jj/repo file contains path to the main repo's .jj/repo directory
                pointer = jj_repo_path.read_text().strip()
                # pointer is path to .jj/repo dir, go up twice for .agent-files
                return Path(pointer).parent.parent
        if current.parent == current:
            break
        current = current.parent

    raise FileNotFoundError(".agent-files directory not found")


def _is_main_workspace(agent_files: Path) -> bool:
    """Check if agent_files is the main workspace (has .jj/repo/ directory)."""
    jj_repo_path = agent_files / ".jj" / "repo"
    return jj_repo_path.is_dir()


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


def _find_main_repo(start: Path | None = None) -> Path:
    """Find the main git repo (parent of worktrees/).

    For worktrees: walks up to find the repo that contains worktrees/
    For main repo: returns cwd if it has .git directory
    """
    current = Path.cwd() if start is None else Path(start)
    if current.is_file():
        current = current.parent

    # Check if we're in a worktree (worktrees/<name>/...)
    for parent in [current] + list(current.parents):
        if parent.name == "worktrees" and parent.parent.is_dir():
            main = parent.parent
            if (main / ".git").is_dir():
                return main

    # Check if current dir is main repo
    if (current / ".git").is_dir():
        return current

    # Walk up looking for .git
    for parent in current.parents:
        if (parent / ".git").is_dir():
            return parent

    raise FileNotFoundError("Git repository not found")


def _get_worktree_name_from_path(path: Path, main_repo: Path) -> str | None:
    """Extract worktree name from path if inside worktrees/<name>/."""
    try:
        rel = path.relative_to(main_repo / "worktrees")
        # First component is the worktree name
        return rel.parts[0] if rel.parts else None
    except ValueError:
        return None


def _parse_git_worktrees(main_repo: Path) -> dict[str, dict]:
    """Parse git worktree list output.

    Returns: {name: {path, branch, valid}} where valid=path exists
    """
    code, out, _ = _run_cmd(["git", "worktree", "list", "--porcelain"], cwd=main_repo)
    if code != 0:
        return {}

    worktrees = {}
    current = {}
    for line in out.splitlines():
        if line.startswith("worktree "):
            if current and current.get("path"):
                # Extract name from path
                path = Path(current["path"])
                name = _get_worktree_name_from_path(path, main_repo)
                if name:
                    current["valid"] = path.exists()
                    worktrees[name] = current
            current = {"path": line[9:]}
        elif line.startswith("branch "):
            current["branch"] = line[7:]
        elif line == "detached":
            current["detached"] = True

    # Handle last entry
    if current and current.get("path"):
        path = Path(current["path"])
        name = _get_worktree_name_from_path(path, main_repo)
        if name:
            current["valid"] = path.exists()
            worktrees[name] = current

    return worktrees


def _parse_jj_workspaces(agent_files: Path) -> dict[str, dict]:
    """Parse jj workspace list output.

    Returns: {name: {path, commit, valid}} where valid=path exists
    """
    try:
        _, out, _ = run_jj(["workspace", "list"], agent_files)
    except RuntimeError:
        return {}

    workspaces = {}
    for line in out.splitlines():
        # Format: "name: commit_id description"
        if ": " not in line:
            continue
        name, rest = line.split(": ", 1)
        # Extract commit (first word after colon)
        commit = rest.split()[0] if rest.split() else ""
        # Path is agent_files parent / worktrees / name / .agent-files for non-default
        if name == "default":
            path = agent_files
        else:
            path = agent_files.parent / "worktrees" / name / ".agent-files"
        workspaces[name] = {
            "commit": commit,
            "path": str(path),
            "valid": path.exists(),
        }

    return workspaces


def _parse_jj_bookmarks(agent_files: Path) -> set[str]:
    """Get set of bookmark names."""
    try:
        _, out, _ = run_jj(["bookmark", "list", "--template", 'name ++ "\\n"'], agent_files)
    except RuntimeError:
        return set()

    return {line.strip() for line in out.splitlines() if line.strip()}


def _is_inside(path: Path, target: Path) -> bool:
    """Check if path is inside or equal to target."""
    try:
        path.resolve().relative_to(target.resolve())
        return True
    except ValueError:
        return False


def wt_list() -> str:
    """List worktrees with health status.

    Cross-references git worktrees, jj workspaces, and jj bookmarks
    to detect orphaned or mismatched state.
    """
    cwd = Path.cwd()
    main_repo = _find_main_repo(cwd)
    main_agent_files = _find_main_agent_files(cwd)

    git_wts = _parse_git_worktrees(main_repo)
    jj_wss = _parse_jj_workspaces(main_agent_files)
    jj_bms = _parse_jj_bookmarks(main_agent_files)

    # Collect all names (excluding 'default' which is the main workspace)
    all_names = (set(git_wts.keys()) | set(jj_wss.keys())) - {"default"}

    if not all_names:
        return "No worktrees found"

    lines = []
    for name in sorted(all_names):
        git = git_wts.get(name)
        jj_ws = jj_wss.get(name)
        has_bm = name in jj_bms

        status = []

        # Git worktree status
        if git:
            if git.get("valid"):
                status.append("git:ok")
            else:
                status.append("git:orphaned")
        else:
            status.append("git:missing")

        # jj workspace status
        if jj_ws:
            if jj_ws.get("valid"):
                status.append("jj-ws:ok")
            else:
                status.append("jj-ws:orphaned")
        else:
            status.append("jj-ws:missing")

        # Bookmark status
        if has_bm:
            status.append("bm:exists")

        lines.append(f"{name}: {' '.join(status)}")

    return "\n".join(lines)


def _has_conflicts(rev: str, agent_files: Path) -> bool:
    """Check if revision has conflicts."""
    try:
        _, out, _ = run_jj(
            ["log", "--no-graph", "-r", rev, "-T", "conflict"],
            agent_files,
        )
        return out.strip() == "true"
    except RuntimeError:
        return False


def wt_rm(name: str, *, force: bool = False) -> str:
    """Remove a git worktree and merge its jj workspace changes.

    Steps:
    1. Check we're not inside the target worktree
    2. Remove git worktree (if exists)
    3. Forget jj workspace
    4. Auto-merge changes into default workspace
    5. Fail loudly if merge conflicts

    Use --force for git worktree with uncommitted files.
    """
    cwd = Path.cwd()
    main_repo = _find_main_repo(cwd)
    main_agent_files = _find_main_agent_files(cwd)
    worktree_dir = main_repo / "worktrees" / name

    # Block removal of current worktree
    if _is_inside(cwd, worktree_dir):
        raise ValueError(
            f"Cannot remove current worktree.\n"
            f"Run: cd {main_repo} && taskman wt rm {name}"
        )

    # Block removal of default workspace
    if name == "default":
        raise ValueError("Cannot remove default workspace")

    results = []
    jj_wss = _parse_jj_workspaces(main_agent_files)
    jj_bms = _parse_jj_bookmarks(main_agent_files)

    # Describe workspace changes before removing
    if name in jj_wss:
        try:
            run_jj(["describe", "-r", f"{name}@", "-m", f"wt-{name}"], main_agent_files)
        except RuntimeError:
            pass  # Best effort

    # 1. Remove git worktree
    git_wts = _parse_git_worktrees(main_repo)
    if name in git_wts:
        if git_wts[name].get("valid"):
            cmd = ["git", "worktree", "remove"]
            if force:
                cmd.append("--force")
            cmd.append(str(worktree_dir))
            try:
                _run_cmd_check(cmd, cwd=main_repo)
                results.append(f"Removed git worktree worktrees/{name}/")
            except RuntimeError as e:
                if "contains modified or untracked files" in str(e):
                    raise ValueError(
                        f"Worktree has uncommitted files. Use --force to remove anyway."
                    ) from e
                raise
        else:
            # Worktree entry exists but path is gone - prune it
            _run_cmd_check(["git", "worktree", "prune"], cwd=main_repo)
            results.append(f"Pruned stale git worktree entry for {name}")
    elif worktree_dir.exists():
        # Directory exists but not a git worktree
        if force:
            shutil.rmtree(worktree_dir)
            results.append(f"Removed directory worktrees/{name}/ (was not a git worktree)")
        else:
            results.append(f"Warning: worktrees/{name}/ exists but is not a git worktree")

    # 2. Forget jj workspace
    if name in jj_wss:
        try:
            run_jj(["workspace", "forget", name], main_agent_files)
            results.append(f"Forgot jj workspace '{name}'")
        except RuntimeError as e:
            results.append(f"Warning: failed to forget jj workspace: {e}")

    # 3. Auto-merge changes into default workspace
    if name in jj_bms:
        try:
            run_jj(["squash", "--from", name, "-m", f"merged wt-{name}"], main_agent_files)
        except RuntimeError as e:
            results.append(f"Warning: could not auto-merge: {e}")
            results.append(f"Bookmark '{name}' retained - merge manually: jj squash --from {name}")
            return "\n".join(results)
        
        # Check for conflicts
        if _has_conflicts("@", main_agent_files):
            raise ValueError(
                f"MERGE CONFLICTS after squashing '{name}'!\n"
                f"\n"
                f"⚠️  DO NOT use --ours/--theirs blindly - you WILL lose accumulated knowledge.\n"
                f"\n"
                f"Resolution steps:\n"
                f"  cd .agent-files\n"
                f"  jj resolve              # or edit conflict markers manually\n"
                f"  jj diff                 # verify result\n"
                f"  jj bookmark delete {name}  # cleanup after resolving\n"
                f"\n"
                f"Guidelines by file type:\n"
                f"  STATUS.md: merge task lists, keep all active tasks\n"
                f"  MEDIUMTERM/LONGTERM_MEM.md: combine entries, dedupe, keep all learnings\n"
                f"  HANDOFF_*.md: keep newer context, check older for unique info\n"
                f"  TASK_*.md: merge attempt histories and checklists\n"
                f"\n"
                f"PRINCIPLE: Err on keeping information. Duplicates can be pruned later. Lost knowledge is gone forever."
            )
        
        # Clean merge - delete bookmark
        run_jj(["bookmark", "delete", name], main_agent_files)
        results.append(f"✓ Merged changes from '{name}'")

    if not results:
        return f"Nothing to clean up for '{name}'"

    return "\n".join(results)


def wt_prune() -> str:
    """Clean up all orphaned worktree state.

    Detects and removes:
    - Git worktree entries pointing to non-existent directories
    - jj workspaces with missing working copies
    - Bookmarks matching orphaned workspace names
    """
    cwd = Path.cwd()
    main_repo = _find_main_repo(cwd)
    main_agent_files = _find_main_agent_files(cwd)

    results = []

    # 1. Prune git worktrees
    code, out, _ = _run_cmd(["git", "worktree", "prune", "-v"], cwd=main_repo)
    if code == 0 and out.strip():
        for line in out.strip().splitlines():
            results.append(f"git: {line}")

    # 2. Find and forget orphaned jj workspaces
    jj_wss = _parse_jj_workspaces(main_agent_files)
    jj_bms = _parse_jj_bookmarks(main_agent_files)

    for name, ws in jj_wss.items():
        if name == "default":
            continue
        if not ws.get("valid"):
            try:
                run_jj(["workspace", "forget", name], main_agent_files)
                results.append(f"Forgot orphaned jj workspace '{name}'")

                # Also delete matching bookmark
                if name in jj_bms:
                    run_jj(["bookmark", "delete", name], main_agent_files)
                    results.append(f"Deleted orphaned bookmark '{name}'")
            except RuntimeError as e:
                results.append(f"Warning: failed to forget workspace {name}: {e}")

    if not results:
        return "No orphaned state found"

    return "\n".join(results)


def wt(name: str | None = None, *, new_branch: bool = False) -> str:
    """Create git worktree with jj workspace for .agent-files.

    If name is provided (from main repo):
        1. Create worktrees/<name>/ via git worktree add
        2. Create jj workspace for .agent-files in worktrees/<name>/

    If name is None (recovery for existing worktree):
        1. Create jj workspace for .agent-files in current directory

    By default uses existing branch. If new_branch=True, creates new branch.

    All workspaces share the same jj repo - no sync needed between them.
    """
    cwd = Path.cwd()
    main_agent_files = _find_main_agent_files(cwd)
    in_main_repo = _is_main_workspace(cwd / ".agent-files") if (cwd / ".agent-files").exists() else False

    if name:
        if not in_main_repo:
            raise ValueError(
                f"Run 'taskman wt {name}' from main repo (where .agent-files/.jj/ exists)"
            )

        worktree_dir = cwd / "worktrees" / name
        if worktree_dir.exists():
            raise FileExistsError(f"worktrees/{name} already exists")

        # Create git worktree for main project
        cmd = ["git", "worktree", "add", str(worktree_dir)]
        if not new_branch:
            cmd.append(name)
        _run_cmd_check(cmd, cwd=cwd)

        # Create jj workspace for .agent-files with matching name
        # Use -r @ to base new workspace on current revision (otherwise starts at root)
        workspace_agent_files = worktree_dir / ".agent-files"
        run_jj(["workspace", "add", "--name", name, "-r", "@", str(workspace_agent_files)], main_agent_files)

        # Create .git file so raw git commands work (see _create_git_file_for_workspace)
        _create_git_file_for_workspace(workspace_agent_files, main_agent_files)

        # Create bookmark matching workspace name
        run_jj(["bookmark", "create", name, "-r", f"{name}@"], workspace_agent_files)

        return f"Created worktree at worktrees/{name}/ with .agent-files workspace '{name}'"
    else:
        if in_main_repo:
            raise ValueError("Use 'taskman wt <name>' to create a worktree")

        workspace_agent_files = cwd / ".agent-files"
        if workspace_agent_files.exists():
            raise FileExistsError(".agent-files already exists")

        # Use parent directory name as workspace name
        # Use -r @ to base new workspace on current revision (otherwise starts at root)
        ws_name = cwd.name
        run_jj(["workspace", "add", "--name", ws_name, "-r", "@", str(workspace_agent_files)], main_agent_files)

        # Create .git file so raw git commands work (see _create_git_file_for_workspace)
        _create_git_file_for_workspace(workspace_agent_files, main_agent_files)

        # Create bookmark matching workspace name
        run_jj(["bookmark", "create", ws_name, "-r", f"{ws_name}@"], workspace_agent_files)

        return f"Created .agent-files workspace '{ws_name}' (linked to {main_agent_files})"


# Re-export migrate from its own module
from taskman.migrate import migrate  # noqa: F401


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    return json.loads(text)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    return tomllib.loads(text)


def _toml_format_value(value) -> str:
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', "\\\"")
        return f"\"{escaped}\""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, list):
        return "[" + ", ".join(_toml_format_value(v) for v in value) + "]"
    raise TypeError(f"Unsupported TOML value: {value!r}")


def _toml_dump_table(lines: list[str], prefix: list[str], table: dict) -> None:
    lines.append(f"[{'.'.join(prefix)}]")
    for key in sorted(table.keys()):
        value = table[key]
        if isinstance(value, dict):
            continue
        lines.append(f"{key} = {_toml_format_value(value)}")

    for key in sorted(table.keys()):
        value = table[key]
        if isinstance(value, dict):
            lines.append("")
            _toml_dump_table(lines, prefix + [key], value)


def _toml_dumps(data: dict) -> str:
    lines: list[str] = []

    for key in sorted(data.keys()):
        value = data[key]
        if isinstance(value, dict):
            continue
        lines.append(f"{key} = {_toml_format_value(value)}")

    for key in sorted(data.keys()):
        value = data[key]
        if isinstance(value, dict):
            if lines:
                lines.append("")
            _toml_dump_table(lines, [key], value)

    if not lines:
        return ""
    return "\n".join(lines).rstrip() + "\n"


def install_mcp(agent: str) -> str:
    """Install MCP config for agent (claude, cursor, codex).

    Config locations:
    - claude: ~/.claude.json or .mcp.json (adds to mcpServers)
    - cursor: ~/.cursor/mcp.json (adds to mcpServers)
    - codex: ~/.codex/config.toml (adds to mcp_servers)
    """
    home = Path.home()
    if agent == "claude":
        project_config = Path(".mcp.json")
        path = project_config if project_config.exists() else home / ".claude.json"
        data = _load_json(path)
        data.setdefault("mcpServers", {})
        data["mcpServers"]["taskman"] = {
            "type": "stdio",
            "command": "taskman",
            "args": ["stdio"],
        }
        _write_json(path, data)
        return f"Installed taskman MCP server in {path}"

    if agent == "cursor":
        project_config = Path(".cursor") / "mcp.json"
        path = project_config if project_config.exists() else home / ".cursor" / "mcp.json"
        data = _load_json(path)
        data.setdefault("mcpServers", {})
        data["mcpServers"]["taskman"] = {
            "type": "stdio",
            "command": "taskman",
            "args": ["stdio"],
        }
        _write_json(path, data)
        return f"Installed taskman MCP server in {path}"

    if agent == "codex":
        path = home / ".codex" / "config.toml"
        data = _load_toml(path)
        data.setdefault("mcp_servers", {})
        data["mcp_servers"]["taskman"] = {
            "command": "taskman",
            "args": ["stdio"],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_toml_dumps(data), encoding="utf-8")
        return f"Installed taskman MCP server in {path}"

    raise ValueError(f"Unknown agent: {agent}")


def install_skills(agent: str) -> str:
    """Copy skill files to agent's skills directory."""
    skills_dir = Path(__file__).resolve().parent / "skills"
    if not skills_dir.is_dir():
        raise FileNotFoundError(f"skills directory not found: {skills_dir}")

    home = Path.home()
    if agent == "claude":
        base_dir = home / ".claude" / "skills"
    elif agent == "codex":
        base_dir = home / ".codex" / "skills"
    elif agent == "pi":
        base_dir = home / ".pi" / "agent" / "skills"
    else:
        raise ValueError(f"Unknown agent: {agent}")

    installed = []
    for skill_src in skills_dir.iterdir():
        if not skill_src.is_dir():
            continue
        dest_dir = base_dir / skill_src.name
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        shutil.copytree(skill_src, dest_dir)
        installed.append(skill_src.name)

    return f"Installed skills to {base_dir}: {', '.join(installed)}"


def uninstall_mcp(agent: str) -> str:
    """Remove MCP config for agent (claude, cursor, codex)."""
    home = Path.home()
    if agent == "claude":
        project_config = Path(".mcp.json")
        path = project_config if project_config.exists() else home / ".claude.json"
        if not path.exists():
            return f"No MCP config found at {path}"
        data = _load_json(path)
        servers = data.get("mcpServers")
        if isinstance(servers, dict) and "taskman" in servers:
            servers.pop("taskman", None)
            if servers:
                data["mcpServers"] = servers
            else:
                data.pop("mcpServers", None)
            _write_json(path, data)
            return f"Removed taskman MCP server from {path}"
        return f"No taskman MCP server entry found in {path}"

    if agent == "cursor":
        project_config = Path(".cursor") / "mcp.json"
        path = project_config if project_config.exists() else home / ".cursor" / "mcp.json"
        if not path.exists():
            return f"No MCP config found at {path}"
        data = _load_json(path)
        servers = data.get("mcpServers")
        if isinstance(servers, dict) and "taskman" in servers:
            servers.pop("taskman", None)
            if servers:
                data["mcpServers"] = servers
            else:
                data.pop("mcpServers", None)
            _write_json(path, data)
            return f"Removed taskman MCP server from {path}"
        return f"No taskman MCP server entry found in {path}"

    if agent == "codex":
        path = home / ".codex" / "config.toml"
        if not path.exists():
            return f"No MCP config found at {path}"
        data = _load_toml(path)
        servers = data.get("mcp_servers")
        if isinstance(servers, dict) and "taskman" in servers:
            servers.pop("taskman", None)
            if servers:
                data["mcp_servers"] = servers
            else:
                data.pop("mcp_servers", None)
            path.write_text(_toml_dumps(data), encoding="utf-8")
            return f"Removed taskman MCP server from {path}"
        return f"No taskman MCP server entry found in {path}"

    raise ValueError(f"Unknown agent: {agent}")


def uninstall_skills(agent: str) -> str:
    """Remove installed skill directories."""
    skills_dir = Path(__file__).resolve().parent / "skills"
    home = Path.home()
    if agent == "claude":
        base_dir = home / ".claude" / "skills"
    elif agent == "codex":
        base_dir = home / ".codex" / "skills"
    elif agent == "pi":
        base_dir = home / ".pi" / "agent" / "skills"
    else:
        raise ValueError(f"Unknown agent: {agent}")

    removed = []
    for skill_src in skills_dir.iterdir():
        if not skill_src.is_dir():
            continue
        dest_dir = base_dir / skill_src.name
        if dest_dir.is_dir():
            shutil.rmtree(dest_dir)
            removed.append(skill_src.name)

    if not removed:
        return f"No skills found to remove in {base_dir}"
    return f"Removed skills from {base_dir}: {', '.join(removed)}"
