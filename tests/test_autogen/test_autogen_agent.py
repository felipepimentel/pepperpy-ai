"""
Tests for the AutoGen agent plugin.
"""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from plugins.agent.autogen.provider import AutoGenAgent, ServiceMixin


@pytest.mark.asyncio
async def test_initialize():
    """Test that the agent initializes correctly."""
    # Create an agent with configuration
    agent = AutoGenAgent(config={"model": "test-model"})

    # Mock the logger
    agent.logger = MagicMock()

    # Initialize the agent
    await agent.initialize()

    # Verify initialization
    assert agent.initialized is True
    agent.logger.debug.assert_called_once()


@pytest.mark.asyncio
async def test_service_mixin():
    """Test the ServiceMixin functionality."""
    mixin = ServiceMixin()
    assert hasattr(mixin, "llm")
    assert hasattr(mixin, "memory")
    assert hasattr(mixin, "get_tool")
    assert isinstance(mixin.logger, logging.Logger)


@pytest.mark.asyncio
async def test_process_message_basic():
    """Test basic message processing without tools."""
    agent = AutoGenAgent(config={"model": "test-model"})
    agent.initialized = True

    # Mock LLM provider
    mock_llm = AsyncMock()
    mock_llm.completion.return_value = "This is a test response"

    # Patch the llm method to return our mock
    with patch.object(agent, "llm", return_value=mock_llm):
        response = await agent.process_message("Hello, how are you?")

    # Verify response
    assert response == "This is a test response"
    mock_llm.completion.assert_called_once_with("Hello, how are you?")


@pytest.mark.asyncio
async def test_execute_chat_task():
    """Test executing a chat task with message history."""
    agent = AutoGenAgent(
        config={"model": "test-model", "system_prompt": "You are a test assistant."}
    )
    agent.initialized = True

    # Mock process_message
    agent.process_message = AsyncMock(return_value="I'm a test response")

    # Execute chat task
    result = await agent.execute(
        {"task": "chat", "messages": [{"role": "user", "content": "Hello!"}]}
    )

    # Verify result
    assert result["status"] == "success"
    assert result["response"] == "I'm a test response"
    assert len(result["messages"]) == 2
    assert result["messages"][1]["role"] == "assistant"
    assert result["messages"][1]["content"] == "I'm a test response"


@pytest.mark.asyncio
async def test_extract_tool_calls():
    """Test extracting tool calls from text."""
    agent = AutoGenAgent()

    text = """
    I need to check the weather.
    
    Tool: weather_basic(location="New York", units="celsius")
    
    Let me also calculate something.
    
    Tool: calculator(expression="2+2")
    """

    tool_calls = agent._extract_tool_calls(text)

    # Verify extracted tool calls
    assert len(tool_calls) == 2
    assert tool_calls[0]["name"] == "weather_basic"
    assert tool_calls[0]["parameters"]["location"] == "New York"
    assert tool_calls[0]["parameters"]["units"] == "celsius"
    assert tool_calls[1]["name"] == "calculator"
    assert tool_calls[1]["parameters"]["expression"] == "2+2"


@pytest.mark.asyncio
async def test_tool_execution():
    """Test tool execution through prepare_response_with_tools."""
    agent = AutoGenAgent(config={"auto_tool_selection": True})
    agent.initialized = True

    # Create a message with tool usage
    message = "I'll check the weather for you. Tool: weather_basic(location=London)"

    # Create a mock for execute_tool that returns success
    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "success": True,
        "data": {"temperature": 20, "condition": "Sunny"},
    }

    agent.execute_tool = AsyncMock(return_value=mock_result)

    # Create test messages
    messages = [{"role": "user", "content": "What's the weather in London?"}]

    # Process the message with tools
    result = await agent.prepare_response_with_tools(message, [])

    # Verify tool was executed
    agent.execute_tool.assert_called_once_with("weather_basic", None, location="London")
    assert "Tool: weather_basic" in result
    assert "Result:" in result
