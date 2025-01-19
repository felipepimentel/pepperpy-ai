"""Tests for OpenRouter LLM provider."""

import json
import os
from datetime import datetime
from typing import AsyncIterator, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import aiohttp
from pepperpy.llms.openrouter import OpenRouterProvider
from pepperpy.llms.types import LLMResponse, ProviderConfig


@pytest.fixture
def config() -> ProviderConfig:
    """Create provider config."""
    return ProviderConfig(
        type="openrouter",
        model_name="anthropic/claude-2",
        api_key="test-key",
        temperature=0.7,
        max_tokens=1000
    )


@pytest.fixture
async def provider(config: ProviderConfig) -> AsyncIterator[OpenRouterProvider]:
    """Create OpenRouter provider."""
    provider = OpenRouterProvider(config)
    await provider.initialize()
    yield provider
    await provider.cleanup()


async def test_initialize(provider: OpenRouterProvider) -> None:
    """Test provider initialization."""
    assert provider.is_initialized
    assert provider.session is not None


async def test_cleanup(provider: OpenRouterProvider) -> None:
    """Test provider cleanup."""
    await provider.cleanup()
    assert not provider.is_initialized
    assert provider.session is None


@patch("aiohttp.ClientSession.post")
async def test_generate(mock_post: MagicMock, provider: OpenRouterProvider) -> None:
    """Test text generation."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "choices": [{
            "message": {
                "content": "Test response"
            }
        }],
        "usage": {
            "total_tokens": 10,
            "prompt_tokens": 5,
            "completion_tokens": 5
        }
    })
    mock_post.return_value.__aenter__.return_value = mock_response

    # Generate text
    response = await provider.generate("Test prompt")
    assert isinstance(response, LLMResponse)
    assert response.text == "Test response"
    assert response.tokens_used == 10
    assert response.cost > 0
    assert response.model_name == "anthropic/claude-2"
    assert isinstance(response.timestamp, datetime)


@patch("aiohttp.ClientSession.post")
async def test_generate_stream(mock_post: MagicMock, provider: OpenRouterProvider) -> None:
    """Test streaming text generation."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.content.iter_any = AsyncMock(return_value=[
        b'data: {"choices":[{"delta":{"content":"Test"}}]}\n\n',
        b'data: {"choices":[{"delta":{"content":" response"}}]}\n\n',
        b'data: [DONE]\n\n'
    ])
    mock_post.return_value.__aenter__.return_value = mock_response

    # Generate stream
    chunks = []
    async for chunk in provider.generate_stream("Test prompt"):
        chunks.append(chunk)

    assert chunks == ["Test", " response"]


@patch("aiohttp.ClientSession.post")
async def test_get_embedding(mock_post: MagicMock, provider: OpenRouterProvider) -> None:
    """Test embedding generation."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "data": [{
            "embedding": [0.1, 0.2, 0.3]
        }]
    })
    mock_post.return_value.__aenter__.return_value = mock_response

    # Get embedding
    embedding = await provider.get_embedding("Test text")
    assert isinstance(embedding, list)
    assert len(embedding) > 0
    assert all(isinstance(x, float) for x in embedding)


@patch("aiohttp.ClientSession.post")
async def test_generate_error(mock_post: MagicMock, provider: OpenRouterProvider) -> None:
    """Test error handling in text generation."""
    # Mock error response
    mock_response = MagicMock()
    mock_response.status = 400
    mock_response.json = AsyncMock(return_value={"error": "Test error"})
    mock_post.return_value.__aenter__.return_value = mock_response

    # Generate text should raise exception
    with pytest.raises(Exception):
        await provider.generate("Test prompt")


@patch("aiohttp.ClientSession.post")
async def test_generate_stream_error(mock_post: MagicMock, provider: OpenRouterProvider) -> None:
    """Test error handling in streaming text generation."""
    # Mock error response
    mock_response = MagicMock()
    mock_response.status = 400
    mock_response.json = AsyncMock(return_value={"error": "Test error"})
    mock_post.return_value.__aenter__.return_value = mock_response

    # Generate stream should raise exception
    with pytest.raises(Exception):
        async for _ in provider.generate_stream("Test prompt"):
            pass


@patch("aiohttp.ClientSession.post")
async def test_get_embedding_error(mock_post: MagicMock, provider: OpenRouterProvider) -> None:
    """Test error handling in embedding generation."""
    # Mock error response
    mock_response = MagicMock()
    mock_response.status = 400
    mock_response.json = AsyncMock(return_value={"error": "Test error"})
    mock_post.return_value.__aenter__.return_value = mock_response

    # Get embedding should raise exception
    with pytest.raises(Exception):
        await provider.get_embedding("Test text") 