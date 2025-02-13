"""Tests for the BaseAgent class."""

from typing import Any

import pytest

from pepperpy.core.agents import BaseAgent


class TestAgent(BaseAgent):
    """Test implementation of BaseAgent."""

    async def analyze(
        self,
        query: str,
        depth: str = "comprehensive",
        style: str = "technical",
        **kwargs: Any,
    ) -> str:
        """Test implementation of analyze."""
        return f"Analyzed {query} with depth={depth} and style={style}"


@pytest.fixture
def test_agent() -> BaseAgent:
    """Create a test agent."""
    return TestAgent(
        name="test_agent",
        capabilities=["analyze", "research"],
        config={"style": "technical", "depth": "comprehensive"},
    )


def test_agent_initialization():
    """Test agent initialization."""
    name = "test_agent"
    capabilities = ["analyze", "research"]
    config = {"style": "technical"}

    agent = TestAgent(name=name, capabilities=capabilities, config=config)

    assert agent.name == name
    assert agent.capabilities == capabilities
    assert agent.config == config


def test_agent_initialization_default_config():
    """Test agent initialization with default config."""
    agent = TestAgent(name="test", capabilities=["analyze"])
    assert agent.config == {}


@pytest.mark.asyncio
async def test_agent_analyze():
    """Test agent analyze method."""
    agent = TestAgent(name="test", capabilities=["analyze"])
    result = await agent.analyze("test query", depth="brief", style="casual")
    assert result == "Analyzed test query with depth=brief and style=casual"


def test_agent_has_capability(test_agent: BaseAgent):
    """Test has_capability method."""
    assert test_agent.has_capability("analyze")
    assert test_agent.has_capability("research")
    assert not test_agent.has_capability("unknown")


def test_agent_validate_capabilities(test_agent: BaseAgent):
    """Test validate_capabilities method."""
    assert test_agent.validate_capabilities(["analyze"])
    assert test_agent.validate_capabilities(["analyze", "research"])
    assert not test_agent.validate_capabilities(["unknown"])
    assert not test_agent.validate_capabilities(["analyze", "unknown"])


def test_agent_get_config(test_agent: BaseAgent):
    """Test get_config method."""
    assert test_agent.get_config("style") == "technical"
    assert test_agent.get_config("depth") == "comprehensive"
    assert test_agent.get_config("unknown") is None
    assert test_agent.get_config("unknown", "default") == "default"
