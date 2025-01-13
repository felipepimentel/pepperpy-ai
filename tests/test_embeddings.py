"""Test embeddings module."""

from collections.abc import AsyncGenerator
from typing import Any

import pytest

from pepperpy_ai.core.responses import AIResponse, ResponseMetadata
from pepperpy_ai.embeddings.base import BaseEmbeddingsProvider, EmbeddingResult
from pepperpy_ai.embeddings.config import EmbeddingsConfig
from pepperpy_ai.exceptions import ProviderError
from pepperpy_ai.types import Message


class TestEmbeddingsProvider(BaseEmbeddingsProvider):
    """Test embeddings provider."""

    def __init__(self, config: EmbeddingsConfig) -> None:
        """Initialize test provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config, api_key="test_key")
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

    async def embed(
        self, texts: list[str], **kwargs: dict[str, Any]
    ) -> list[EmbeddingResult]:
        """Embed text using test provider.

        Args:
            texts: Texts to embed
            **kwargs: Additional keyword arguments

        Returns:
            list[EmbeddingResult]: List of embedding results

        Raises:
            ProviderError: If provider is not initialized
        """
        if not self.is_initialized:
            raise ProviderError(
                "Provider not initialized", provider="test", operation="embed"
            )

        return [
            EmbeddingResult(
                embeddings=[0.1, 0.2, 0.3],
                metadata={"model": "test-model"},
            )
            for _ in texts
        ]

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Embed batch of texts using test provider.

        Args:
            texts: Texts to embed

        Returns:
            list[EmbeddingResult]: List of embedding results

        Raises:
            ProviderError: If provider is not initialized
        """
        return await self.embed(texts)

    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: dict[str, Any],
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from test provider.

        Args:
            messages: Messages to stream
            model: Model to use
            temperature: Temperature to use
            max_tokens: Maximum tokens to generate
            **kwargs: Additional keyword arguments

        Yields:
            AIResponse: Response from provider

        Raises:
            ProviderError: If provider is not initialized
        """
        if not self.is_initialized:
            raise ProviderError(
                "Provider not initialized", provider="test", operation="stream"
            )

        yield AIResponse(
            content="test",
            metadata=ResponseMetadata(
                model=model or "test-model",
                provider="test",
                usage={
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
                finish_reason="stop",
            ),
        )


@pytest.mark.asyncio
async def test_embeddings_provider() -> None:
    """Test embeddings provider functionality."""
    config = EmbeddingsConfig(
        model_name="test-model",
        dimension=3,
        batch_size=1,
    )
    provider = TestEmbeddingsProvider(config)

    await provider.initialize()
    assert provider.is_initialized

    result = await provider.embed(["test"])
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], EmbeddingResult)
    assert result[0].embeddings == [0.1, 0.2, 0.3]
    assert result[0].metadata == {"model": "test-model"}

    await provider.cleanup()
    assert not provider.is_initialized


@pytest.mark.asyncio
async def test_embeddings_provider_batch() -> None:
    """Test embeddings provider batch functionality."""
    config = EmbeddingsConfig(
        model_name="test-model",
        dimension=3,
        batch_size=2,
    )
    provider = TestEmbeddingsProvider(config)

    await provider.initialize()
    assert provider.is_initialized

    texts = ["test1", "test2"]
    result = await provider.embed_batch(texts)
    assert isinstance(result, list)
    assert len(result) == 2
    for res in result:
        assert isinstance(res, EmbeddingResult)
        assert res.embeddings == [0.1, 0.2, 0.3]
        assert res.metadata == {"model": "test-model"}

    await provider.cleanup()
    assert not provider.is_initialized


@pytest.mark.asyncio
async def test_embeddings_provider_error() -> None:
    """Test embeddings provider error handling."""
    config = EmbeddingsConfig(
        model_name="test-model",
        dimension=3,
        batch_size=1,
    )
    provider = TestEmbeddingsProvider(config)

    with pytest.raises(ProviderError) as exc_info:
        await provider.embed(["test"])
    assert str(exc_info.value) == "Provider not initialized"
