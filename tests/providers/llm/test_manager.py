"""Tests for LLM manager."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from typing import Dict, Any, AsyncIterator

from pepperpy.providers.llm.manager import LLMManager, PROVIDER_TYPES
from pepperpy.providers.llm.huggingface import HuggingFaceProvider
from pepperpy.providers.llm.types import LLMConfig

@pytest.fixture
def config() -> Dict[str, Dict[str, Any]]:
    """Create test configuration."""
    return {
        "main": {
            "api_key": "test_key",
            "model": "test_model",
            "base_url": "https://test.huggingface.co/models",
            "is_fallback": False,
            "max_tokens": 100,
            "temperature": 0.7
        },
        "fallback": {
            "api_key": "test_key",
            "model": "test_model",
            "base_url": "https://test.huggingface.co/models",
            "is_fallback": True,
            "max_tokens": 100,
            "temperature": 0.7
        }
    }

@pytest.fixture
def manager() -> LLMManager:
    """Create a manager instance."""
    return LLMManager()

@pytest.mark.asyncio
async def test_initialize(manager: LLMManager, config: Dict[str, Dict[str, Any]]) -> None:
    """Test manager initialization."""
    with patch.object(HuggingFaceProvider, "initialize"):
        await manager.initialize(config)
        assert len(manager.providers) == 2
        assert len(manager.configs) == 2
        assert manager._is_initialized

@pytest.mark.asyncio
async def test_get_primary_provider(manager: LLMManager, config: Dict[str, Dict[str, Any]]) -> None:
    """Test getting primary provider."""
    with patch.object(HuggingFaceProvider, "initialize"):
        await manager.initialize(config)
        provider = manager.get_primary_provider()
        assert provider == manager.providers["main"]
        assert not manager.configs["main"].is_fallback

@pytest.mark.asyncio
async def test_get_fallback_providers(manager: LLMManager, config: Dict[str, Dict[str, Any]]) -> None:
    """Test getting fallback providers."""
    with patch.object(HuggingFaceProvider, "initialize"):
        await manager.initialize(config)
        fallbacks = manager.get_fallback_providers()
        assert len(fallbacks) == 1
        assert fallbacks[0] == manager.providers["fallback"]
        assert manager.configs["fallback"].is_fallback

@pytest.mark.asyncio
async def test_generate(manager: LLMManager, config: Dict[str, Dict[str, Any]]) -> None:
    """Test text generation."""
    test_response = "Test response"

    with patch.object(HuggingFaceProvider, "initialize"), \
         patch.object(HuggingFaceProvider, "generate", return_value=test_response):
        await manager.initialize(config)
        response = await manager.generate("Test prompt")
        assert response == test_response

@pytest.mark.asyncio
async def test_generate_with_fallback(manager: LLMManager, config: Dict[str, Dict[str, Any]]) -> None:
    """Test text generation with fallback."""
    test_response = "Test response"

    with patch.object(HuggingFaceProvider, "initialize"), \
         patch.object(HuggingFaceProvider, "generate", side_effect=[RuntimeError, test_response]):
        await manager.initialize(config)
        response = await manager.generate("Test prompt")
        assert response == test_response

@pytest.mark.asyncio
async def test_stream(manager: LLMManager, config: Dict[str, Dict[str, Any]]) -> None:
    """Test streaming text generation."""
    test_chunks = ["Hello", " world", "!"]

    async def mock_stream(*args, **kwargs):
        for chunk in test_chunks:
            yield chunk

    with patch.object(HuggingFaceProvider, "initialize"), \
         patch.object(HuggingFaceProvider, "stream", side_effect=mock_stream):
        await manager.initialize(config)
        chunks = []
        async for chunk in manager.stream("Test prompt"):
            chunks.append(chunk)
        assert chunks == test_chunks

@pytest.mark.asyncio
async def test_stream_with_fallback(manager: LLMManager, config: Dict[str, Dict[str, Any]]) -> None:
    """Test streaming text generation with fallback."""
    test_chunks = ["Hello", " world", "!"]

    async def mock_stream(*args, **kwargs) -> AsyncIterator[str]:
        for chunk in test_chunks:
            yield chunk

    mock_stream_gen = mock_stream()

    with patch.object(HuggingFaceProvider, "initialize"), \
         patch.object(HuggingFaceProvider, "stream", side_effect=[RuntimeError, mock_stream_gen]):
        await manager.initialize(config)
        chunks = []
        async for chunk in manager.stream("Test prompt"):
            chunks.append(chunk)
        assert chunks == test_chunks

@pytest.mark.asyncio
async def test_cleanup(manager: LLMManager, config: Dict[str, Dict[str, Any]]) -> None:
    """Test manager cleanup."""
    with patch.object(HuggingFaceProvider, "initialize"), \
         patch.object(HuggingFaceProvider, "cleanup") as mock_cleanup:
        await manager.initialize(config)
        await manager.cleanup()
        assert not manager._is_initialized
        assert not manager.providers
        assert not manager.configs
        assert mock_cleanup.call_count == 2 