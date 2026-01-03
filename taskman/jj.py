import shlex
import subprocess
from pathlib import Path


def run_jj(args: list[str], cwd: Path) -> tuple[int, str, str]:
    """Run jj command with git conflict style.

    Uses --config-toml when supported, otherwise falls back to --config.
    Uses subprocess.run() - no async needed for sequential CLI commands.

    Returns: (returncode, stdout, stderr)
    Raises: RuntimeError if returncode != 0
    """
    cmd_toml = [
        "jj",
        "--config-toml",
        'ui.conflict-marker-style = "git"',
        *args,
    ]
    proc = subprocess.run(
        cmd_toml,
        cwd=str(cwd),
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0 and "unexpected argument '--config-toml'" in proc.stderr:
        cmd_legacy = [
            "jj",
            "--config",
            "ui.conflict-marker-style=git",
            *args,
        ]
        proc = subprocess.run(
            cmd_legacy,
            cwd=str(cwd),
            text=True,
            capture_output=True,
        )
        if proc.returncode != 0:
            message = (
                f"jj command failed ({proc.returncode}): {shlex.join(cmd_legacy)}\n"
                f"stdout:\n{proc.stdout}\n"
                f"stderr:\n{proc.stderr}"
            )
            raise RuntimeError(message)
        return proc.returncode, proc.stdout, proc.stderr

    if proc.returncode != 0:
        message = (
            f"jj command failed ({proc.returncode}): {shlex.join(cmd_toml)}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )
        raise RuntimeError(message)
    return proc.returncode, proc.stdout, proc.stderr


def find_agent_files_dir(start: Path | None = None) -> Path:
    """Search upward from start (default: cwd) to find .agent-files/

    Returns: Path to .agent-files/ or raises FileNotFoundError
    """
    current = Path.cwd() if start is None else Path(start)
    if current.is_file():
        current = current.parent

    while True:
        candidate = current / ".agent-files"
        if candidate.is_dir():
            return candidate
        if current.parent == current:
            break
        current = current.parent

    raise FileNotFoundError(".agent-files directory not found")
