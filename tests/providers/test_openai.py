"""Test OpenAI provider functionality.

This module contains tests for the OpenAI provider implementation.

@file: test_openai.py
@purpose: Test cases for OpenAI provider implementation
@component: Tests
@created: 2024-03-20
@task: TASK-001
@status: active
"""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import openai
import pytest
import pytest_asyncio
from openai.types.chat import ChatCompletion, ChatCompletionChunk, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice as ChatChoice
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from openai.types.chat.chat_completion_chunk import ChoiceDelta
from openai.types.completion_usage import CompletionUsage
from openai.types.model import Model
from pydantic import SecretStr

from pepperpy.providers.domain import ProviderAPIError, ProviderRateLimitError
from pepperpy.providers.provider import ProviderConfig
from pepperpy.providers.services.openai import OpenAIProvider


@pytest.fixture
def provider_config() -> ProviderConfig:
    """Create a test provider config."""
    return ProviderConfig(
        provider_type="openai",
        api_key=SecretStr("test-key"),
        model="gpt-4",
        max_retries=3,
        timeout=30,
    )


@pytest_asyncio.fixture
async def mock_client() -> AsyncMock:
    """Create mock OpenAI client."""
    mock = AsyncMock()

    # Mock models list
    mock.models = AsyncMock()
    mock.models.list = AsyncMock()
    mock_model = Model(
        id="gpt-4", created=1234567890, owned_by="openai", object="model"
    )
    mock.models.list.return_value = MagicMock(data=[mock_model])

    # Mock chat completions
    mock.chat = AsyncMock()
    mock.chat.completions = AsyncMock()
    mock.chat.completions.create = AsyncMock()

    # Mock embeddings
    mock.embeddings = AsyncMock()
    mock.embeddings.create = AsyncMock()

    return mock


@pytest_asyncio.fixture
async def provider(
    provider_config: ProviderConfig,
    mock_client: AsyncMock,
) -> AsyncGenerator[OpenAIProvider, None]:
    """Create and initialize test provider."""
    with patch(
        "pepperpy.providers.services.openai.AsyncOpenAI",
        return_value=mock_client,
    ):
        provider = OpenAIProvider(provider_config)
        await provider.initialize()
        try:
            yield provider
        finally:
            await provider.cleanup()


@pytest.mark.asyncio
async def test_openai_complete(
    provider: OpenAIProvider, mock_client: AsyncMock
) -> None:
    """Test OpenAI completion."""
    mock_message = ChatCompletionMessage(role="assistant", content="Hello")
    mock_choice = ChatChoice(
        index=0,
        message=mock_message,
        finish_reason="stop",
    )
    mock_response = ChatCompletion(
        id="test",
        choices=[mock_choice],
        created=1234567890,
        model="gpt-4",
        object="chat.completion",
        usage=CompletionUsage(
            completion_tokens=5,
            prompt_tokens=5,
            total_tokens=10,
        ),
    )

    mock_client.chat.completions.create.return_value = mock_response
    response = await provider.complete("Hi")
    assert response == "Hello"

    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hi"}],
        temperature=0.7,
        max_tokens=None,
        stream=False,
    )


@pytest.mark.asyncio
async def test_openai_complete_stream(
    provider: OpenAIProvider, mock_client: AsyncMock
) -> None:
    """Test OpenAI streaming completion."""
    mock_delta = ChoiceDelta(content="Hello", role=None)
    mock_choice = ChunkChoice(
        index=0,
        delta=mock_delta,
        finish_reason=None,
    )
    mock_chunk = ChatCompletionChunk(
        id="test",
        choices=[mock_choice],
        created=1234567890,
        model="gpt-4",
        object="chat.completion.chunk",
    )

    async def mock_stream(
        *args: Any, **kwargs: Any
    ) -> AsyncGenerator[ChatCompletionChunk, None]:
        yield mock_chunk

    mock_client.chat.completions.create = mock_stream
    result = await provider.complete("Hi", stream=True)
    assert isinstance(result, AsyncGenerator)

    chunks = []
    async for chunk in result:
        chunks.append(chunk)
    assert chunks == ["Hello"]

    # Note: We can't use assert_called_once_with since we replaced the mock
    # with a real function. Instead, we'll verify the behavior through the output


@pytest.mark.asyncio
async def test_openai_complete_rate_limit(
    provider: OpenAIProvider, mock_client: AsyncMock
) -> None:
    """Test OpenAI completion rate limit error."""
    error_msg = "Rate limit exceeded"
    mock_response = httpx.Response(
        429, request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    )
    mock_client.chat.completions.create.side_effect = openai.RateLimitError(
        message=error_msg,
        response=mock_response,
        body={"error": {"message": error_msg}},
    )
    with pytest.raises(ProviderRateLimitError) as exc_info:
        await provider.complete("Hi")
    assert str(exc_info.value) == error_msg
    assert exc_info.value.provider_type == "openai"
    assert exc_info.value.details == {
        "args": (),
        "kwargs": {
            "messages": [{"role": "user", "content": "Hi"}],
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": None,
            "stream": False,
        },
    }


