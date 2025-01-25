"""Test tool functionality."""

from collections.abc import AsyncIterator
import pytest
from unittest.mock import AsyncMock, patch
from pepperpy.capabilities.tools.functions.serp import SerpSearchTool, SerpSearchResult
from pepperpy.capabilities.tools.functions.terminal import CommandResult, TerminalTool


@pytest.fixture
async def terminal_tool() -> AsyncIterator[TerminalTool]:
    """Create test terminal tool."""
    tool = TerminalTool()
    yield tool
    await tool.cleanup()


async def test_terminal_safe_command(terminal_tool: TerminalTool) -> None:
    """Test safe command execution."""
    result = await terminal_tool.execute(command="echo 'test'")
    assert isinstance(result.data, CommandResult)
    assert result.data.stdout == "test\n"
    assert result.data.exit_code == 0


async def test_terminal_unsafe_command(terminal_tool: TerminalTool) -> None:
    """Test unsafe command rejection."""
    result = await terminal_tool.execute(command="rm -rf /")
    assert not result.success
    assert result.error is not None
    assert isinstance(result.error, str)
    assert "not allowed" in result.error.lower()


async def test_terminal_missing_command(terminal_tool: TerminalTool) -> None:
    """Test missing command handling."""
    result = await terminal_tool.execute(command="nonexistent_command")
    assert not result.success
    assert result.error is not None
    assert isinstance(result.error, str)
    assert "not found" in result.error.lower()


@pytest.fixture
async def serp_tool() -> AsyncIterator[SerpSearchTool]:
    """Create test SERP tool."""
    tool = SerpSearchTool()
    yield tool
    await tool.cleanup()


async def test_serp_search_news(serp_tool: SerpSearchTool) -> None:
    """Test news search."""
    result = await serp_tool.execute(
        query="test query",
        num_results=1
    )

    if result.success:
        assert isinstance(result.data, list)
        assert len(result.data) == 1
        assert isinstance(result.data[0], SerpSearchResult)
        assert result.data[0].title
        assert result.data[0].link
        assert result.data[0].snippet
    else:
        # API might be unavailable, skip test
        pytest.skip("SERP API unavailable") 