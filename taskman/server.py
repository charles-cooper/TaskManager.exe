import asyncio
from mcp.server.fastmcp import FastMCP

from taskman import core


class _SyncMCP:
    def __init__(self, inner: FastMCP) -> None:
        self._inner = inner

    def list_tools(self):
        return asyncio.run(self._inner.list_tools())

    def __getattr__(self, name):
        return getattr(self._inner, name)


mcp = _SyncMCP(FastMCP("taskman"))


@mcp.tool()
def describe(reason: str) -> str:
    """Create named checkpoint."""
    return core.describe(reason)


@mcp.tool()
def sync(reason: str) -> str:
    """Full sync: describe, fetch, rebase, push."""
    return core.sync(reason)


@mcp.tool()
def history_diffs(file: str, start_rev: str, end_rev: str = "@") -> str:
    """Get all diffs for file across revision range."""
    return core.history_diffs(file, start_rev, end_rev)


@mcp.tool()
def history_batch(file: str, start_rev: str, end_rev: str = "@") -> str:
    """Fetch file content at all revisions in range."""
    return core.history_batch(file, start_rev, end_rev)


@mcp.tool()
def history_search(pattern: str, file: str | None = None, limit: int = 20) -> str:
    """Search history for pattern in diffs."""
    return core.history_search(pattern, file, limit)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
