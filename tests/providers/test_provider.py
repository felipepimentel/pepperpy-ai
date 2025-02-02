"""Test provider functionality."""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import MagicMock

import pytest
from pydantic import SecretStr

from pepperpy.common.errors import ProviderError
from pepperpy.providers.domain import ProviderInitError
from pepperpy.providers.provider import Provider, ProviderConfig


class MockStreamResponse:
    """Mock response for streaming completions."""

    def __init__(self, chunks: list[str] | None = None) -> None:
        """Initialize the mock stream response."""
        self.chunks = chunks if chunks is not None else ["Hello", " World"]
        self.index = 0

    def __aiter__(self) -> "MockStreamResponse":
        """Return self as async iterator.

        Returns:
            Self as async iterator.
        """
        return self

    async def __anext__(self) -> str:
        """Get next chunk from stream.

        Returns:
            Next chunk from stream.

        Raises:
            StopAsyncIteration: When no more chunks.
        """
        if self.index >= len(self.chunks):
            raise StopAsyncIteration
        chunk = self.chunks[self.index]
        self.index += 1
        return chunk


class MockProvider(Provider):
    """Mock provider for testing."""

    mock_complete: MagicMock = MagicMock()
    mock_embed: MagicMock = MagicMock()

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the mock provider.

        Args:
            config: Provider configuration.
        """
        super().__init__(config=config)
        self._initialized = False
        self.mock_complete = MagicMock()
        self.mock_embed = MagicMock()

    async def initialize(self) -> None:
        """Initialize the provider."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up any resources used by the provider."""
        self._initialized = False

    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> str | AsyncGenerator[str, None]:
        """Complete a prompt using the test provider.

        Args:
            prompt: The prompt to complete
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text or async generator of text chunks if streaming

        Raises:
            ProviderError: If the API call fails
        """
        if not self._initialized:
            raise ProviderError(
                "Provider not initialized",
                provider_type=self.config.provider_type or "unknown",
            )

        if stream:

            async def response_generator() -> AsyncGenerator[str, None]:
                yield "Test"
                yield " response"
                yield " streaming"

            return response_generator()
        return "Test response"

    async def embed(self, text: str, **kwargs: Any) -> list[float]:
        """Mock embedding.

        Args:
            text: The text to embed.
            **kwargs: Additional provider-specific parameters

        Returns:
            A list of floats representing the embedding.

        Raises:
            ProviderError: If provider is not initialized
        """
        if not self._initialized:
            raise ProviderError(
                "Provider not initialized",
                provider_type=self.config.provider_type or "unknown",
            )

        return [0.1, 0.2, 0.3]


@pytest.fixture
def provider_config() -> ProviderConfig:
    """Create test provider config.

    Returns:
        Test provider config.
    """
    return ProviderConfig(
        provider_type="test",
        api_key=SecretStr("test-key"),
        model="test-model",
        max_retries=3,
        timeout=30,
    )


@pytest.fixture
def provider(provider_config: ProviderConfig) -> MockProvider:
    """Create a mock provider instance.

    Args:
        provider_config: The provider configuration.

    Returns:
        Initialized mock provider.
    """
    return MockProvider(config=provider_config)


@pytest.mark.asyncio
async def test_initialize(provider: MockProvider) -> None:
    """Test provider initialization."""
    assert not provider._initialized
    await provider.initialize()
    assert provider._initialized


@pytest.mark.asyncio
async def test_complete_sync(provider: MockProvider) -> None:
    """Test synchronous completion."""
    await provider.initialize()
    response = await provider.complete("test")
    assert isinstance(response, str)
    assert response == "Test response"


@pytest.mark.asyncio
async def test_complete_stream(provider: MockProvider) -> None:
    """Test streaming completion."""
    await provider.initialize()
    response = await provider.complete("test", stream=True)
    assert isinstance(response, AsyncGenerator)
    chunks = [chunk async for chunk in response]
    assert chunks == ["Test", " response", " streaming"]


