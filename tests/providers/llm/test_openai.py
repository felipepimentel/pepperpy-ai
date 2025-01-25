"""Tests for OpenAI LLM provider."""

import os
import pytest
from typing import Any, Dict, List, cast
from unittest.mock import AsyncMock, MagicMock, patch

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage, FunctionCall
from openai.types.chat.chat_completion_chunk import Choice as StreamChoice
from openai.types.chat.chat_completion_chunk import ChoiceDelta
from openai.types.completion_usage import CompletionUsage

from pepperpy.core.utils.errors import ProviderError
from pepperpy.providers.llm.base import LLMMessage, LLMConfig
from pepperpy.providers.llm.openai import OpenAIProvider


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    mock = MagicMock(spec=AsyncOpenAI)
    mock.chat = MagicMock()
    mock.chat.completions = MagicMock()
    mock.close = AsyncMock()
    with patch("openai.AsyncOpenAI", return_value=mock) as mock_class:
        yield mock_class


@pytest.fixture
def mock_response():
    """Create a mock OpenAI chat completion response."""
    return ChatCompletion(
        id="test-id",
        choices=[
            Choice(
                finish_reason="stop",
                index=0,
                message=ChatCompletionMessage(
                    content="Test response",
                    role="assistant",
                    function_call=None,
                    tool_calls=None,
                ),
            )
        ],
        created=1234567890,
        model="gpt-3.5-turbo",
        object="chat.completion",
        usage=CompletionUsage(
            completion_tokens=10,
            prompt_tokens=20,
            total_tokens=30,
        ),
    )


@pytest.fixture
def mock_stream_response():
    """Create a mock OpenAI chat completion stream response."""
    return ChatCompletionChunk(
        id="test-id",
        choices=[
            StreamChoice(
                delta=ChoiceDelta(
                    content="Test response",
                    role="assistant",
                    function_call=None,
                    tool_calls=None,
                ),
                finish_reason="stop",
                index=0,
            )
        ],
        created=1234567890,
        model="gpt-3.5-turbo",
        object="chat.completion.chunk",
    )


@pytest.fixture
def provider():
    """Create an OpenAI provider instance."""
    return OpenAIProvider({
        "api_key": "test-key",
        "model": "gpt-3.5-turbo",
        "timeout": 30,
    })


async def test_initialization(provider: OpenAIProvider, mock_openai_client):
    """Test provider initialization."""
    await provider.initialize()
    assert provider.is_initialized
    mock_openai_client.assert_called_once_with(
        api_key="test-key",
        timeout=30,
    )


async def test_initialization_no_api_key():
    """Test initialization without API key."""
    provider = OpenAIProvider()
    with pytest.raises(ProviderError, match="OpenAI API key not found"):
        await provider.initialize()


async def test_shutdown(provider: OpenAIProvider, mock_openai_client):
    """Test provider shutdown."""
    await provider.initialize()
    await provider.shutdown()
    assert not provider.is_initialized
    assert provider._client is not None
    provider._client.close.assert_called_once()


async def test_generate(
    provider: OpenAIProvider,
    mock_openai_client,
    mock_response: ChatCompletion,
):
    """Test text generation."""
    await provider.initialize()
    assert provider._client is not None
    assert provider._client.chat is not None
    provider._client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    response = await provider.generate("Test prompt")
    assert response.content == "Test response"
    assert response.role == "assistant"
    assert response.finish_reason == "stop"
    assert response.usage == {
        "prompt_tokens": 20,
        "completion_tokens": 10,
        "total_tokens": 30,
    }


async def test_generate_stream(
    provider: OpenAIProvider,
    mock_openai_client,
    mock_stream_response: ChatCompletionChunk,
):
    """Test streaming text generation."""
    await provider.initialize()
    assert provider._client is not None
    assert provider._client.chat is not None
    
    async def mock_stream():
        yield mock_stream_response
    
    provider._client.chat.completions.create = AsyncMock(return_value=mock_stream())
    
    async for response in provider.generate_stream("Test prompt"):
        assert response.content == "Test response"
        assert response.role == "assistant"
        assert response.finish_reason == "stop"


