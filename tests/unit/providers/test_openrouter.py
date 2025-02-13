"""Tests for the OpenRouter provider."""

import os
from typing import Any, Dict, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import AsyncOpenAI
from openai._types import NOT_GIVEN
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,
)
from openai.types.chat.chat_completion_chunk import Choice, ChoiceDelta

from pepperpy.core.messages import Message
from pepperpy.core.types import MessageType, Response, ResponseStatus
from pepperpy.providers.domain import (
    ProviderConfigError,
    ProviderError,
)
from pepperpy.providers.services.openrouter import OpenRouterConfig, OpenRouterProvider


@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """Mock configuration for testing."""
    return {
        "provider_type": "openrouter",
        "api_key": "test-key",
        "model": "openai/gpt-4",
        "temperature": 0.7,
        "max_tokens": 2048,
        "timeout": 30.0,
        "max_retries": 3,
    }


@pytest.fixture
def config(mock_config: Dict[str, Any]) -> OpenRouterConfig:
    """Create OpenRouter configuration."""
    return OpenRouterConfig(**mock_config)


@pytest.fixture
def provider(config: OpenRouterConfig) -> OpenRouterProvider:
    """Create OpenRouter provider."""
    return OpenRouterProvider(config)


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_client.chat = AsyncMock()
    mock_client.chat.completions = AsyncMock()
    mock_client.chat.completions.create = AsyncMock()
    return mock_client


@pytest.mark.asyncio
async def test_initialization(provider: OpenRouterProvider, mock_openai_client):
    """Test provider initialization."""
    with patch(
        "pepperpy.providers.services.openrouter.AsyncOpenAI",
        return_value=mock_openai_client,
    ):
        await provider.initialize()
        assert provider._client is not None
        assert provider._initialized is True


@pytest.mark.asyncio
async def test_initialization_with_env_api_key(mock_openai_client):
    """Test initialization with API key from environment."""
    with patch.dict(os.environ, {"PEPPERPY_API_KEY": "env-test-key"}):
        config = OpenRouterConfig()
        provider = OpenRouterProvider(config)
        with patch(
            "pepperpy.providers.services.openrouter.AsyncOpenAI",
            return_value=mock_openai_client,
        ):
            await provider.initialize()
            assert provider._client is not None
            assert provider._initialized is True


@pytest.mark.asyncio
async def test_initialization_error(provider: OpenRouterProvider):
    """Test initialization error handling."""
    with patch(
        "pepperpy.providers.services.openrouter.AsyncOpenAI",
        side_effect=ValueError("Invalid config"),
    ):
        with pytest.raises(ProviderConfigError) as exc_info:
            await provider.initialize()
        assert "Invalid config" in str(exc_info.value)


@pytest.mark.asyncio
async def test_cleanup(provider: OpenRouterProvider, mock_openai_client):
    """Test provider cleanup."""
    with patch(
        "pepperpy.providers.services.openrouter.AsyncOpenAI",
        return_value=mock_openai_client,
    ):
        await provider.initialize()
        await provider.cleanup()
        mock_openai_client.close.assert_called_once()
        assert provider._client is None
        assert not provider._initialized


@pytest.mark.asyncio
async def test_cleanup_error(provider: OpenRouterProvider, mock_openai_client):
    """Test cleanup error handling."""
    mock_openai_client.close.side_effect = Exception("Cleanup failed")
    with patch(
        "pepperpy.providers.services.openrouter.AsyncOpenAI",
        return_value=mock_openai_client,
    ):
        await provider.initialize()
        with pytest.raises(ProviderError) as exc_info:
            await provider.cleanup()
        assert "Cleanup failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_message_conversion(provider: OpenRouterProvider):
    """Test message conversion."""
    messages = [
        Message(
            id="12345678-1234-5678-1234-567812345678",
            content="Test message",
            metadata={"role": "user"},
        ),
        Message(
            id="87654321-4321-8765-4321-876543210987",
            content="Test response",
            metadata={"role": "assistant"},
        ),
        Message(
            id="11111111-1111-1111-1111-111111111111",
            content="System message",
            metadata={"role": "system"},
        ),
    ]

    converted = provider._convert_messages(messages)
    assert len(converted) == 3
    assert converted[0]["role"] == "user"
    assert converted[0].get("content") == "Test message"
    assert converted[1]["role"] == "assistant"
    assert converted[1].get("content") == "Test response"
    assert converted[2]["role"] == "system"
    assert converted[2].get("content") == "System message"


