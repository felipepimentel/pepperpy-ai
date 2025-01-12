"""Common test fixtures and utilities."""

from typing import AsyncGenerator, Generator

import pytest
from pytest_mock import MockerFixture

from pepperpy_ai.providers.mock import MockProvider
from pepperpy_ai.providers.config import ProviderConfig


@pytest.fixture
def mock_provider() -> Generator[MockProvider, None, None]:
    """Create a mock provider for testing."""
    config = ProviderConfig(
        api_key="mock-key",
        model="mock-model",
        provider="mock",
        temperature=0.7,
        max_tokens=100,
    )
    provider = MockProvider(config, api_key="mock-key")
    yield provider


@pytest.fixture
async def initialized_mock_provider(mock_provider: MockProvider) -> AsyncGenerator[MockProvider, None]:
    """Create an initialized mock provider for testing."""
    await mock_provider.initialize()
    yield mock_provider
    await mock_provider.cleanup()


@pytest.fixture
def mock_provider_factory(mocker: MockerFixture) -> Generator[MockProvider, None, None]:
    """Create a mock provider factory for testing."""
    config = ProviderConfig(
        api_key="mock-key",
        model="mock-model",
        provider="mock",
        temperature=0.7,
        max_tokens=100,
    )
    provider = MockProvider(config, api_key="mock-key")
    mocker.patch("pepperpy_ai.providers.factory.create_provider", return_value=provider)
    yield provider
