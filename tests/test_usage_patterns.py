"""Test all documented usage patterns."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from pepperpy import Pepperpy
from pepperpy.core.errors import ConfigurationError, PepperpyError
from pepperpy.core.types import MessageContent, MessageType, Response


@pytest.fixture
async def mock_client():
    """Create a mock Pepperpy client."""
    with patch("pepperpy.PepperpyClient") as mock:
        client = AsyncMock()
        mock.return_value = client
        yield client


@pytest.fixture
async def pepper(mock_client):
    """Create a Pepperpy instance with mocked client."""
    instance = await Pepperpy.create()
    return instance


@pytest.mark.asyncio
async def test_basic_usage(pepper: Pepperpy, mock_client: AsyncMock):
    """Test basic usage patterns."""
    # Test ask method
    mock_client.run.return_value = "Test response"
    result = await pepper.ask("What is AI?")
    assert result == "Test response"
    mock_client.run.assert_called_once()

    # Test ask with options
    await pepper.ask(
        "What is AI?",
        style="concise",
        format="text",
        temperature=0.7,
        max_tokens=2048,
    )
    mock_client.run.assert_called_with(
        "assistant",
        "ask",
        question="What is AI?",
        style="concise",
        format="text",
        temperature=0.7,
        max_tokens=2048,
    )


@pytest.mark.asyncio
async def test_research(pepper: Pepperpy, mock_client: AsyncMock):
    """Test research functionality."""
    mock_client.run.return_value = {
        "tldr": "Quick summary",
        "full": "Full report",
        "bullets": ["Point 1", "Point 2"],
        "references": ["Source 1", "Source 2"],
    }

    result = await pepper.research(
        "Impact of AI",
        depth="comprehensive",
        style="academic",
        format="report",
        max_sources=10,
    )

    assert result.tldr == "Quick summary"
    assert result.full == "Full report"
    assert result.bullets == ["Point 1", "Point 2"]
    assert result.references == ["Source 1", "Source 2"]

    mock_client.run.assert_called_with(
        "research_assistant",
        "research",
        topic="Impact of AI",
        depth="comprehensive",
        style="academic",
        format="report",
        max_sources=10,
    )


@pytest.mark.asyncio
async def test_stream_response(pepper: Pepperpy, mock_client: AsyncMock):
    """Test streaming response functionality."""
    message_id = str(uuid4())
    mock_responses = [
        Response(
            message_id=message_id,
            content=MessageContent(
                type=MessageType.RESPONSE,
                content={"text": "Hello"},
            ),
        ),
        Response(
            message_id=message_id,
            content=MessageContent(
                type=MessageType.RESPONSE,
                content={"text": " world"},
            ),
        ),
        Response(
            message_id=message_id,
            content=MessageContent(
                type=MessageType.RESPONSE,
                content={"text": "!"},
            ),
        ),
    ]
    mock_client.stream_chat.return_value = mock_responses

    collected_response = ""
    async for token in pepper.stream_response(
        "Test message",
        style="technical",
        format="text",
        temperature=0.8,
    ):
        collected_response += token

    assert collected_response == "Hello world!"
    mock_client.stream_chat.assert_called_once()


@pytest.mark.asyncio
async def test_analyze(pepper: Pepperpy, mock_client: AsyncMock):
    """Test text analysis functionality."""
    mock_analysis = {
        "summary": "Test summary",
        "key_points": ["Point 1", "Point 2"],
        "sentiment": "positive",
    }
    mock_client.run.return_value = mock_analysis

    result = await pepper.analyze(
        "Sample text",
        focus="sentiment",
        depth="detailed",
    )

    assert result == mock_analysis
    mock_client.run.assert_called_with(
        "researcher",
        "analyze",
        text="Sample text",
        focus="sentiment",
        depth="detailed",
    )


@pytest.mark.asyncio
async def test_collaborate(pepper: Pepperpy, mock_client: AsyncMock):
    """Test collaboration functionality."""
    mock_result = {"status": "completed", "output": "Collaboration result"}
    mock_client.run.return_value = mock_result

    result = await pepper.collaborate(
        "Research and write about AI",
        team_name="research-team",
        workflow_name="research-workflow",
    )

    assert result == mock_result
    mock_client.run.assert_called_with(
        "research-team",
        "research-workflow",
        task="Research and write about AI",
    )


@pytest.mark.asyncio
async def test_error_handling(pepper: Pepperpy, mock_client: AsyncMock):
    """Test error handling in various scenarios."""
    # Test configuration error
    with pytest.raises(ConfigurationError):
        await Pepperpy.create(api_key="invalid")

    # Test runtime error
    mock_client.run.side_effect = PepperpyError("Test error")
    with pytest.raises(PepperpyError) as exc_info:
        await pepper.ask("What is AI?")
    assert str(exc_info.value) == "Test error"

    # Test streaming error
    mock_client.stream_chat.side_effect = PepperpyError("Stream error")
    with pytest.raises(PepperpyError) as exc_info:
        async for _ in pepper.stream_response("Test"):
            pass
    assert str(exc_info.value) == "Stream error"