async def test_chat(
    provider: OpenAIProvider,
    mock_openai_client,
    mock_response: ChatCompletion,
):
    """Test chat conversation."""
    await provider.initialize()
    assert provider._client is not None
    assert provider._client.chat is not None
    provider._client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    messages = [
        LLMMessage(role="user", content="Hello"),
        LLMMessage(role="assistant", content="Hi"),
        LLMMessage(role="user", content="How are you?"),
    ]
    
    response = await provider.chat(messages)
    assert response.content == "Test response"
    assert response.role == "assistant"
    assert response.finish_reason == "stop"
    assert response.usage == {
        "prompt_tokens": 20,
        "completion_tokens": 10,
        "total_tokens": 30,
    }


async def test_chat_stream(
    provider: OpenAIProvider,
    mock_openai_client,
    mock_stream_response: ChatCompletionChunk,
):
    """Test streaming chat conversation."""
    await provider.initialize()
    assert provider._client is not None
    assert provider._client.chat is not None
    
    async def mock_stream():
        yield mock_stream_response
    
    provider._client.chat.completions.create = AsyncMock(return_value=mock_stream())
    
    messages = [
        LLMMessage(role="user", content="Hello"),
        LLMMessage(role="assistant", content="Hi"),
        LLMMessage(role="user", content="How are you?"),
    ]
    
    async for response in provider.chat_stream(messages):
        assert response.content == "Test response"
        assert response.role == "assistant"
        assert response.finish_reason == "stop"


async def test_function_call(
    provider: OpenAIProvider,
    mock_openai_client,
):
    """Test function call handling."""
    await provider.initialize()
    assert provider._client is not None
    assert provider._client.chat is not None
    
    response = ChatCompletion(
        id="test-id",
        choices=[
            Choice(
                finish_reason="function_call",
                index=0,
                message=ChatCompletionMessage(
                    content=None,
                    role="assistant",
                    function_call=FunctionCall(
                        name="test_function",
                        arguments='{"arg1": "value1"}',
                    ),
                    tool_calls=None,
                ),
            )
        ],
        created=1234567890,
        model="gpt-3.5-turbo",
        object="chat.completion",
        usage=CompletionUsage(
            completion_tokens=10,
            prompt_tokens=20,
            total_tokens=30,
        ),
    )
    
    provider._client.chat.completions.create = AsyncMock(return_value=response)
    
    result = await provider.generate("Test prompt")
    assert result.function_call == {
        "name": "test_function",
        "arguments": '{"arg1": "value1"}',
    }


async def test_tool_calls(
    provider: OpenAIProvider,
    mock_openai_client,
):
    """Test tool calls handling."""
    await provider.initialize()
    assert provider._client is not None
    assert provider._client.chat is not None
    
    response = ChatCompletion(
        id="test-id",
        choices=[
            Choice(
                finish_reason="tool_calls",
                index=0,
                message=ChatCompletionMessage(
                    content=None,
                    role="assistant",
                    function_call=None,
                    tool_calls=[
                        MagicMock(
                            id="test-tool-1",
                            type="function",
                            function=MagicMock(
                                name="test_function",
                                arguments='{"arg1": "value1"}',
                            ),
                        ),
                    ],
                ),
            )
        ],
        created=1234567890,
        model="gpt-3.5-turbo",
        object="chat.completion",
        usage=CompletionUsage(
            completion_tokens=10,
            prompt_tokens=20,
            total_tokens=30,
        ),
    )
    
    provider._client.chat.completions.create = AsyncMock(return_value=response)
    
    result = await provider.generate("Test prompt")
    assert result.tool_calls == [
        {
            "id": "test-tool-1",
            "type": "function",
            "function": {
                "name": "test_function",
                "arguments": '{"arg1": "value1"}',
            },
        },
    ]


async def test_get_token_count(provider: OpenAIProvider):
    """Test token count estimation."""
    count = await provider.get_token_count("This is a test text.")
    assert count > 0


async def test_get_metadata(provider: OpenAIProvider):
    """Test metadata retrieval."""
    metadata = await provider.get_metadata()
    assert metadata["model_name"] == "gpt-3.5-turbo"
    assert metadata["context_window"] == 4096
    assert metadata["max_tokens"] == 4096
    assert metadata["supports_streaming"] is True
    assert metadata["supports_tools"] is True
    assert metadata["provider_name"] == "openai" 