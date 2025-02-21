"""Unit tests for the LangChain adapter."""

import pytest
from langchain.agents import AgentExecutor, Tool
from langchain.chains import LLMChain
from langchain.llms.base import BaseLLM
from langchain.schema import Generation, LLMResult

from pepperpy.adapters.langchain import LangChainAdapter, LangChainConfig
from pepperpy.agents.base import AgentConfig, BaseAgent
from pepperpy.workflows.base import BaseWorkflow, WorkflowConfig


class MockLLM(BaseLLM):
    """Mock LLM for testing."""

    def _call(self, prompt: str, stop=None, **kwargs):
        """Mock LLM call."""
        return "Mock response"

    def _generate(self, prompts, stop=None, **kwargs) -> LLMResult:
        """Mock LLM generation."""
        return LLMResult(
            generations=[[Generation(text="Mock response")] for _ in prompts]
        )

    @property
    def _llm_type(self):
        """Get LLM type."""
        return "mock"


class TestLangChainAdapter(LangChainAdapter):
    """Test LangChain adapter implementation."""

    async def _initialize(self) -> None:
        """Initialize adapter."""
        pass

    async def _cleanup(self) -> None:
        """Clean up adapter."""
        pass


@pytest.fixture
def mock_llm():
    """Create mock LLM."""
    return MockLLM()


@pytest.fixture
def adapter():
    """Create LangChain adapter."""
    config = LangChainConfig(
        name="test_adapter",
        framework_version="0.1.0",
        llm_config={"llm": MockLLM()},
        agent_config={"handle_parsing_errors": True},
    )
    return TestLangChainAdapter(config=config)


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
    """Test adapting Pepperpy agent to LangChain agent."""
    # Adapt agent
    langchain_agent = await adapter.adapt_agent(agent)

    # Verify adaptation
    assert isinstance(langchain_agent, AgentExecutor)
    assert langchain_agent.agent is not None
    assert len(langchain_agent.tools) > 0


@pytest.mark.asyncio
async def test_adapt_workflow(adapter, workflow):
    """Test adapting Pepperpy workflow to LangChain chain."""
    # Adapt workflow
    langchain_chain = await adapter.adapt_workflow(workflow)

    # Verify adaptation
    assert isinstance(langchain_chain, LLMChain)
    assert langchain_chain.llm is not None
    assert langchain_chain.prompt is not None


@pytest.mark.asyncio
async def test_adapt_tool(adapter):
    """Test adapting Pepperpy tool to LangChain tool."""
    # Create test tool
    tool = {
        "metadata": {
            "name": "test_tool",
            "description": "Test tool description",
        },
        "run": lambda x: x,
    }

    # Adapt tool
    langchain_tool = await adapter.adapt_tool(tool)

    # Verify adaptation
    assert isinstance(langchain_tool, Tool)
    assert langchain_tool.name == "test_tool"
    assert langchain_tool.description == "Test tool description"
    assert callable(langchain_tool.func)


@pytest.mark.asyncio
async def test_adapt_from_agent(adapter):
    """Test adapting LangChain agent to Pepperpy agent."""
    # Create LangChain agent
    tools = [
        Tool(
            name="test_tool",
            func=lambda x: x,
            description="Test tool",
        )
    ]
    llm_chain = LLMChain(
        llm=MockLLM(),
        prompt=None,
    )
    langchain_agent = AgentExecutor.from_agent_and_tools(
        agent=llm_chain,
        tools=tools,
    )

    # Adapt agent
    pepperpy_agent = await adapter.adapt_from_agent(langchain_agent)

    # Verify adaptation
    assert isinstance(pepperpy_agent, BaseAgent)
    assert pepperpy_agent.metadata.name == "unknown"


@pytest.mark.asyncio
async def test_adapt_from_workflow(adapter):
    """Test adapting LangChain chain to Pepperpy workflow."""
    # Create LangChain chain
    langchain_chain = LLMChain(
        llm=MockLLM(),
        prompt=None,
    )

    # Adapt workflow
    pepperpy_workflow = await adapter.adapt_from_workflow(langchain_chain)

    # Verify adaptation
    assert isinstance(pepperpy_workflow, BaseWorkflow)
    assert pepperpy_workflow.metadata.name == "unknown"


@pytest.mark.asyncio
async def test_adapt_from_tool(adapter):
    """Test adapting LangChain tool to Pepperpy tool."""
    # Create LangChain tool
    langchain_tool = Tool(
        name="test_tool",
        func=lambda x: x,
        description="Test tool",
    )

    # Adapt tool
    pepperpy_tool = await adapter.adapt_from_tool(langchain_tool)

    # Verify adaptation
    assert isinstance(pepperpy_tool, dict)
    assert pepperpy_tool["name"] == "test_tool"
    assert pepperpy_tool["description"] == "Test tool"
    assert callable(pepperpy_tool["run"])
