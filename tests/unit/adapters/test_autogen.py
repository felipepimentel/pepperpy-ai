"""Tests for AutoGen adapter.

This module contains tests for the AutoGen framework adapter.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from pepperpy.adapters.autogen import (
    AutoGenAdapter,
    AutoGenMessage,
)
from pepperpy.adapters.errors import ConversionError
from pepperpy.core.types import Message, MessageType, Response, ResponseStatus


@pytest.fixture
def mock_agent():
    """Create a mock Pepperpy agent."""
    agent = AsyncMock()
    agent.name = "test_agent"
    agent.process = AsyncMock()
    return agent


@pytest.fixture
def adapter(mock_agent):
    """Create an AutoGen adapter instance."""
    return AutoGenAdapter(agent=mock_agent)


@pytest.mark.asyncio
async def test_to_framework_agent_no_autogen(adapter):
    """Test conversion to framework agent when AutoGen is not installed."""
    with patch("pepperpy.adapters.autogen.has_autogen", False):
        with pytest.raises(ConversionError) as exc_info:
            await adapter.to_framework_agent()
        assert "AutoGen is not installed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_to_framework_agent_success(adapter):
    """Test successful conversion to framework agent."""
    with patch("pepperpy.adapters.autogen.has_autogen", True):
        agent = await adapter.to_framework_agent()
        assert agent.name == "test_agent"
        assert hasattr(agent, "send")
        assert hasattr(agent, "receive")


@pytest.mark.asyncio
async def test_from_framework_message(adapter):
    """Test conversion from AutoGen message to Pepperpy message."""
    autogen_msg = AutoGenMessage(
        sender="sender",
        receiver="receiver",
        content="test message",
    )

    message = await adapter.from_framework_message(autogen_msg)

    assert isinstance(message, Message)
    assert message.type == MessageType.QUERY
    assert message.content == {"text": "test message"}
    assert isinstance(message.id, UUID)


@pytest.mark.asyncio
async def test_to_framework_message(adapter):
    """Test conversion from Pepperpy message to AutoGen message."""
    pepperpy_msg = Message(
        type=MessageType.QUERY,
        content={"text": "test message"},
        id=UUID("12345678-1234-5678-1234-567812345678"),
    )

    message = await adapter.to_framework_message(pepperpy_msg)

    assert isinstance(message, dict)
    assert message["content"] == "test message"


@pytest.mark.asyncio
async def test_from_framework_response(adapter):
    """Test conversion from AutoGen response to Pepperpy response."""
    autogen_resp = AutoGenMessage(
        sender="sender",
        receiver="receiver",
        content="test response",
    )

    response = await adapter.from_framework_response(autogen_resp)

    assert isinstance(response, Response)
    assert response.status == ResponseStatus.SUCCESS
    assert response.content["content"] == {"text": "test response"}
    assert isinstance(response.id, UUID)
    assert isinstance(response.message_id, str)
    assert len(response.message_id) > 0


@pytest.mark.asyncio
async def test_to_framework_response(adapter):
    """Test conversion from Pepperpy response to AutoGen response."""
    pepperpy_resp = Response(
        message_id="12345678-1234-5678-1234-567812345678",
        status=ResponseStatus.SUCCESS,
        content={"type": MessageType.RESPONSE, "content": {"text": "test response"}},
        id=UUID("87654321-4321-8765-4321-876543210987"),
    )

    response = await adapter.to_framework_response(pepperpy_resp)

    assert isinstance(response, dict)
    assert response["content"] == "test response"


@pytest.mark.asyncio
async def test_framework_agent_receive(adapter, mock_agent):
    """Test framework agent receive method."""
    with patch("pepperpy.adapters.autogen.has_autogen", True):
        agent = await adapter.to_framework_agent()

        # Setup mock response
        mock_agent.process.return_value = Response(
            message_id="12345678-1234-5678-1234-567812345678",
            status=ResponseStatus.SUCCESS,
            content={
                "type": MessageType.RESPONSE,
                "content": {"text": "processed response"},
            },
            id=UUID("87654321-4321-8765-4321-876543210987"),
        )

        # Create test message
        message = AutoGenMessage(
            sender="test_sender",
            receiver="test_receiver",
            content="test message",
        )

        # Test receive method
        await agent.receive(message, MagicMock())

        # Verify agent.process was called
        mock_agent.process.assert_called_once()
        call_arg = mock_agent.process.call_args[0][0]
        assert isinstance(call_arg, Message)
        assert call_arg.content == {"text": "test message"}


@pytest.mark.asyncio
async def test_conversion_error_handling(adapter):
    """Test error handling during conversions."""
    # Test from_framework_message error
    with pytest.raises(ConversionError):
        await adapter.from_framework_message({"invalid": "message"})  # type: ignore

    # Test to_framework_message error
    invalid_msg = Message(
        type=MessageType.QUERY,
        content={},  # Missing text field
        id=UUID("12345678-1234-5678-1234-567812345678"),
    )
    message = await adapter.to_framework_message(invalid_msg)
    assert message["content"] == ""  # Should handle missing text gracefully

    # Test from_framework_response error
    with pytest.raises(ConversionError):
        await adapter.from_framework_response({"invalid": "response"})  # type: ignore
