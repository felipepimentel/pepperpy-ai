"""Tests for providers module."""

import pytest
from typing import Any

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
    async for response in await provider.stream("Test prompt"):
        assert isinstance(response, AIResponse)
        assert response.content == "Mock stream"
        assert response.metadata is None


def test_base_provider_abstract():
    """Test that BaseProvider is abstract."""
    # Verify that BaseProvider has abstract methods
    assert hasattr(BaseProvider, "complete")
    assert hasattr(BaseProvider, "stream")

    # Try to create a concrete class missing the abstract methods
    with pytest.raises(TypeError) as exc_info:
        class ConcreteProvider(BaseProvider):
            pass
        ConcreteProvider() 