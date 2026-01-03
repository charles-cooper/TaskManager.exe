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

    Returns: Revision ID and confirmation
    """
    cwd = _agent_files_cwd()
    run_jj(["status"], cwd)
    run_jj(["describe", "-m", reason], cwd)
    rev = _current_rev_id(cwd)
    return f"described {rev}: {reason}"


def sync(reason: str) -> str:
    """Full sync: describe, fetch, rebase, push.

    1. jj describe -m "<reason>"
    2. jj git fetch
    3. jj rebase -d main@origin (skip if no remote branch)
    4. Check jj status for conflicts -> return if conflicts
    5. jj git push -> return error if rejected

    Returns: Step-by-step status or conflict info
    """
    cwd = _agent_files_cwd()
    steps: list[str] = []

    run_jj(["describe", "-m", reason], cwd)
    rev = _current_rev_id(cwd)
    steps.append(f"describe: {rev}")

    run_jj(["git", "fetch"], cwd)
    steps.append("git fetch: ok")

    if _has_remote_main(cwd):
        run_jj(["rebase", "-d", "main@origin"], cwd)
        steps.append("rebase: main@origin")
    else:
        steps.append("rebase: skipped (no main@origin)")

    _, status_out, _ = run_jj(["status"], cwd)
    if _status_has_conflicts(status_out):
        return "conflicts detected:\n" + status_out

    run_jj(["git", "push"], cwd)
    steps.append("git push: ok")

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
    """Create .agent-files.git/ (bare) + .agent-files/ (clone)

    1. git init --bare .agent-files.git
    2. jj git clone .agent-files.git .agent-files
    3. Create initial files: STATUS.md, LONGTERM_MEM.md, MEDIUMTERM_MEM.md, tasks/
    4. jj describe -m "initial setup" && jj git push
    """
    cwd = Path.cwd()
    bare = cwd / ".agent-files.git"
    clone = cwd / ".agent-files"

    if bare.exists() or clone.exists():
        raise FileExistsError(".agent-files.git or .agent-files already exists")

    _run_cmd_check(["git", "init", "--bare", str(bare)], cwd=cwd)
    run_jj(["git", "clone", str(bare), str(clone)], cwd)

    (clone / "tasks").mkdir(parents=True, exist_ok=True)
    for filename in ["STATUS.md", "LONGTERM_MEM.md", "MEDIUMTERM_MEM.md"]:
        path = clone / filename
        path.touch(exist_ok=True)

    run_jj(["describe", "-m", "initial setup"], clone)
    run_jj(["git", "push"], clone)

    return "Initialized .agent-files.git and .agent-files"


def _find_agent_files_git_dir(start: Path | None = None) -> Path:
    current = Path.cwd() if start is None else Path(start)
    if current.is_file():
        current = current.parent

    while True:
        candidate = current / ".agent-files.git"
        if candidate.is_dir():
            return candidate
        if current.parent == current:
            break
        current = current.parent

    raise FileNotFoundError(".agent-files.git directory not found")


def wt() -> str:
    """Clone from root's .agent-files.git/

    1. Find root repo's .agent-files.git/ (search upward)
    2. jj git clone {root}/.agent-files.git .agent-files
    """
    cwd = Path.cwd()
    clone = cwd / ".agent-files"
    if clone.exists():
        raise FileExistsError(".agent-files already exists in this directory")

    origin = _find_agent_files_git_dir(cwd)
    run_jj(["git", "clone", str(origin), str(clone)], cwd)
    return f"Cloned .agent-files from {origin}"


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
            "args": ["serve"],
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
            "args": ["serve"],
        }
        _write_json(path, data)
        return f"Installed taskman MCP server in {path}"

    if agent == "codex":
        path = home / ".codex" / "config.toml"
        data = _load_toml(path)
        data.setdefault("mcp_servers", {})
        data["mcp_servers"]["taskman"] = {
            "command": "taskman",
            "args": ["serve"],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_toml_dumps(data), encoding="utf-8")
        return f"Installed taskman MCP server in {path}"

    raise ValueError(f"Unknown agent: {agent}")


def install_skills() -> str:
    """Copy skill files to ~/.claude/skills/"""
    skills_dir = Path(__file__).resolve().parent.parent / "skills"
    if not skills_dir.is_dir():
        raise FileNotFoundError(f"skills directory not found: {skills_dir}")

    dest_dir = Path.home() / ".claude" / "skills"
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


def uninstall_skills() -> str:
    """Remove taskman skill files from ~/.claude/skills/"""
    skills_dir = Path(__file__).resolve().parent.parent / "skills"
    if not skills_dir.is_dir():
        raise FileNotFoundError(f"skills directory not found: {skills_dir}")

    dest_dir = Path.home() / ".claude" / "skills"
    if not dest_dir.is_dir():
        return f"No skills directory found at {dest_dir}"

    count = 0
    for path in skills_dir.glob("*.md"):
        dest_path = dest_dir / path.name
        if dest_path.exists():
            dest_path.unlink()
            count += 1

    return f"Removed {count} skills from {dest_dir}"
