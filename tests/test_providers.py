"""Tests for providers module."""

import pytest

from pepperpy_ai.providers.base import BaseProvider
from pepperpy_ai.providers.mock import MockProvider
from pepperpy_ai.responses import AIResponse


@pytest.mark.asyncio
async def test_mock_provider():
    """Test mock provider."""
    provider = MockProvider()

    # Test completion
    response = await provider.complete("Test prompt")
    assert isinstance(response, AIResponse)
    assert response.content == "Mock completion"
    assert response.metadata is None

    # Test streaming
    response = await provider.stream("Test prompt")
    assert isinstance(response, AIResponse)
    assert response.content == "Mock stream"
    assert response.metadata is None


@pytest.mark.asyncio
async def test_base_provider_abstract():
    """Test that BaseProvider cannot be instantiated."""
    with pytest.raises(TypeError):
        BaseProvider() 