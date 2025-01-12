"""Test embeddings module."""

from collections.abc import AsyncGenerator
from typing import cast

import pytest

from pepperpy_ai.config.embeddings import EmbeddingsConfig
from pepperpy_ai.embeddings.base import BaseEmbeddingsProvider, EmbeddingResult
from pepperpy_ai.responses import AIResponse, ResponseMetadata
from pepperpy_ai.types import Message


class TestEmbeddingsProvider(BaseEmbeddingsProvider):
    """Test embeddings provider implementation."""

    def __init__(self, config: EmbeddingsConfig) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration.
        """
        super().__init__(config)

    async def initialize(self) -> None:
        """Initialize provider."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup provider resources."""
        self._initialized = False

    async def embed(self, text: str) -> EmbeddingResult:
        """Embed text.

        Args:
            text: Text to embed.

        Returns:
            Embedding result.

        Raises:
            RuntimeError: If provider is not initialized.
        """
        if not self._initialized:
            raise RuntimeError("Provider not initialized")
        return EmbeddingResult(
            embeddings=[0.1, 0.2, 0.3],
            metadata={"model": "test", "dimensions": 3},
        )

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Embed multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding results.
        """
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
            messages: List of messages to send to provider
            model: Optional model to use
            temperature: Optional temperature parameter
            max_tokens: Optional maximum tokens parameter

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            RuntimeError: If provider is not initialized
        """
        if not self._initialized:
            raise RuntimeError("Provider not initialized")
        yield AIResponse(
            content="test response",
            metadata=cast(ResponseMetadata, {
                "model": model or self.config.model,
                "provider": "test",
                "usage": {"total_tokens": 0},
                "finish_reason": "stop",
            }),
        )


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
    with pytest.raises(RuntimeError):
        await provider.embed("test")
