"""Unit tests for OpenAI embedding provider."""

import os
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai.types.embedding import Embedding
from openai.types.create_embedding_response import CreateEmbeddingResponse
from openai.types.create_embedding_response import Usage

from pepperpy.core.utils.errors import ProviderError
from pepperpy.providers.embedding.openai import OpenAIEmbeddingProvider


@pytest.fixture
def mock_response() -> CreateEmbeddingResponse:
    """Create a mock OpenAI embedding response."""
    embedding = Embedding(
        embedding=[0.1, 0.2, 0.3],
        index=0,
        object="embedding",
    )
    return CreateEmbeddingResponse(
        data=[embedding],
        model="text-embedding-3-small",
        object="list",
        usage=Usage(
            prompt_tokens=10,
            total_tokens=10,
        ),
    )


@pytest.fixture
def mock_batch_response() -> CreateEmbeddingResponse:
    """Create a mock OpenAI batch embedding response."""
    embeddings = [
        Embedding(
            embedding=[0.1, 0.2, 0.3],
            index=0,
            object="embedding",
        ),
        Embedding(
            embedding=[0.4, 0.5, 0.6],
            index=1,
            object="embedding",
        ),
    ]
    return CreateEmbeddingResponse(
        data=embeddings,
        model="text-embedding-3-small",
        object="list",
        usage=Usage(
            prompt_tokens=20,
            total_tokens=20,
        ),
    )


@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Provide test configuration."""
    return {
        "api_key": "test-key",
        "model": "text-embedding-3-small",
        "dimensions": 3,
        "timeout": 10,
    }


@pytest.mark.asyncio
async def test_initialization(test_config: Dict[str, Any]) -> None:
    """Test provider initialization."""
    provider = OpenAIEmbeddingProvider(test_config)
    assert not provider.is_initialized
    
    with patch("openai.AsyncOpenAI"):
        await provider.initialize()
        assert provider.is_initialized


@pytest.mark.asyncio
async def test_initialization_no_api_key() -> None:
    """Test initialization without API key."""
    provider = OpenAIEmbeddingProvider()
    
    with pytest.raises(ProviderError) as exc_info:
        await provider.initialize()
    assert "API key not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_embed_text(
    test_config: Dict[str, Any],
    mock_response: CreateEmbeddingResponse,
) -> None:
    """Test single text embedding."""
    provider = OpenAIEmbeddingProvider(test_config)
    
    with patch("openai.AsyncOpenAI") as mock_client:
        mock_client.return_value.embeddings.create = AsyncMock(return_value=mock_response)
        await provider.initialize()
        
        embedding = await provider.embed_text("test text")
        assert isinstance(embedding, list)
        assert len(embedding) == 3
        assert embedding == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_embed_texts(
    test_config: Dict[str, Any],
    mock_batch_response: CreateEmbeddingResponse,
) -> None:
    """Test batch text embedding."""
    provider = OpenAIEmbeddingProvider(test_config)
    
    with patch("openai.AsyncOpenAI") as mock_client:
        mock_client.return_value.embeddings.create = AsyncMock(return_value=mock_batch_response)
        await provider.initialize()
        
        embeddings = await provider.embed_texts(["test 1", "test 2"])
        assert isinstance(embeddings, list)
        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2, 0.3]
        assert embeddings[1] == [0.4, 0.5, 0.6]


@pytest.mark.asyncio
async def test_embed_query(
    test_config: Dict[str, Any],
    mock_response: CreateEmbeddingResponse,
) -> None:
    """Test query embedding."""
    provider = OpenAIEmbeddingProvider(test_config)
    
    with patch("openai.AsyncOpenAI") as mock_client:
        mock_client.return_value.embeddings.create = AsyncMock(return_value=mock_response)
        await provider.initialize()
        
        embedding = await provider.embed_query("test query")
        assert isinstance(embedding, list)
        assert len(embedding) == 3
        assert embedding == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_get_embedding_dimension(test_config: Dict[str, Any]) -> None:
    """Test getting embedding dimension."""
    provider = OpenAIEmbeddingProvider(test_config)
    dim = await provider.get_embedding_dimension()
    assert dim == 3


@pytest.mark.asyncio
async def test_get_metadata(test_config: Dict[str, Any]) -> None:
    """Test getting provider metadata."""
    provider = OpenAIEmbeddingProvider(test_config)
    metadata = await provider.get_metadata()
    
    assert metadata["model_name"] == "text-embedding-3-small"
    assert metadata["dimension"] == 3
    assert metadata["max_length"] == 8191
    assert metadata["supports_batching"] is True
    assert metadata["provider_name"] == "openai"


@pytest.mark.asyncio
async def test_error_handling(test_config: Dict[str, Any]) -> None:
    """Test error handling."""
    provider = OpenAIEmbeddingProvider(test_config)
    
    # Test uninitialized error
    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_text("test")
    assert "not initialized" in str(exc_info.value)
    
    # Test API error
    with patch("openai.AsyncOpenAI") as mock_client:
        mock_client.return_value.embeddings.create = AsyncMock(
            side_effect=Exception("API Error")
        )
        await provider.initialize()
        
        with pytest.raises(ProviderError) as exc_info:
            await provider.embed_text("test")
        assert "Failed to generate embedding" in str(exc_info.value) 