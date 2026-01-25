import json
import re
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


def _has_remote_main(cwd: Path) -> bool:
    try:
        run_jj(["log", "-r", "main@origin", "--no-graph", "-T", "commit_id"], cwd)
    except RuntimeError:
        return False
    return True


def _is_main_tracked(cwd: Path) -> bool:
    """Check if main@origin is tracked (linked to local main)."""
    _, out, _ = run_jj(["bookmark", "list", "--all"], cwd)
    # Tracked: "main: xyz abc" with "main@origin" on separate line
    # Untracked: "main@origin [new] untracked"
    for line in out.splitlines():
        if "main@origin" in line and "untracked" in line:
            return False
    return True


def _setup_main_bookmark(cwd: Path) -> None:
    """Ensure main bookmark exists, tracks main@origin, and points to @."""
    # Track main@origin if exists and untracked
    if _has_remote_main(cwd) and not _is_main_tracked(cwd):
        run_jj(["bookmark", "track", "main@origin"], cwd)

    # Set main bookmark to current revision (creates if doesn't exist)
    try:
        run_jj(["bookmark", "set", "main", "-r", "@"], cwd)
    except RuntimeError as exc:
        # If bookmark doesn't exist, create it
        if "no such bookmark" in str(exc).lower():
            run_jj(["bookmark", "create", "main", "-r", "@"], cwd)
        else:
            raise


def _status_has_conflicts(status_out: str) -> bool:
    return bool(re.search(r"(?im)^(conflicts|conflicted)\b", status_out))


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


def sync(reason: str) -> str:
    """Full sync: describe, fetch, rebase, push, new.

    1. jj describe -m "<reason>"
    2. jj git fetch
    3. jj rebase -d main@origin (skip if no remote branch)
    4. Check jj status for conflicts -> return if conflicts
    5. jj git push -> return error if rejected
    6. jj new (start fresh working copy)

    Returns: Step-by-step status or conflict info
    """
    cwd = _agent_files_cwd()
    steps: list[str] = []

    run_jj(["describe", "-m", reason], cwd)
    rev = _current_rev_id(cwd)
    steps.append(f"rev: {rev}")

    run_jj(["git", "fetch"], cwd)
    steps.append("git fetch: ok")

    has_remote = _has_remote_main(cwd)
    if has_remote:
        run_jj(["rebase", "-d", "main@origin"], cwd)
        steps.append("rebase: main@origin")
    else:
        steps.append("rebase: skipped (no main@origin)")

    _, status_out, _ = run_jj(["status"], cwd)
    if _status_has_conflicts(status_out):
        return "conflicts detected:\n" + status_out

    _setup_main_bookmark(cwd)

    try:
        # Use --all for first push (no remote yet), regular push otherwise
        push_cmd = ["git", "push"] if has_remote else ["git", "push", "--all"]
        run_jj(push_cmd, cwd)
        steps.append("git push: ok")
        # Start fresh working copy so subsequent edits don't modify pushed commit
        run_jj(["new"], cwd)
    except RuntimeError as exc:
        err_msg = str(exc)
        steps.append("git push: FAILED")
        # Extract useful info from jj error
        if "no author" in err_msg.lower() or "no committer" in err_msg.lower():
            steps.append("Error: commit has no author/committer set")
            steps.append("Fix: jj config set --user user.name 'Your Name'")
            steps.append("     jj config set --user user.email 'you@example.com'")
        elif "rejected" in err_msg.lower() or "non-fast-forward" in err_msg.lower():
            steps.append("Error: push rejected (remote changed)")
            steps.append("Recovery: jj git fetch && jj rebase -d main@origin && jj git push")
        else:
            steps.append(err_msg)
        return "\n".join(steps)

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
    run_jj(["bookmark", "create", "main", "-r", "@"], agent_files)
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
            jj_path = candidate / ".jj"
            if jj_path.is_dir():
                # This is the main workspace
                return candidate
            elif jj_path.is_file():
                # This is a linked workspace - read the pointer to find main
                # .jj file contains path to the main repo's .jj directory
                pointer = jj_path.read_text().strip()
                # pointer is path to .jj dir, parent is .agent-files
                return Path(pointer).parent
        if current.parent == current:
            break
        current = current.parent

    raise FileNotFoundError(".agent-files directory not found")


def _is_main_workspace(agent_files: Path) -> bool:
    """Check if agent_files is the main workspace (has .jj/ directory)."""
    jj_path = agent_files / ".jj"
    return jj_path.is_dir()


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

        # Create jj workspace for .agent-files
        workspace_agent_files = worktree_dir / ".agent-files"
        run_jj(["workspace", "add", str(workspace_agent_files)], main_agent_files)

        return f"Created worktree at worktrees/{name}/ with .agent-files workspace"
    else:
        if in_main_repo:
            raise ValueError("Use 'taskman wt <name>' to create a worktree")

        workspace_agent_files = cwd / ".agent-files"
        if workspace_agent_files.exists():
            raise FileExistsError(".agent-files already exists")

        # Create jj workspace for .agent-files
        run_jj(["workspace", "add", str(workspace_agent_files)], main_agent_files)

        return f"Created .agent-files workspace (linked to {main_agent_files})"



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
        dest_dir = home / ".claude" / "skills" / "taskman"
    elif agent == "codex":
        dest_dir = home / ".codex" / "skills" / "taskman"
    elif agent == "pi":
        dest_dir = home / ".pi" / "agent" / "skills" / "taskman"
    else:
        raise ValueError(f"Unknown agent: {agent}")

    dest_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for path in skills_dir.glob("*.md"):
        shutil.copy2(path, dest_dir / path.name)
        count += 1

    return f"Installed {count} skills to {dest_dir}"


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
    """Remove taskman skill files from agent's skills directory."""
    home = Path.home()
    if agent == "claude":
        dest_dir = home / ".claude" / "skills" / "taskman"
    elif agent == "codex":
        dest_dir = home / ".codex" / "skills" / "taskman"
    elif agent == "pi":
        dest_dir = home / ".pi" / "agent" / "skills" / "taskman"
    else:
        raise ValueError(f"Unknown agent: {agent}")

    if not dest_dir.is_dir():
        return f"No skills directory found at {dest_dir}"

    count = 0
    for path in dest_dir.glob("*.md"):
        path.unlink()
        count += 1

    # Remove the taskman directory if empty
    if dest_dir.is_dir() and not any(dest_dir.iterdir()):
        dest_dir.rmdir()

    return f"Removed {count} skills from {dest_dir}"