@pytest.mark.asyncio
async def test_generate(provider: OpenRouterProvider, mock_openai_client):
    """Test message generation."""
    # Setup mock response
    mock_completion = MagicMock(spec=ChatCompletion)
    mock_message = MagicMock(spec=ChatCompletionMessage)
    mock_message.content = "Generated response"
    mock_completion.choices = [MagicMock(message=mock_message)]
    mock_openai_client.chat.completions.create.return_value = mock_completion

    # Initialize provider
    with patch(
        "pepperpy.providers.services.openrouter.AsyncOpenAI",
        return_value=mock_openai_client,
    ):
        await provider.initialize()

        # Create test message
        message = Message(
            id="12345678-1234-5678-1234-567812345678",
            content="Test message",
        )

        # Generate response
        response = await provider.generate([message])

        # Verify response
        assert isinstance(response, Response)
        assert response.status == ResponseStatus.SUCCESS
        assert response.content["content"]["text"] == "Generated response"
        assert response.message_id == message.id

        # Verify client call
        mock_openai_client.chat.completions.create.assert_called_once_with(
            model="openai/gpt-4",
            messages=[{"role": "user", "content": "Test message"}],
            temperature=0.7,
            max_tokens=2048,
        )


@pytest.mark.asyncio
async def test_generate_with_custom_params(
    provider: OpenRouterProvider, mock_openai_client
):
    """Test message generation with custom parameters."""
    # Setup mock response
    mock_completion = MagicMock(spec=ChatCompletion)
    mock_message = MagicMock(spec=ChatCompletionMessage)
    mock_message.content = "Generated response"
    mock_completion.choices = [MagicMock(message=mock_message)]
    mock_openai_client.chat.completions.create.return_value = mock_completion

    # Initialize provider
    with patch(
        "pepperpy.providers.services.openrouter.AsyncOpenAI",
        return_value=mock_openai_client,
    ):
        await provider.initialize()

        # Create test message
        message = Message(
            id="12345678-1234-5678-1234-567812345678",
            content="Test message",
        )

        # Generate response with custom parameters
        response = await provider.generate(
            [message],
            model="openai/gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=1000,
        )

        # Verify response
        assert isinstance(response, Response)
        assert response.status == ResponseStatus.SUCCESS
        assert response.content["content"]["text"] == "Generated response"

        # Verify client call with custom parameters
        mock_openai_client.chat.completions.create.assert_called_once_with(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Test message"}],
            temperature=0.5,
            max_tokens=1000,
        )


@pytest.mark.asyncio
async def test_generate_error(provider: OpenRouterProvider, mock_openai_client):
    """Test error handling during generation."""
    mock_openai_client.chat.completions.create.side_effect = Exception(
        "Generation failed"
    )

    # Initialize provider
    with patch(
        "pepperpy.providers.services.openrouter.AsyncOpenAI",
        return_value=mock_openai_client,
    ):
        await provider.initialize()

        message = Message(
            id="12345678-1234-5678-1234-567812345678",
            content="Test message",
        )

        with pytest.raises(ProviderError) as exc_info:
            await provider.generate([message])
        assert "Generation failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_stream(provider: OpenRouterProvider, mock_openai_client):
    """Test message streaming."""

    # Setup mock response chunks
    async def mock_stream():
        chunks = [
            ChatCompletionChunk(
                id="chunk1",
                choices=[
                    Choice(
                        delta=ChoiceDelta(
                            content="Hello",
                            role=None,
                            function_call=None,
                            tool_calls=None,
                        ),
                        finish_reason=None,
                        index=0,
                        logprobs=None,
                    )
                ],
                model="gpt-4",
                object="chat.completion.chunk",
                created=1234567890,
                system_fingerprint=None,
            ),
            ChatCompletionChunk(
                id="chunk2",
                choices=[
                    Choice(
                        delta=ChoiceDelta(
                            content=" world",
                            role=None,
                            function_call=None,
                            tool_calls=None,
                        ),
                        finish_reason=None,
                        index=0,
                        logprobs=None,
                    )
                ],
                model="gpt-4",
                object="chat.completion.chunk",
                created=1234567890,
                system_fingerprint=None,
            ),
        ]
        for chunk in chunks:
            yield chunk

    mock_openai_client.chat.completions.create.return_value = mock_stream()

    # Initialize provider
    with patch(
        "pepperpy.providers.services.openrouter.AsyncOpenAI",
        return_value=mock_openai_client,
    ):
        await provider.initialize()

        # Create test message
        message = Message(
            id="12345678-1234-5678-1234-567812345678",
            content="Test message",
        )

        # Stream responses
        responses = []
        async for response in provider.stream([message]):
            responses.append(response)

        # Verify responses
        assert len(responses) == 2
        assert responses[0].content["content"]["text"] == "Hello"
        assert responses[1].content["content"]["text"] == " world"

        # Verify client call
        mock_openai_client.chat.completions.create.assert_called_once_with(
            model="openai/gpt-4",
            messages=[{"role": "user", "content": "Test message"}],
            temperature=0.7,
            max_tokens=2048,
            stream=True,
        )


