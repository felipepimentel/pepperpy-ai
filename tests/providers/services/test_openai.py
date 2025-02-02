"""Test OpenAI provider functionality."""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import openai
import pytest
import pytest_asyncio
from openai.types.chat import ChatCompletionChunk
from pydantic import SecretStr

from pepperpy.common.errors import ProviderError
from pepperpy.providers.domain import (
    ProviderAPIError,
    ProviderInitError,
    ProviderRateLimitError,
)
from pepperpy.providers.provider import ProviderConfig
from pepperpy.providers.services.openai import OpenAIProvider


class MockAsyncIterator:
    """Mock async iterator for streaming responses."""

    def __init__(self, items: list[AsyncMock]) -> None:
        """Initialize the mock async iterator.

        Args:
            items: List of mock responses to iterate over.
        """
        self.items = items

    def __aiter__(self) -> "MockAsyncIterator":
        """Return self as async iterator.

        Returns:
            Self as async iterator.
        """
        return self

    async def __anext__(self) -> AsyncMock:
        """Get next item from iterator.

        Returns:
            Next mock response.

        Raises:
            StopAsyncIteration: When no more items.
        """
        if not self.items:
            raise StopAsyncIteration
        return self.items.pop(0)


@pytest.fixture
def openai_config() -> ProviderConfig:
    """Provide OpenAI test configuration."""
    return ProviderConfig(
        provider_type="openai",
        api_key=SecretStr("test-key"),
        model="gpt-3.5-turbo",
    )


@pytest_asyncio.fixture
async def mock_client() -> AsyncMock:
    """Create mock OpenAI client."""
    mock = AsyncMock()

    # Mock models list
    mock.models = AsyncMock()
    mock.models.list = AsyncMock()
    mock_models_response = MagicMock()
    mock_models_response.data = [
        MagicMock(id="gpt-4", created=1234567890, owned_by="openai", object="model")
    ]
    mock.models.list.return_value = mock_models_response

    # Mock chat completions
    mock.chat = AsyncMock()
    mock.chat.completions = AsyncMock()
    mock.chat.completions.create = AsyncMock()

    # Mock embeddings
    mock.embeddings = AsyncMock()
    mock.embeddings.create = AsyncMock()

    # Mock close
    mock.close = AsyncMock()

    return mock


@pytest_asyncio.fixture
async def provider(
    openai_config: ProviderConfig,
    mock_client: AsyncMock,
) -> AsyncGenerator[OpenAIProvider, None]:
    """Create and initialize test provider."""
    with patch(
        "pepperpy.providers.services.openai.AsyncOpenAI",
        return_value=mock_client,
    ):
        provider = OpenAIProvider(openai_config)
        await provider.initialize()
        try:
            yield provider
        finally:
            await provider.cleanup()


def test_initialization_with_defaults() -> None:
    """Test OpenAI provider initialization with default configuration."""
    config = ProviderConfig(
        provider_type="openai",
        api_key=SecretStr("test-key"),
        model="gpt-3.5-turbo",
        max_retries=3,
        timeout=30,
    )
    provider = OpenAIProvider(config)
    assert provider.config.model == "gpt-3.5-turbo"


def test_initialization_error() -> None:
    """Test OpenAI provider initialization with invalid configuration."""
    config = ProviderConfig(
        provider_type="openai",
        model="gpt-3.5-turbo",
        api_key=SecretStr(""),  # Empty API key should raise error
        max_retries=3,
        timeout=30,
    )
    with pytest.raises(ProviderError) as exc_info:
        OpenAIProvider(config)
    assert "API key is required" in str(exc_info.value)


