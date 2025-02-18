"""Tests for OpenAI LLM provider."""

import os
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pepperpy.llm.providers.openai import OpenAIProvider


@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    with patch("pepperpy.llm.providers.openai.AsyncOpenAI") as mock:
        # Mock chat completion
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="Test response"))
        ]
        mock.return_value.chat.completions.create = AsyncMock(
            return_value=mock_completion
        )

        # Mock embeddings
        mock_embedding = MagicMock()
        mock_embedding.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock.return_value.embeddings.create = AsyncMock(return_value=mock_embedding)

        yield mock


@pytest.fixture
async def provider(mock_openai) -> AsyncGenerator[OpenAIProvider, None]:
    """Create test provider."""
    provider = OpenAIProvider(api_key="test_key", model="gpt-3.5-turbo")
    yield provider


@pytest.mark.asyncio
async def test_generate(provider, mock_openai):
    """Test text generation."""
    # Test basic generation
    response = await provider.generate("Test prompt")
    assert response == "Test response"

    # Verify API call
    mock_openai.return_value.chat.completions.create.assert_called_once_with(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Test prompt"}],
        temperature=0.7,
        max_tokens=None,
        stop=None,
    )


@pytest.mark.asyncio
async def test_chat(provider, mock_openai):
    """Test chat completion."""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
        {"role": "user", "content": "How are you?"},
    ]

    # Test chat completion
    response = await provider.chat(messages)
    assert response == "Test response"

    # Verify API call
    mock_openai.return_value.chat.completions.create.assert_called_once_with(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
        max_tokens=None,
        stop=None,
    )


@pytest.mark.asyncio
async def test_embed(provider, mock_openai):
    """Test text embedding."""
    # Test embedding generation
    embedding = await provider.embed("Test text")
    assert embedding == [0.1, 0.2, 0.3]

    # Verify API call
    mock_openai.return_value.embeddings.create.assert_called_once_with(
        model="text-embedding-ada-002", input="Test text"
    )


@pytest.mark.asyncio
async def test_api_key_from_env(mock_openai):
    """Test API key loading from environment."""
    # Set environment variable
    os.environ["OPENAI_API_KEY"] = "env_test_key"

    # Create provider without key
    provider = OpenAIProvider()

    # Verify client creation
    mock_openai.assert_called_once_with(api_key="env_test_key")

    # Clean up
    del os.environ["OPENAI_API_KEY"]


@pytest.mark.asyncio
async def test_custom_parameters(provider, mock_openai):
    """Test custom parameter handling."""
    # Test with custom parameters
    await provider.generate(
        "Test prompt",
        temperature=0.5,
        max_tokens=100,
        stop=["END"],
        custom_param="test",
    )

    # Verify API call with custom parameters
    mock_openai.return_value.chat.completions.create.assert_called_once_with(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Test prompt"}],
        temperature=0.5,
        max_tokens=100,
        stop=["END"],
        custom_param="test",
    )
