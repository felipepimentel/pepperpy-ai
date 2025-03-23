"""Tests for the AutoGen provider implementation."""

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pepperpy.agents.provider import Message
from pepperpy.agents.providers.autogen import AutoGenConfig, AutoGenProvider


@pytest.fixture
def mock_assistant():
    """Create a mock AssistantAgent."""
    mock = MagicMock()
    mock.name = "assistant"
    mock.register_reply = MagicMock()
    return mock


@pytest.fixture
def mock_user_proxy():
    """Create a mock UserProxyAgent."""
    mock = MagicMock()
    mock.name = "user"
    mock.register_reply = MagicMock()
    mock.a_initiate_chat = AsyncMock()
    return mock


@pytest.fixture
def config():
    """Create a test configuration."""
    return AutoGenConfig(
        name="test_assistant",
        description="Test assistant for unit tests",
        llm_config={
            "config_list": [{"model": "gpt-4", "api_key": "test-key"}],
            "temperature": 0,
        },
    )


@pytest.mark.asyncio
async def test_initialize(config, mock_assistant, mock_user_proxy):
    """Test provider initialization."""
    with (
        patch("pepperpy.agents.providers.autogen.AssistantAgent") as mock_assistant_cls,
        patch(
            "pepperpy.agents.providers.autogen.UserProxyAgent"
        ) as mock_user_proxy_cls,
    ):
        mock_assistant_cls.return_value = mock_assistant
        mock_user_proxy_cls.return_value = mock_user_proxy

        provider = AutoGenProvider()
        await provider.initialize(config)

        assert provider.config == config
        assert provider.assistant == mock_assistant
        assert provider.user_proxy == mock_user_proxy

        mock_assistant_cls.assert_called_once()
        mock_user_proxy_cls.assert_called_once()


@pytest.mark.asyncio
async def test_execute(config, mock_assistant, mock_user_proxy):
    """Test task execution."""
    with (
        patch("pepperpy.agents.providers.autogen.AssistantAgent") as mock_assistant_cls,
        patch(
            "pepperpy.agents.providers.autogen.UserProxyAgent"
        ) as mock_user_proxy_cls,
    ):
        mock_assistant_cls.return_value = mock_assistant
        mock_user_proxy_cls.return_value = mock_user_proxy

        # Set up test data
        task = "Write a function to add two numbers"
        context = {"language": "python"}

        # Initialize provider
        provider = AutoGenProvider()
        await provider.initialize(config)

        # Execute task
        messages = await provider.execute(task, context)

        # Verify interactions
        mock_user_proxy.a_initiate_chat.assert_called_once_with(
            mock_assistant,
            message=task,
            context=context,
        )

        # Verify callbacks were registered
        assert mock_assistant.register_reply.called
        assert mock_user_proxy.register_reply.called


@pytest.mark.asyncio
async def test_execute_without_initialization():
    """Test execution without initialization."""
    provider = AutoGenProvider()
    with pytest.raises(RuntimeError, match="Provider not initialized"):
        await provider.execute("test task")


@pytest.mark.asyncio
async def test_message_callback(config, mock_assistant, mock_user_proxy):
    """Test message callback functionality."""
    with (
        patch("pepperpy.agents.providers.autogen.AssistantAgent") as mock_assistant_cls,
        patch(
            "pepperpy.agents.providers.autogen.UserProxyAgent"
        ) as mock_user_proxy_cls,
    ):
        mock_assistant_cls.return_value = mock_assistant
        mock_user_proxy_cls.return_value = mock_user_proxy

        provider = AutoGenProvider()
        await provider.initialize(config)

        # Simulate message callback
        test_message: Dict[str, Any] = {
            "content": "Test message",
            "type": "message",
        }

        # Get the callback function
        callback = mock_assistant.register_reply.call_args[1]["callback"]

        # Call the callback with test data
        callback(test_message, mock_assistant, mock_user_proxy)

        # Execute task to get messages
        messages = await provider.execute("test task")

        # Verify message was captured
        assert len(messages) == 1
        assert isinstance(messages[0], Message)
        assert messages[0].role == "assistant"
        assert messages[0].content == "Test message"
        assert messages[0].metadata["sender"] == "assistant"
        assert messages[0].metadata["receiver"] == "user"


@pytest.mark.asyncio
async def test_shutdown(config, mock_assistant, mock_user_proxy):
    """Test provider shutdown."""
    with (
        patch("pepperpy.agents.providers.autogen.AssistantAgent") as mock_assistant_cls,
        patch(
            "pepperpy.agents.providers.autogen.UserProxyAgent"
        ) as mock_user_proxy_cls,
    ):
        mock_assistant_cls.return_value = mock_assistant
        mock_user_proxy_cls.return_value = mock_user_proxy

        provider = AutoGenProvider()
        await provider.initialize(config)
        await provider.shutdown()

        assert provider.assistant is None
        assert provider.user_proxy is None
