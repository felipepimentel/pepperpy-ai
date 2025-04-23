"""
Test the OpenAI Embeddings Provider.
"""

import pytest

from plugins.embedding.openai.provider import OpenAIEmbeddingsProvider


@pytest.mark.asyncio
async def test_openai_provider_initialization():
    """Test provider initialization."""
    provider = OpenAIEmbeddingsProvider(
        api_key="test_key", model="text-embedding-3-small", dimensions=128
    )

    assert provider.api_key == "test_key"
    assert provider.model == "text-embedding-3-small"
    assert provider.dimensions == 128
    assert provider.initialized is False

    # Test initialization
    await provider.initialize()
    assert provider.initialized is True

    # Test cleanup
    await provider.cleanup()
    assert provider.initialized is False


@pytest.mark.asyncio
async def test_openai_provider_example_task():
    """Test example task execution."""
    provider = OpenAIEmbeddingsProvider(api_key="test_key")

    # Test example task
    result = await provider.execute({"task": "example_task"})
    assert result["status"] == "success"
    assert result["result"] == "Task executed successfully"


@pytest.mark.asyncio
async def test_openai_provider_embed_text():
    """Test text embedding."""
    provider = OpenAIEmbeddingsProvider(api_key="test_key", dimensions=128)

    # Test embedding
    text = "This is a test sentence for embedding."
    result = await provider.execute({"task": "embed_text", "text": text})

    assert result["status"] == "success"
    assert "result" in result
    assert isinstance(result["result"], list)
    assert len(result["result"]) == 128


@pytest.mark.asyncio
async def test_openai_provider_error_handling():
    """Test error handling."""
    provider = OpenAIEmbeddingsProvider(api_key="test_key")

    # Test missing task
    result = await provider.execute({})
    assert result["status"] == "error"
    assert "message" in result

    # Test missing text
    result = await provider.execute({"task": "embed_text"})
    assert result["status"] == "error"
    assert "message" in result

    # Test unknown task
    result = await provider.execute({"task": "unknown_task"})
    assert result["status"] == "error"
    assert "message" in result
