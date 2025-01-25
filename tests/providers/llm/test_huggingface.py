"""Tests for HuggingFace LLM provider."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from typing import AsyncIterator, Dict, Any
import json

from pepperpy.providers.llm.huggingface import HuggingFaceProvider
from pepperpy.providers.llm.types import LLMConfig

@pytest.fixture
def provider() -> HuggingFaceProvider:
    """Create a provider instance."""
    config = LLMConfig(
        api_key="test_key",
        model="test_model",
        base_url="https://test.huggingface.co/models"
    )
    return HuggingFaceProvider(config)

@pytest.mark.asyncio
async def test_initialize(provider: HuggingFaceProvider) -> None:
    """Test provider initialization."""
    with patch("aiohttp.ClientSession"):
        await provider.initialize()
        assert provider._session is not None

@pytest.mark.asyncio
async def test_generate(provider: HuggingFaceProvider) -> None:
    """Test text generation."""
    test_response = {"generated_text": "Test response"}

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = [test_response]
    mock_response.__aenter__.return_value = mock_response

    mock_session = AsyncMock()
    mock_session.post.return_value = mock_response

    with patch("aiohttp.ClientSession", return_value=mock_session):
        await provider.initialize()
        response = await provider.generate("Test prompt")
        assert response == test_response["generated_text"]

@pytest.mark.asyncio
async def test_stream(provider: HuggingFaceProvider) -> None:
    """Test streaming text generation."""
    test_chunks = [
        {"token": {"text": "Hello"}},
        {"token": {"text": " world"}},
        {"token": {"text": "!"}}
    ]

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.content = AsyncMock()
    mock_response.content.__aiter__.return_value = [json.dumps(chunk).encode() for chunk in test_chunks]
    mock_response.__aenter__.return_value = mock_response

    mock_session = AsyncMock()
    mock_session.post.return_value = mock_response

    with patch("aiohttp.ClientSession", return_value=mock_session):
        await provider.initialize()
        chunks = []
        async for chunk in provider.stream("Test prompt"):
            chunks.append(chunk)
        assert chunks == ["Hello", " world", "!"]

@pytest.mark.asyncio
async def test_generate_error(provider: HuggingFaceProvider) -> None:
    """Test error handling in text generation."""
    mock_response = AsyncMock()
    mock_response.status = 400
    mock_response.text.return_value = "Error message"
    mock_response.__aenter__.return_value = mock_response

    mock_session = AsyncMock()
    mock_session.post.return_value = mock_response

    with patch("aiohttp.ClientSession", return_value=mock_session):
        await provider.initialize()
        with pytest.raises(RuntimeError, match="HuggingFace API error: Error message"):
            await provider.generate("Test prompt")

@pytest.mark.asyncio
async def test_stream_error(provider: HuggingFaceProvider) -> None:
    """Test error handling in streaming text generation."""
    mock_response = AsyncMock()
    mock_response.status = 400
    mock_response.text.return_value = "Error message"
    mock_response.__aenter__.return_value = mock_response

    mock_session = AsyncMock()
    mock_session.post.return_value = mock_response

    with patch("aiohttp.ClientSession", return_value=mock_session):
        await provider.initialize()
        with pytest.raises(RuntimeError, match="HuggingFace API error: Error message"):
            async for _ in provider.stream("Test prompt"):
                pass

@pytest.mark.asyncio
async def test_cleanup(provider: HuggingFaceProvider) -> None:
    """Test provider cleanup."""
    mock_session = AsyncMock()
    with patch("aiohttp.ClientSession", return_value=mock_session):
        await provider.initialize()
        await provider.cleanup()
        assert provider._session is None
        mock_session.close.assert_awaited_once() 