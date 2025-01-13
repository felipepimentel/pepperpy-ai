"""Test embeddings module."""

from collections.abc import AsyncGenerator
from typing import Any

import pytest

from pepperpy_ai.ai_types import Message, MessageRole
from pepperpy_ai.config.embeddings import EmbeddingsConfig
from pepperpy_ai.embeddings.base import BaseEmbeddingsProvider, EmbeddingResult
from pepperpy_ai.exceptions import ProviderError
from pepperpy_ai.providers.base import BaseProvider
from pepperpy_ai.responses import AIResponse


class TestEmbeddingsProvider(BaseEmbeddingsProvider):
    """Test embeddings provider."""

    def __init__(self, config: EmbeddingsConfig) -> None:
        """Initialize test provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Return whether provider is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize test provider."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup test provider."""
        self._initialized = False

    async def embed(self, text: str) -> EmbeddingResult:
        """Embed text using test provider.

        Args:
            text: Text to embed

        Returns:
            EmbeddingResult: Embedding result

        Raises:
            ProviderError: If provider is not initialized
        """
        if not self.is_initialized:
            raise ProviderError("Provider not initialized", provider="test", operation="embed")
        return EmbeddingResult(
            embeddings=[0.1, 0.2, 0.3],
            metadata={"model": "test", "dimensions": 3},
        )

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Embed texts using test provider.

        Args:
            texts: Texts to embed

        Returns:
            list[EmbeddingResult]: Embedding results

        Raises:
            ProviderError: If provider is not initialized
        """
        if not self.is_initialized:
            raise ProviderError("Provider not initialized", provider="test", operation="embed_batch")
        return [
            EmbeddingResult(
                embeddings=[0.1, 0.2, 0.3],
                metadata={"model": "test", "dimensions": 3},
            )
            for _ in texts
        ]

    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from test provider.

        Args:
            messages: Messages to send to provider
            model: Model to use
            temperature: Temperature to use
            max_tokens: Maximum tokens to generate

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            ProviderError: If provider is not initialized
        """
        if not self.is_initialized:
            raise ProviderError("Provider not initialized", provider="test", operation="stream")
        yield AIResponse(content="test")


@pytest.mark.asyncio
async def test_embeddings_provider() -> None:
    """Test embeddings provider functionality."""
    config = EmbeddingsConfig(name="test", version="1.0", model="test-model")
    provider = TestEmbeddingsProvider(config)
    await provider.initialize()
    result = await provider.embed("test")
    assert result.embeddings == [0.1, 0.2, 0.3]
    assert result.metadata == {"model": "test", "dimensions": 3}
    await provider.cleanup()


@pytest.mark.asyncio
async def test_embeddings_provider_batch() -> None:
    """Test embeddings provider batch functionality."""
    config = EmbeddingsConfig(name="test", version="1.0", model="test-model")
    provider = TestEmbeddingsProvider(config)
    await provider.initialize()
    results = await provider.embed_batch(["test1", "test2"])
    assert len(results) == 2
    for result in results:
        assert result.embeddings == [0.1, 0.2, 0.3]
        assert result.metadata == {"model": "test", "dimensions": 3}
    await provider.cleanup()


@pytest.mark.asyncio
async def test_embeddings_provider_error() -> None:
    """Test embeddings provider error handling."""
    config = EmbeddingsConfig(name="test", version="1.0", model="test-model")
    provider = TestEmbeddingsProvider(config)
    with pytest.raises(ProviderError) as exc_info:
        await provider.embed("test")
    assert exc_info.value.context["provider"] == "test"
    assert exc_info.value.context["operation"] == "embed"
