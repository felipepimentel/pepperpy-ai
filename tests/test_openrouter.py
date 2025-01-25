"""Test OpenRouter provider functionality."""

import json
from collections.abc import AsyncIterator
from typing import Any, Dict
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pepperpy.providers.llm.openrouter import OpenRouterProvider
from pepperpy.providers.llm.types import LLMResponse, ProviderConfig


@pytest.fixture
def config() -> ProviderConfig:
    """Create provider config."""
    return ProviderConfig(
        type="openrouter",
        model_name="test-model",
        api_key="test-key"
    )


@pytest.fixture
async def provider(config: ProviderConfig) -> AsyncIterator[OpenRouterProvider]:
    """Create provider instance."""
    provider = OpenRouterProvider(config)
    await provider.initialize()
    yield provider
    await provider.cleanup()


@patch("aiohttp.ClientSession.post")
async def test_generate(mock_post: MagicMock, provider: OpenRouterProvider) -> None:
    """Test text generation."""
    # Mock response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "choices": [{"text": "Test response"}],
        "usage": {
            "total_tokens": 10,
            "completion_tokens": 5,
            "prompt_tokens": 5
        },
        "model": "test-model"
    }
    mock_post.return_value.__aenter__.return_value = mock_response

    # Generate text
    response = await provider.generate("Test prompt")
    assert isinstance(response, LLMResponse)
    assert response.text == "Test response"
    assert response.tokens_used == 10
    assert response.finish_reason == "stop"
    assert response.model_name == "test-model"
    assert response.cost == 0.0
    assert isinstance(response.timestamp, datetime)
    assert isinstance(response.metadata, dict)


@patch("aiohttp.ClientSession.post")
async def test_generate_stream(mock_post: MagicMock, provider: OpenRouterProvider) -> None:
    """Test streaming text generation."""
    # Mock response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.content.iter_any = AsyncMock(
        return_value=[
            'data: {"choices":[{"text":"Test"}],"model":"test-model"}\n\n'.encode()
        ]
    )
    mock_post.return_value.__aenter__.return_value = mock_response

    # Generate stream
    async for text in provider.generate_stream("Test prompt"):
        assert text == "Test"


@patch("aiohttp.ClientSession.post")
async def test_get_embedding(mock_post: MagicMock, provider: OpenRouterProvider) -> None:
    """Test embedding generation."""
    # Mock response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "data": [{"embedding": [0.1, 0.2, 0.3]}],
        "model": "test-model"
    }
    mock_post.return_value.__aenter__.return_value = mock_response

    # Get embedding
    embedding = await provider.get_embedding("Test text")
    assert isinstance(embedding, list)
    assert len(embedding) == 3
    assert embedding == [0.1, 0.2, 0.3]


@patch("aiohttp.ClientSession.post")
async def test_generate_error(mock_post: MagicMock, provider: OpenRouterProvider) -> None:
    """Test error handling in text generation."""
    # Mock error response
    mock_response = AsyncMock()
    mock_response.status = 400
    mock_response.json.return_value = {"error": "Test error"}
    mock_post.return_value.__aenter__.return_value = mock_response

    # Generate text should raise exception
    with pytest.raises(Exception, match="Test error"):
        await provider.generate("Test prompt")


@patch("aiohttp.ClientSession.post")
async def test_generate_stream_error(mock_post: MagicMock, provider: OpenRouterProvider) -> None:
    """Test error handling in streaming text generation."""
    # Mock error response
    mock_response = AsyncMock()
    mock_response.status = 400
    mock_response.json.return_value = {"error": "Test error"}
    mock_post.return_value.__aenter__.return_value = mock_response

    # Generate stream should raise exception
    with pytest.raises(Exception, match="Test error"):
        async for _ in provider.generate_stream("Test prompt"):
            pass


@patch("aiohttp.ClientSession.post")
async def test_get_embedding_error(mock_post: MagicMock, provider: OpenRouterProvider) -> None:
    """Test error handling in embedding generation."""
    # Mock error response
    mock_response = AsyncMock()
    mock_response.status = 400
    mock_response.json.return_value = {"error": "Test error"}
    mock_post.return_value.__aenter__.return_value = mock_response

    # Get embedding should raise exception
    with pytest.raises(Exception, match="Test error"):
        await provider.get_embedding("Test text") 