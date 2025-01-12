"""Tests for embeddings functionality."""

import pytest

from pepperpy_ai.embeddings.base import EmbeddingsConfig
from pepperpy_ai.embeddings.client import EmbeddingsClient
from pepperpy_ai.embeddings.providers import SimpleEmbeddingsProvider


@pytest.mark.asyncio
async def test_simple_embeddings_initialization(initialized_embeddings_client: EmbeddingsClient) -> None:
    """Test that simple embeddings can be initialized."""
    assert initialized_embeddings_client.is_initialized


@pytest.mark.asyncio
async def test_simple_embeddings_embed(initialized_embeddings_client: EmbeddingsClient) -> None:
    """Test that simple embeddings can embed text."""
    text = "Hello, world!"
    result = await initialized_embeddings_client.embed(text)
    assert isinstance(result, list)
    assert all(isinstance(x, float) for x in result)
    assert len(result) == 384  # Default dimension


@pytest.mark.asyncio
async def test_simple_embeddings_embed_batch(initialized_embeddings_client: EmbeddingsClient) -> None:
    """Test that simple embeddings can embed multiple texts."""
    texts = ["Hello, world!", "Another text", "And another one"]
    results = await initialized_embeddings_client.embed_batch(texts)
    assert isinstance(results, list)
    assert len(results) == len(texts)
    for result in results:
        assert isinstance(result, list)
        assert all(isinstance(x, float) for x in result)
        assert len(result) == 384  # Default dimension


@pytest.mark.asyncio
async def test_simple_embeddings_deterministic(initialized_embeddings_client: EmbeddingsClient) -> None:
    """Test that simple embeddings are deterministic for the same input."""
    text = "Hello, world!"
    result1 = await initialized_embeddings_client.embed(text)
    result2 = await initialized_embeddings_client.embed(text)
    assert result1 == result2


@pytest.mark.asyncio
async def test_simple_embeddings_cleanup(embeddings_client: EmbeddingsClient) -> None:
    """Test that simple embeddings can be cleaned up."""
    await embeddings_client.initialize()
    assert embeddings_client.is_initialized
    await embeddings_client.cleanup()
    assert not embeddings_client.is_initialized


@pytest.mark.asyncio
async def test_simple_embeddings_custom_dimension() -> None:
    """Test that simple embeddings can be configured with custom dimension."""
    dimension = 128
    config = EmbeddingsConfig(dimension=dimension)
    client = EmbeddingsClient(SimpleEmbeddingsProvider, config)
    await client.initialize()
    try:
        text = "Hello, world!"
        result = await client.embed(text)
        assert len(result) == dimension
    finally:
        await client.cleanup() 