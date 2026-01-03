import pytest
from taskman.server import mcp


def test_mcp_has_describe_tool():
    """MCP server exposes describe tool"""
    tools = [t.name for t in mcp.list_tools()]
    assert "describe" in tools


def test_mcp_has_sync_tool():
    """MCP server exposes sync tool"""
    tools = [t.name for t in mcp.list_tools()]
    assert "sync" in tools


def test_mcp_has_history_tools():
    """MCP server exposes history tools"""
    tools = [t.name for t in mcp.list_tools()]
    assert "history_diffs" in tools
    assert "history_batch" in tools
    assert "history_search" in tools
