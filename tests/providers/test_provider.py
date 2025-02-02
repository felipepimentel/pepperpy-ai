"""Test provider functionality."""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import MagicMock

import pytest
from pydantic import SecretStr

from pepperpy.common.errors import ProviderError
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
                "Provider not initialized", provider_type=self.config.provider_type
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
                "Provider not initialized", provider_type=self.config.provider_type
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
        enabled_providers=["local"],
        rate_limits={"local": 100},
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
