"""Tests for the chain topology provider."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pepperpy.agent.topology.base import TopologyError
from plugins.agent.topology.chain.provider import ChainTopologyProvider


@pytest.fixture
def mock_agent():
    """Create a mock agent."""
    agent = AsyncMock()
    agent.process_message = AsyncMock(return_value="Agent output")
    return agent


@pytest.fixture
def chain_provider():
    """Create a chain topology provider with mock configuration."""
    provider = ChainTopologyProvider(
        config={
            "chain_direction": "linear",
            "max_iterations": 2,
            "agent_order": ["agent1", "agent2"],
            "agents": {
                "agent1": {"provider": "test", "model": "test-model"},
                "agent2": {"provider": "test", "model": "test-model"},
            },
        }
    )
    # Mock the logger
    provider.logger = MagicMock()
    return provider


@pytest.mark.asyncio
async def test_initialization(chain_provider):
    """Test provider initialization."""
    with patch("pepperpy.agent.create_agent", return_value=AsyncMock()) as mock_create:
        await chain_provider.initialize()

        # Verify agent creation
        assert mock_create.call_count == 2
        assert len(chain_provider.agents) == 2
        assert chain_provider.agent_order == ["agent1", "agent2"]
        assert chain_provider.chain_direction == "linear"
        assert chain_provider.max_iterations == 2


@pytest.mark.asyncio
async def test_initialization_error(chain_provider):
    """Test initialization with error."""
    with patch("pepperpy.agent.create_agent", side_effect=Exception("Test error")):
        with pytest.raises(TopologyError):
            await chain_provider.initialize()

        assert chain_provider.logger.error.called


@pytest.mark.asyncio
async def test_linear_chain_execution(chain_provider, mock_agent):
    """Test linear chain execution."""
    chain_provider.agents = {"agent1": mock_agent, "agent2": mock_agent}
    chain_provider.initialized = True

    result = await chain_provider.execute({"task": "run_chain", "content": "Test task"})

    assert result["status"] == "success"
    assert result["result"] == "Agent output"
    assert len(result["steps"]) == 4  # 2 iterations * 2 agents
    assert mock_agent.process_message.call_count == 4


@pytest.mark.asyncio
async def test_bidirectional_chain_execution(chain_provider, mock_agent):
    """Test bidirectional chain execution."""
    chain_provider.agents = {"agent1": mock_agent, "agent2": mock_agent}
    chain_provider.initialized = True
    chain_provider.chain_direction = "bidirectional"

    result = await chain_provider.execute({"task": "run_chain", "content": "Test task"})

    assert result["status"] == "success"
    assert result["result"] == "Agent output"
    # 2 iterations * 2 agents * 2 directions
    assert len(result["steps"]) == 8
    assert mock_agent.process_message.call_count == 8


@pytest.mark.asyncio
async def test_agent_error_handling(chain_provider, mock_agent):
    """Test error handling during chain execution."""
    error_agent = AsyncMock()
    error_agent.process_message = AsyncMock(side_effect=Exception("Agent error"))

    chain_provider.agents = {"agent1": mock_agent, "agent2": error_agent}
    chain_provider.initialized = True

    result = await chain_provider.execute({"task": "run_chain", "content": "Test task"})

    assert result["status"] == "error"
    assert mock_agent.process_message.call_count == 1
    assert error_agent.process_message.call_count == 1


@pytest.mark.asyncio
async def test_set_agent_order(chain_provider):
    """Test setting agent order."""
    chain_provider.agents = {
        "agent1": AsyncMock(),
        "agent2": AsyncMock(),
        "agent3": AsyncMock(),
    }
    chain_provider.initialized = True

    result = await chain_provider.execute(
        {"task": "set_agent_order", "agent_order": ["agent3", "agent1", "agent2"]}
    )

    assert result["status"] == "success"
    assert chain_provider.agent_order == ["agent3", "agent1", "agent2"]


@pytest.mark.asyncio
async def test_set_invalid_agent_order(chain_provider):
    """Test setting invalid agent order."""
    chain_provider.agents = {"agent1": AsyncMock(), "agent2": AsyncMock()}
    chain_provider.initialized = True

    result = await chain_provider.execute(
        {
            "task": "set_agent_order",
            "agent_order": ["agent3"],  # invalid agent ID
        }
    )

    assert result["status"] == "error"
    assert "Invalid agent ID" in result["message"]


@pytest.mark.asyncio
async def test_get_agent_order(chain_provider):
    """Test getting agent order."""
    chain_provider.initialized = True
    chain_provider.agent_order = ["agent2", "agent1"]

    result = await chain_provider.execute({"task": "get_agent_order"})

    assert result["status"] == "success"
    assert result["agent_order"] == ["agent2", "agent1"]


@pytest.mark.asyncio
async def test_invalid_task(chain_provider):
    """Test execution with invalid task."""
    chain_provider.initialized = True

    result = await chain_provider.execute({"task": "invalid_task"})

    assert result["status"] == "error"
    assert "Unknown task" in result["message"]


@pytest.mark.asyncio
async def test_missing_task(chain_provider):
    """Test execution with missing task."""
    chain_provider.initialized = True

    result = await chain_provider.execute({})

    assert result["status"] == "error"
    assert "No task specified" in result["message"]


@pytest.mark.asyncio
async def test_missing_content(chain_provider):
    """Test run_chain with missing content."""
    chain_provider.initialized = True

    result = await chain_provider.execute({"task": "run_chain"})

    assert result["status"] == "error"
    assert "No content provided" in result["message"]


@pytest.mark.asyncio
async def test_cleanup(chain_provider, mock_agent):
    """Test cleanup method properly releases resources."""
    # Setup agents
    agent1 = mock_agent
    agent2 = mock_agent
    chain_provider.agents = {"agent1": agent1, "agent2": agent2}
    chain_provider.initialized = True

    # Call cleanup
    await chain_provider.cleanup()

    # Verify agent cleanup was called
    assert chain_provider.logger.error.call_count == 0  # No errors
    assert not chain_provider.initialized  # Should be reset to False
