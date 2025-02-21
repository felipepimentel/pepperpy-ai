"""Unit tests for the AutoGen adapter."""

import pytest

from pepperpy.adapters.autogen import AutoGenAdapter, AutoGenConfig
from pepperpy.agents.base import AgentConfig, BaseAgent
from pepperpy.workflows.base import BaseWorkflow, WorkflowConfig


class TestAutoGenAdapter(AutoGenAdapter):
    """Test AutoGen adapter implementation."""

    async def _initialize(self) -> None:
        """Initialize adapter."""
        pass

    async def _cleanup(self) -> None:
        """Clean up adapter."""
        pass


@pytest.fixture
def adapter():
    """Create AutoGen adapter."""
    config = AutoGenConfig(
        name="test_adapter",
        framework_version="0.1.0",
        llm_config={"model": "gpt-4"},
        agent_config={"temperature": 0.7},
    )
    return TestAutoGenAdapter(config=config)


@pytest.fixture
def agent():
    """Create test agent."""
    config = AgentConfig(
        name="test_agent",
        description="Test agent description",
    )
    return BaseAgent(
        name="test_agent",
        version="0.1.0",
        config=config,
    )


@pytest.fixture
def workflow():
    """Create test workflow."""
    config = WorkflowConfig(
        name="test_workflow",
        description="Test workflow description",
    )
    return BaseWorkflow(
        name="test_workflow",
        version="0.1.0",
        config=config,
    )


@pytest.mark.asyncio
async def test_adapt_agent(adapter, agent):
    """Test adapting Pepperpy agent to AutoGen agent."""
    # Adapt agent
    autogen_agent = await adapter.adapt_agent(agent)

    # Verify adaptation
    assert isinstance(autogen_agent, dict)
    assert "config" in autogen_agent
    assert "capabilities" in autogen_agent
    assert autogen_agent["config"]["name"] == "test_agent"
    assert autogen_agent["config"]["description"] == "Test agent description"
    assert autogen_agent["config"]["llm_config"] == {"model": "gpt-4"}
    assert autogen_agent["config"]["temperature"] == 0.7


@pytest.mark.asyncio
async def test_adapt_workflow(adapter, workflow):
    """Test adapting Pepperpy workflow to AutoGen workflow."""
    # Adapt workflow
    autogen_workflow = await adapter.adapt_workflow(workflow)

    # Verify adaptation
    assert isinstance(autogen_workflow, dict)
    assert "config" in autogen_workflow
    assert "capabilities" in autogen_workflow
    assert autogen_workflow["config"]["name"] == "test_workflow"
    assert autogen_workflow["config"]["description"] == "Test workflow description"
    assert autogen_workflow["config"]["llm_config"] == {"model": "gpt-4"}


@pytest.mark.asyncio
async def test_adapt_tool(adapter):
    """Test adapting Pepperpy tool to AutoGen tool."""
    # Create test tool
    tool = {
        "metadata": {
            "name": "test_tool",
            "description": "Test tool description",
        },
        "run": lambda x: x,
    }

    # Adapt tool
    autogen_tool = await adapter.adapt_tool(tool)

    # Verify adaptation
    assert isinstance(autogen_tool, dict)
    assert autogen_tool["name"] == "test_tool"
    assert autogen_tool["description"] == "Test tool description"
    assert callable(autogen_tool["run"])


@pytest.mark.asyncio
async def test_adapt_from_agent(adapter):
    """Test adapting AutoGen agent to Pepperpy agent."""
    # Create AutoGen agent
    autogen_agent = {
        "config": {
            "name": "test_agent",
            "description": "Test agent description",
            "llm_config": {"model": "gpt-4"},
        }
    }

    # Adapt agent
    pepperpy_agent = await adapter.adapt_from_agent(autogen_agent)

    # Verify adaptation
    assert isinstance(pepperpy_agent, BaseAgent)
    assert pepperpy_agent.metadata.name == "test_agent"
    assert pepperpy_agent.metadata.description == "Test agent description"


@pytest.mark.asyncio
async def test_adapt_from_workflow(adapter):
    """Test adapting AutoGen workflow to Pepperpy workflow."""
    # Create AutoGen workflow
    autogen_workflow = {
        "config": {
            "name": "test_workflow",
            "description": "Test workflow description",
            "llm_config": {"model": "gpt-4"},
        }
    }

    # Adapt workflow
    pepperpy_workflow = await adapter.adapt_from_workflow(autogen_workflow)

    # Verify adaptation
    assert isinstance(pepperpy_workflow, BaseWorkflow)
    assert pepperpy_workflow.metadata.name == "test_workflow"
    assert pepperpy_workflow.metadata.description == "Test workflow description"


@pytest.mark.asyncio
async def test_adapt_from_tool(adapter):
    """Test adapting AutoGen tool to Pepperpy tool."""
    # Create AutoGen tool
    autogen_tool = {
        "name": "test_tool",
        "description": "Test tool description",
        "run": lambda x: x,
    }

    # Adapt tool
    pepperpy_tool = await adapter.adapt_from_tool(autogen_tool)

    # Verify adaptation
    assert isinstance(pepperpy_tool, dict)
    assert pepperpy_tool["name"] == "test_tool"
    assert pepperpy_tool["description"] == "Test tool description"
    assert callable(pepperpy_tool["run"])