@pytest.mark.asyncio
async def test_openai_complete_api_error(
    provider: OpenAIProvider, mock_client: AsyncMock
) -> None:
    """Test OpenAI completion API error."""
    error_msg = "API Error"
    mock_response = httpx.Response(
        500, request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    )
    mock_client.chat.completions.create.side_effect = openai.InternalServerError(
        message=error_msg,
        response=mock_response,
        body={"error": {"message": error_msg}},
    )
    with pytest.raises(ProviderAPIError) as exc_info:
        await provider.complete("Hi")
    assert str(exc_info.value) == error_msg
    assert exc_info.value.provider_type == "openai"
    assert exc_info.value.details == {
        "args": (),
        "kwargs": {
            "messages": [{"role": "user", "content": "Hi"}],
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": None,
            "stream": False,
        },
    }


@pytest.mark.asyncio
async def test_openai_complete_authentication_error(
    provider: OpenAIProvider, mock_client: AsyncMock
) -> None:
    """Test OpenAI completion authentication error."""
    error_msg = "Authentication failed"
    mock_response = httpx.Response(
        401, request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    )
    mock_client.chat.completions.create.side_effect = openai.AuthenticationError(
        message=error_msg,
        response=mock_response,
        body={"error": {"message": error_msg}},
    )
    with pytest.raises(ProviderAPIError) as exc_info:
        await provider.complete("Hi")
    assert str(exc_info.value) == error_msg
    assert exc_info.value.provider_type == "openai"
    assert exc_info.value.details == {
        "args": (),
        "kwargs": {
            "messages": [{"role": "user", "content": "Hi"}],
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": None,
            "stream": False,
        },
    }


@pytest.mark.asyncio
async def test_openai_embed(provider: OpenAIProvider, mock_client: AsyncMock) -> None:
    """Test OpenAI embedding."""
    mock_response = MagicMock()
    mock_response.data = [MagicMock()]
    mock_response.data[0].embedding = [0.1, 0.2, 0.3]

    mock_client.embeddings.create.return_value = mock_response
    embedding = await provider.embed("Hello")
    assert embedding == [0.1, 0.2, 0.3]

    mock_client.embeddings.create.assert_called_once_with(
        model="text-embedding-ada-002",
        input="Hello",
    )


@pytest.mark.asyncio
async def test_openai_cleanup(provider: OpenAIProvider, mock_client: AsyncMock) -> None:
    """Test OpenAI provider cleanup."""
    await provider.cleanup()
    mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_initialize(provider: OpenAIProvider) -> None:
    """Test provider initialization."""
    assert provider._client is not None


@pytest.mark.asyncio
async def test_complete_with_options(
    provider: OpenAIProvider, mock_client: AsyncMock
) -> None:
    """Test completion with custom options."""
    mock_message = ChatCompletionMessage(role="assistant", content="test response")
    mock_choice = ChatChoice(
        index=0,
        message=mock_message,
        finish_reason="stop",
    )
    mock_response = ChatCompletion(
        id="test",
        choices=[mock_choice],
        created=1234567890,
        model="gpt-4",
        object="chat.completion",
        usage=CompletionUsage(
            completion_tokens=5,
            prompt_tokens=5,
            total_tokens=10,
        ),
    )

    mock_client.chat.completions.create.return_value = mock_response
    response = await provider.complete(
        "test prompt",
        temperature=0.5,
        max_tokens=50,
    )
    assert response == "test response"

    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-4",
        messages=[{"role": "user", "content": "test prompt"}],
        temperature=0.5,
        max_tokens=50,
        stream=False,
    )


@pytest.mark.asyncio
async def test_complete_stream_with_options(
    provider: OpenAIProvider, mock_client: AsyncMock
) -> None:
    """Test streaming completion with custom options."""
    mock_delta = ChoiceDelta(content="test response", role=None)
    mock_choice = ChunkChoice(
        index=0,
        delta=mock_delta,
        finish_reason=None,
    )
    mock_chunk = ChatCompletionChunk(
        id="test",
        choices=[mock_choice],
        created=1234567890,
        model="gpt-4",
        object="chat.completion.chunk",
    )

    async def mock_stream(
        *args: Any, **kwargs: Any
    ) -> AsyncGenerator[ChatCompletionChunk, None]:
        yield mock_chunk

    mock_client.chat.completions.create = mock_stream
    result = await provider.complete(
        "test prompt",
        temperature=0.5,
        max_tokens=50,
        stream=True,
    )
    assert isinstance(result, AsyncGenerator)

    chunks = []
    async for chunk in result:
        chunks.append(chunk)
    assert chunks == ["test response"]

    # Note: We can't use assert_called_once_with since we replaced the mock
    # with a real function. Instead, we'll verify the behavior through the output