@pytest.mark.asyncio
async def test_embed(provider: MockProvider) -> None:
    """Test embedding generation."""
    await provider.initialize()
    response = await provider.embed("test")
    assert isinstance(response, list)
    assert len(response) == 3
    assert all(isinstance(x, float) for x in response)


class TestProvider(Provider):
    """Test provider implementation."""

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize test provider."""
        super().__init__(config)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the provider."""
        if not self.config.api_key:
            raise ProviderInitError(
                "API key is required",
                provider_type=self.config.provider_type or "unknown",
            )
        self._initialized = True

    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> str | AsyncGenerator[str, None]:
        """Complete a prompt."""
        if not self._initialized:
            raise ProviderInitError(
                "Provider not initialized",
                provider_type=self.config.provider_type or "unknown",
            )

        if stream:

            async def response_generator() -> AsyncGenerator[str, None]:
                yield "Test"
                yield " response"
                yield " streaming"

            return response_generator()

        return "Test response"

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False

    async def embed(self, text: str, **kwargs: Any) -> list[float]:
        """Generate embeddings for text."""
        return [0.1, 0.2, 0.3]


def test_provider_init_requires_config() -> None:
    """Test that provider initialization requires config."""
    with pytest.raises(ValueError, match="Config cannot be None"):
        TestProvider(config=None)  # type: ignore


def test_provider_init_requires_api_key() -> None:
    """Test that provider initialization requires API key."""
    config = ProviderConfig(
        provider_type="test",
        model="test-model",
    )
    with pytest.raises(ProviderError, match="API key is required"):
        TestProvider(config=config)


def test_provider_init_requires_provider_type() -> None:
    """Test that provider initialization requires provider type."""
    with pytest.raises(ValueError, match="Provider type cannot be empty"):
        ProviderConfig(
            api_key=SecretStr("test-key"),
            model="test-model",
            provider_type="",  # Empty provider type should raise error
        )


def test_provider_init_success() -> None:
    """Test successful provider initialization."""
    config = ProviderConfig(
        provider_type="test",
        api_key=SecretStr("test-key"),
        model="test-model",
    )
    provider = TestProvider(config=config)
    assert provider.config == config
    assert not provider._initialized


@pytest.fixture
def test_config() -> ProviderConfig:
    """Provide test configuration."""
    return ProviderConfig(
        provider_type="test",
        api_key=SecretStr("test-key"),
        model="test-model",
    )


@pytest.fixture
async def test_provider(
    test_config: ProviderConfig,
) -> AsyncGenerator[TestProvider, None]:
    """Provide initialized test provider.

    Args:
        test_config: The provider configuration.

    Yields:
        Initialized test provider.
    """
    provider = TestProvider(config=test_config)
    await provider.initialize()
    yield provider
    await provider.cleanup()


async def test_provider_initialization() -> None:
    """Test provider initialization."""
    config = ProviderConfig(
        provider_type="test",
        api_key=SecretStr("test-key"),
        model="test-model",
    )
    provider = TestProvider(config)
    await provider.initialize()
    assert provider._initialized
    await provider.cleanup()


async def test_provider_initialization_no_api_key() -> None:
    """Test provider initialization without API key."""
    config = ProviderConfig(provider_type="test", model="test-model")
    provider = TestProvider(config)
    with pytest.raises(ProviderInitError):
        await provider.initialize()


async def test_provider_completion(test_provider: TestProvider) -> None:
    """Test provider completion."""
    response = await test_provider.complete("test prompt")
    assert isinstance(response, str)
    assert response == "Test response"


async def test_provider_streaming(test_provider: TestProvider) -> None:
    """Test provider streaming."""
    response = await test_provider.complete("test prompt", stream=True)
    assert isinstance(response, AsyncGenerator)

    chunks = []
    async for chunk in response:
        chunks.append(chunk)

    assert chunks == ["Test", " response", " streaming"]


async def test_provider_completion_not_initialized() -> None:
    """Test provider completion without initialization."""
    config = ProviderConfig(
        provider_type="test",
        api_key=SecretStr("test-key"),
        model="test-model",
    )
    provider = TestProvider(config)
    with pytest.raises(ProviderInitError):
        await provider.complete("test prompt")
