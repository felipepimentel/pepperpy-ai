"""Test Gemini provider functionality.

This module contains tests for the Gemini provider implementation.

@file: test_gemini.py
@purpose: Test cases for Gemini provider implementation
@component: Tests
@created: 2024-03-20
@task: TASK-001
@status: active
"""

from collections.abc import AsyncGenerator, AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from pydantic import SecretStr

from pepperpy.providers.domain import (
    ProviderAPIError,
    ProviderInitError,
    ProviderRateLimitError,
)
from pepperpy.providers.provider import ProviderConfig
from pepperpy.providers.services.gemini import GeminiProvider


@pytest.fixture
def provider_config() -> ProviderConfig:
    """Create a test provider config."""
    return ProviderConfig(
        provider_type="gemini",
        api_key=SecretStr("test-key"),
        model="gemini-pro",
        max_retries=3,
        timeout=30,
    )


@pytest_asyncio.fixture
async def mock_client() -> AsyncMock:
    """Create mock Gemini client."""
    mock = AsyncMock()
    mock.generate_content_async = AsyncMock()
    return mock


@pytest_asyncio.fixture
async def provider(
    provider_config: ProviderConfig,
    mock_client: AsyncMock,
) -> AsyncIterator[GeminiProvider]:
    """Create and initialize test provider."""
    with (
        patch(
            "pepperpy.providers.services.gemini.GenerativeModel",
            return_value=mock_client,
        ),
        patch("pepperpy.providers.services.gemini.configure"),
    ):
        provider = GeminiProvider(provider_config)
        await provider.initialize()
        try:
            yield provider
        finally:
            await provider.cleanup()


@pytest.mark.asyncio
async def test_gemini_complete(
    provider: GeminiProvider, mock_client: AsyncMock
) -> None:
    """Test Gemini completion."""
    mock_response = MagicMock()
    mock_response.text = "Hello"
    mock_client.generate_content_async.return_value = mock_response

    response = await provider.complete("Hi")
    assert response == "Hello"

    mock_client.generate_content_async.assert_called_once()
    call_args = mock_client.generate_content_async.call_args
    assert call_args[0][0] == "Hi"
    assert call_args[1]["stream"] is False


@pytest.mark.asyncio
async def test_gemini_complete_stream(
    provider: GeminiProvider, mock_client: AsyncMock
) -> None:
    """Test Gemini streaming completion."""
    mock_chunk = MagicMock()
    mock_chunk.text = "Hello"

    async def mock_stream() -> AsyncGenerator[MagicMock, None]:
        yield mock_chunk

    mock_client.generate_content_async.return_value = mock_stream()
    result = await provider.complete("Hi", stream=True)
    assert isinstance(result, AsyncGenerator)

    chunks = []
    async for chunk in result:
        chunks.append(chunk)
    assert chunks == ["Hello"]

    mock_client.generate_content_async.assert_called_once()
    call_args = mock_client.generate_content_async.call_args
    assert call_args[0][0] == "Hi"
    assert call_args[1]["stream"] is True


@pytest.mark.asyncio
async def test_gemini_complete_rate_limit(
    provider: GeminiProvider, mock_client: AsyncMock
) -> None:
    """Test Gemini completion rate limit error."""
    error_msg = "Quota exceeded"
    mock_client.generate_content_async.side_effect = Exception(error_msg)
    with pytest.raises(ProviderRateLimitError) as exc_info:
        await provider.complete("Hi")
    assert str(exc_info.value) == "Gemini rate limit exceeded"
    assert exc_info.value.provider_type == "gemini"
    assert exc_info.value.details == {"error": error_msg}


@pytest.mark.asyncio
async def test_gemini_complete_api_error(
    provider: GeminiProvider, mock_client: AsyncMock
) -> None:
    """Test Gemini completion API error."""
    error_msg = "API Error"
    mock_client.generate_content_async.side_effect = Exception(error_msg)
    with pytest.raises(ProviderAPIError) as exc_info:
        await provider.complete("Hi")
    assert str(exc_info.value) == f"Gemini API error: {error_msg}"
    assert exc_info.value.provider_type == "gemini"
    assert exc_info.value.details == {"error": error_msg}


@pytest.mark.asyncio
async def test_gemini_embed(
    provider: GeminiProvider,
    mock_client: AsyncMock,
) -> None:
    """Test Gemini embedding."""
    mock_embedding = [0.1, 0.2, 0.3]
    mock_response = {"embedding": mock_embedding}

    with patch(
        "google.generativeai.embed_content",
        return_value=mock_response,
    ):
        embedding = await provider.embed("Hello")
        assert embedding == mock_embedding


