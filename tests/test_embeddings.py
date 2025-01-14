"""Embeddings tests."""

from typing import Any

import pytest

from pepperpy.embeddings.base import BaseEmbeddingsProvider
from pepperpy.exceptions import ProviderError
from pepperpy.types import CapabilityConfig


class TestEmbeddingsProvider(BaseEmbeddingsProvider):
    """Test embeddings provider."""

    def __init__(self, config: CapabilityConfig) -> None:
        """Initialize test embeddings provider.

        Args:
            config: Provider configuration.
        """
        super().__init__(config)

    async def _embed_texts(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        """Embed texts.

        Args:
            texts: List of texts to embed.
            **kwargs: Additional arguments.

        Returns:
            list[list[float]]: List of embeddings.

        Raises:
            ProviderError: If embedding fails.
        """
        if not texts:
            raise ProviderError("No texts provided")

        return [[0.1, 0.2, 0.3] for _ in texts]

    async def _embed_text(self, text: str, **kwargs: Any) -> list[float]:
        """Embed text.

        Args:
            text: Text to embed.
            **kwargs: Additional arguments.

        Returns:
            list[float]: Embedding.

        Raises:
            ProviderError: If embedding fails.
        """
        if not text:
            raise ProviderError("No text provided")

        return [0.1, 0.2, 0.3]


@pytest.fixture
def provider() -> TestEmbeddingsProvider:
    """Create test provider."""
    config = CapabilityConfig(name="test", version="1.0.0")
    return TestEmbeddingsProvider(config)


async def test_embeddings_provider(provider: TestEmbeddingsProvider) -> None:
    """Test embeddings provider."""
    await provider.initialize()
    assert provider.is_initialized

    embedding = await provider.embed_text("test")
    assert isinstance(embedding, list)
    assert len(embedding) == 3
    assert all(isinstance(x, float) for x in embedding)


async def test_embeddings_provider_batch(provider: TestEmbeddingsProvider) -> None:
    """Test embeddings provider batch."""
    await provider.initialize()
    assert provider.is_initialized

    embeddings = await provider.embed_texts(["test1", "test2"])
    assert isinstance(embeddings, list)
    assert len(embeddings) == 2
    assert all(isinstance(x, list) for x in embeddings)
    assert all(len(x) == 3 for x in embeddings)
    assert all(isinstance(y, float) for x in embeddings for y in x)


async def test_embeddings_provider_error(provider: TestEmbeddingsProvider) -> None:
    """Test embeddings provider error."""
    await provider.initialize()
    assert provider.is_initialized

    with pytest.raises(ProviderError):
        await provider.embed_text("")

    with pytest.raises(ProviderError):
        await provider.embed_texts([])
