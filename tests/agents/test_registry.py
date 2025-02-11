"""Tests for the agent registry module."""

from unittest.mock import Mock

import pytest

from pepper_hub.agents.base import AgentConfig, BaseAgent
from pepper_hub.agents.registry import AgentRegistry
from pepper_hub.prompts import PromptRegistry


class MockAgent(BaseAgent):
    """Mock agent for testing."""

    def __init__(self, config: AgentConfig, prompt_registry: PromptRegistry):
        """Initialize the mock agent.

        Args:
            config: The agent configuration.
            prompt_registry: The prompt registry.

        """
        super().__init__(config=config, prompt_registry=prompt_registry)

    async def run(self, *args, **kwargs):
        """Mock run method."""
        return "mock_response"


@pytest.fixture
def mock_prompt_registry():
    """Create a mock prompt registry."""
    return Mock(spec=PromptRegistry)


@pytest.fixture
def mock_config():
    """Create a mock agent configuration."""
    return AgentConfig(
        name="test_agent",
        description="A test agent",
        provider="test_provider",
        model="test_model",
        memory=None,
        prompts={},
        parameters={"temperature": 0.7},
    )


def test_agent_registry_initialization():
    """Test that the agent registry can be initialized."""
    registry = AgentRegistry()
    assert isinstance(registry, AgentRegistry)
    assert registry._agents == {}


def test_agent_registration(mock_config, mock_prompt_registry):
    """Test registering and retrieving agents."""
    registry = AgentRegistry()
    registry.register_agent("mock", MockAgent)
    assert registry.get("mock") == MockAgent

    # Test loading an agent instance
    agent = registry.load_agent("mock", mock_config, mock_prompt_registry)
    assert isinstance(agent, MockAgent)


def test_duplicate_registration():
    """Test that registering the same name twice raises an error."""
    registry = AgentRegistry()
    registry.register_agent("mock", MockAgent)
    with pytest.raises(ValueError, match="Agent 'mock' is already registered"):
        registry.register_agent("mock", MockAgent)


def test_get_nonexistent_agent():
    """Test that getting a non-existent agent raises an error."""
    registry = AgentRegistry()
    with pytest.raises(KeyError, match="No agent registered under name 'nonexistent'"):
        registry.get("nonexistent")


def test_has_agent():
    """Test checking if an agent exists."""
    registry = AgentRegistry()
    assert not registry.has_agent("mock")
    registry.register_agent("mock", MockAgent)
    assert registry.has_agent("mock")


def test_list_agents():
    """Test listing registered agents."""
    registry = AgentRegistry()
    assert registry.list_agents() == []

    registry.register_agent("mock1", MockAgent)
    registry.register_agent("mock2", MockAgent)
    assert sorted(registry.list_agents()) == ["mock1", "mock2"]
