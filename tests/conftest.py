"""Test fixtures module."""

from collections.abc import AsyncGenerator

import pytest

from pepperpy_ai.providers.mock import MockConfig, MockProvider


@pytest.fixture
async def mock_provider() -> MockProvider:
    """Create a mock provider for testing."""
    config = MockConfig(model="test-model")
    return MockProvider(config=config, api_key="test-key")


@pytest.fixture
async def initialized_mock_provider(
    mock_provider: MockProvider,
) -> AsyncGenerator[MockProvider, None]:
    """Create an initialized mock provider for testing."""
    await mock_provider.initialize()
    yield mock_provider
    await mock_provider.cleanup()