@pytest.mark.asyncio
async def test_complete_sync(provider: OpenAIProvider, mock_client: AsyncMock) -> None:
    """Test synchronous completion with OpenAI provider."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response"
    mock_client.chat.completions.create.return_value = mock_response

    response = await provider.complete("Test prompt")
    assert response == "Test response"
    mock_client.chat.completions.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_complete_stream(
    provider: OpenAIProvider, mock_client: AsyncMock
) -> None:
    """Test streaming completion with OpenAI provider."""
    mock_chunk = MagicMock(spec=ChatCompletionChunk)
    mock_choice = MagicMock()
    mock_choice.delta.content = "Test"
    mock_chunk.choices = [mock_choice]

    async def mock_stream(
        *args: Any, **kwargs: Any
    ) -> AsyncGenerator[ChatCompletionChunk, None]:
        yield mock_chunk

    mock_client.chat.completions.create = mock_stream

    result = await provider.complete("Test prompt", stream=True)
    assert isinstance(result, AsyncGenerator)
    chunks = []
    async for chunk in result:
        chunks.append(chunk)
    assert chunks == ["Test"]


@pytest.mark.asyncio
async def test_complete_rate_limit_error(
    provider: OpenAIProvider, mock_client: AsyncMock
) -> None:
    """Test handling of rate limit errors during completion."""
    error_msg = "Rate limit exceeded"
    mock_response = httpx.Response(
        429,
        request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
    )

    mock_client.chat.completions.create.side_effect = openai.RateLimitError(
        message=error_msg,
        response=mock_response,
        body={"error": {"message": error_msg}},
    )

    with pytest.raises(ProviderRateLimitError) as exc_info:
        await provider.complete("Test prompt")
    assert error_msg in str(exc_info.value)


@pytest.mark.asyncio
async def test_complete_api_error(
    provider: OpenAIProvider, mock_client: AsyncMock
) -> None:
    """Test handling of API errors during completion."""
    error_msg = "API Error"
    mock_response = httpx.Response(
        500,
        request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
    )

    mock_client.chat.completions.create.side_effect = openai.InternalServerError(
        message=error_msg,
        response=mock_response,
        body={"error": {"message": error_msg}},
    )

    with pytest.raises(ProviderAPIError) as exc_info:
        await provider.complete("Test prompt")
    assert error_msg in str(exc_info.value)


@pytest.mark.asyncio
async def test_embed(provider: OpenAIProvider, mock_client: AsyncMock) -> None:
    """Test text embedding with OpenAI provider."""
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
    mock_client.embeddings.create.return_value = mock_response

    embedding = await provider.embed("Test text")
    assert embedding == [0.1, 0.2, 0.3]
    mock_client.embeddings.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_embed_rate_limit_error(
    provider: OpenAIProvider, mock_client: AsyncMock
) -> None:
    """Test handling of rate limit errors during embedding."""
    error_msg = "Rate limit exceeded"
    mock_response = httpx.Response(
        429,
        request=httpx.Request("POST", "https://api.openai.com/v1/embeddings"),
    )

    mock_client.embeddings.create.side_effect = openai.RateLimitError(
        message=error_msg,
        response=mock_response,
        body={"error": {"message": error_msg}},
    )

    with pytest.raises(ProviderRateLimitError) as exc_info:
        await provider.embed("Test text")
    assert error_msg in str(exc_info.value)


@pytest.mark.asyncio
async def test_embed_api_error(
    provider: OpenAIProvider, mock_client: AsyncMock
) -> None:
    """Test handling of API errors during embedding."""
    error_msg = "API Error"
    mock_response = httpx.Response(
        500,
        request=httpx.Request("POST", "https://api.openai.com/v1/embeddings"),
    )

    mock_client.embeddings.create.side_effect = openai.InternalServerError(
        message=error_msg,
        response=mock_response,
        body={"error": {"message": error_msg}},
    )

    with pytest.raises(ProviderAPIError) as exc_info:
        await provider.embed("Test text")
    assert error_msg in str(exc_info.value)


@pytest.mark.asyncio
async def test_cleanup(provider: OpenAIProvider, mock_client: AsyncMock) -> None:
    """Test cleanup of OpenAI provider resources."""
    await provider.cleanup()
    mock_client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_cleanup_not_initialized() -> None:
    """Test cleanup when provider is not initialized."""
    provider = OpenAIProvider(
        ProviderConfig(
            provider_type="openai",
            api_key=SecretStr("test-key"),
            model="gpt-3.5-turbo",
            max_retries=3,
            timeout=30,
        )
    )
    await provider.cleanup()  # Should not raise any errors


@pytest.fixture
async def openai_provider() -> AsyncGenerator[OpenAIProvider, None]:
    """Create an OpenAI provider instance.

    Returns:
        An initialized OpenAI provider instance.

    Yields:
        The OpenAI provider instance.
    """
    config = ProviderConfig(
        provider_type="openai",
        api_key=SecretStr("test-key"),
        model="gpt-3.5-turbo",
    )
    provider = OpenAIProvider(config)
    await provider.initialize()
    yield provider
    await provider.cleanup()


async def test_openai_provider_initialization() -> None:
    """Test OpenAI provider initialization."""
    config = ProviderConfig(
        provider_type="openai",
        api_key=SecretStr("test-key"),
        model="gpt-3.5-turbo",
    )
    provider = OpenAIProvider(config)
    await provider.initialize()
    assert provider._client is not None
    await provider.cleanup()


async def test_openai_provider_initialization_no_api_key() -> None:
    """Test OpenAI provider initialization without API key."""
    config = ProviderConfig(provider_type="openai", model="gpt-3.5-turbo")
    provider = OpenAIProvider(config)
    with pytest.raises(ProviderInitError):
        await provider.initialize()


async def test_openai_provider_completion(openai_provider: OpenAIProvider) -> None:
    """Test OpenAI provider completion."""
    response = await openai_provider.complete("test prompt")
    assert isinstance(response, str)


async def test_openai_provider_streaming(openai_provider: OpenAIProvider) -> None:
    """Test OpenAI provider streaming."""
    response = await openai_provider.complete("test prompt", stream=True)
    assert isinstance(response, AsyncGenerator)

    chunks = []
    async for chunk in response:
        chunks.append(chunk)
        assert isinstance(chunk, str)


async def test_openai_provider_completion_not_initialized() -> None:
    """Test OpenAI provider completion without initialization."""
    config = ProviderConfig(
        provider_type="openai",
        api_key=SecretStr("test-key"),
        model="gpt-3.5-turbo",
    )
    provider = OpenAIProvider(config)
    with pytest.raises(ProviderInitError):
        await provider.complete("test prompt")