@pytest.mark.asyncio
async def test_gemini_embed_error(
    provider: GeminiProvider,
    mock_client: AsyncMock,
) -> None:
    """Test Gemini embedding error."""
    error_msg = "Embedding error"

    with patch(
        "google.generativeai.embed_content",
        side_effect=Exception(error_msg),
    ):
        with pytest.raises(ProviderAPIError) as exc_info:
            await provider.embed("Hello")
        assert str(exc_info.value) == f"Gemini API error: {error_msg}"
        assert exc_info.value.provider_type == "gemini"
        assert exc_info.value.details == {"error": error_msg}


@pytest.mark.asyncio
async def test_gemini_cleanup(provider: GeminiProvider) -> None:
    """Test Gemini provider cleanup."""
    await provider.cleanup()  # Should not raise any errors


@pytest.mark.asyncio
async def test_initialize(provider_config: ProviderConfig) -> None:
    """Test provider initialization."""
    with (
        patch("pepperpy.providers.services.gemini.GenerativeModel") as mock_model,
        patch("pepperpy.providers.services.gemini.configure"),
    ):
        provider = GeminiProvider(provider_config)
        await provider.initialize()
        assert provider._client is not None
        mock_model.assert_called_once_with("gemini-pro")


@pytest.mark.asyncio
async def test_initialize_error(provider_config: ProviderConfig) -> None:
    """Test provider initialization error."""
    error_msg = "Init error"
    with (
        patch(
            "pepperpy.providers.services.gemini.GenerativeModel",
            side_effect=Exception(error_msg),
        ),
        patch("pepperpy.providers.services.gemini.configure"),
    ):
        provider = GeminiProvider(provider_config)
        with pytest.raises(ProviderInitError) as exc_info:
            await provider.initialize()
        assert (
            str(exc_info.value) == f"Failed to initialize Gemini provider: {error_msg}"
        )
        assert exc_info.value.provider_type == "gemini"
        assert exc_info.value.details == {"error": error_msg}


@pytest.mark.asyncio
async def test_complete_with_options(
    provider: GeminiProvider, mock_client: AsyncMock
) -> None:
    """Test completion with custom options."""
    mock_response = MagicMock()
    mock_response.text = "test response"
    mock_client.generate_content_async.return_value = mock_response

    response = await provider.complete(
        "test prompt",
        temperature=0.5,
        max_tokens=50,
    )
    assert response == "test response"

    mock_client.generate_content_async.assert_called_once()
    call_args = mock_client.generate_content_async.call_args
    assert call_args[0][0] == "test prompt"
    assert call_args[1]["generation_config"].temperature == 0.5
    assert call_args[1]["generation_config"].max_output_tokens == 50
    assert call_args[1]["stream"] is False


@pytest.fixture
async def gemini_provider() -> AsyncGenerator[GeminiProvider, None]:
    """Create a Gemini provider instance.

    Returns:
        An initialized Gemini provider instance.

    Yields:
        The Gemini provider instance.
    """
    config = ProviderConfig(
        provider_type="gemini",
        api_key=SecretStr("test-key"),
        model="gemini-pro",
    )
    provider = GeminiProvider(config)
    await provider.initialize()
    yield provider
    await provider.cleanup()


async def test_gemini_provider_initialization() -> None:
    """Test Gemini provider initialization."""
    config = ProviderConfig(
        provider_type="gemini",
        api_key=SecretStr("test-key"),
        model="gemini-pro",
    )
    provider = GeminiProvider(config)
    await provider.initialize()
    assert provider._client is not None
    await provider.cleanup()


async def test_gemini_provider_initialization_no_api_key() -> None:
    """Test Gemini provider initialization without API key."""
    config = ProviderConfig(provider_type="gemini", model="gemini-pro")
    provider = GeminiProvider(config)
    with pytest.raises(ProviderInitError):
        await provider.initialize()


async def test_gemini_provider_completion(gemini_provider: GeminiProvider) -> None:
    """Test Gemini provider completion."""
    response = await gemini_provider.complete("test prompt")
    assert isinstance(response, str)


async def test_gemini_provider_streaming(gemini_provider: GeminiProvider) -> None:
    """Test Gemini provider streaming."""
    response = await gemini_provider.complete("test prompt", stream=True)
    assert isinstance(response, AsyncGenerator)

    chunks = []
    async for chunk in response:
        chunks.append(chunk)
        assert isinstance(chunk, str)


async def test_gemini_provider_completion_not_initialized() -> None:
    """Test Gemini provider completion without initialization."""
    config = ProviderConfig(
        provider_type="gemini",
        api_key=SecretStr("test-key"),
        model="gemini-pro",
    )
    provider = GeminiProvider(config)
    with pytest.raises(ProviderInitError):
        await provider.complete("test prompt")