@pytest.mark.asyncio
async def test_stream_with_custom_params(
    provider: OpenRouterProvider, mock_openai_client
):
    """Test message streaming with custom parameters."""

    # Setup mock response chunks
    async def mock_stream():
        chunks = [
            ChatCompletionChunk(
                id="chunk1",
                choices=[
                    Choice(
                        delta=ChoiceDelta(
                            content="Custom",
                            role=None,
                            function_call=None,
                            tool_calls=None,
                        ),
                        finish_reason=None,
                        index=0,
                        logprobs=None,
                    )
                ],
                model="gpt-3.5-turbo",
                object="chat.completion.chunk",
                created=1234567890,
                system_fingerprint=None,
            ),
            ChatCompletionChunk(
                id="chunk2",
                choices=[
                    Choice(
                        delta=ChoiceDelta(
                            content=" response",
                            role=None,
                            function_call=None,
                            tool_calls=None,
                        ),
                        finish_reason=None,
                        index=0,
                        logprobs=None,
                    )
                ],
                model="gpt-3.5-turbo",
                object="chat.completion.chunk",
                created=1234567890,
                system_fingerprint=None,
            ),
        ]
        for chunk in chunks:
            yield chunk

    mock_openai_client.chat.completions.create.return_value = mock_stream()

    # Initialize provider
    with patch(
        "pepperpy.providers.services.openrouter.AsyncOpenAI",
        return_value=mock_openai_client,
    ):
        await provider.initialize()

        # Create test message
        message = Message(
            id="12345678-1234-5678-1234-567812345678",
            content="Test message",
        )

        # Stream responses with custom parameters
        responses = []
        kwargs = {
            "model": "openai/gpt-3.5-turbo",
            "temperature": 0.5,
            "max_tokens": 1000,
        }
        async for response in provider.stream([message], **cast(Any, kwargs)):
            responses.append(response)

        # Verify responses
        assert len(responses) == 2
        assert responses[0].content["content"]["text"] == "Custom"
        assert responses[1].content["content"]["text"] == " response"

        # Verify client call with custom parameters
        mock_openai_client.chat.completions.create.assert_called_once_with(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Test message"}],
            temperature=0.5,
            max_tokens=1000,
            stream=True,
        )


@pytest.mark.asyncio
async def test_stream_error(provider: OpenRouterProvider, mock_openai_client):
    """Test error handling during streaming."""
    mock_openai_client.chat.completions.create.side_effect = Exception(
        "Streaming failed"
    )

    # Initialize provider
    with patch(
        "pepperpy.providers.services.openrouter.AsyncOpenAI",
        return_value=mock_openai_client,
    ):
        await provider.initialize()

        message = Message(
            id="12345678-1234-5678-1234-567812345678",
            content="Test message",
        )

        with pytest.raises(ProviderError) as exc_info:
            async for _ in provider.stream([message]):
                pass
        assert "Streaming failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_send_message(provider: OpenRouterProvider, mock_openai_client):
    """Test sending a message."""
    # Setup mock response
    mock_completion = MagicMock(spec=ChatCompletion)
    mock_message = MagicMock(spec=ChatCompletionMessage)
    mock_message.content = "Generated response"
    mock_completion.choices = [MagicMock(message=mock_message)]
    mock_openai_client.chat.completions.create.return_value = mock_completion

    # Initialize provider
    with patch(
        "pepperpy.providers.services.openrouter.AsyncOpenAI",
        return_value=mock_openai_client,
    ):
        await provider.initialize()

        # Send message
        response = await provider.send_message("Test message")

        # Verify response
        assert isinstance(response, Response)
        assert response.status == ResponseStatus.SUCCESS
        assert response.content["type"] == MessageType.RESPONSE
        assert response.content["content"]["text"] == "Generated response"

        # Verify client call
        mock_openai_client.chat.completions.create.assert_called_once_with(
            model="openai/gpt-4",
            messages=[{"role": "user", "content": "Test message"}],
            temperature=0.7,
            max_tokens=2048,
            stop=NOT_GIVEN,
        )
