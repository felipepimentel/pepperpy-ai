"""Tests for the OpenRouter provider implementation."""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from pydantic import SecretStr

from pepperpy.providers.provider import ProviderConfig
from pepperpy.providers.services.openrouter import OpenRouterProvider


@pytest.fixture
def provider_config() -> ProviderConfig:
    """Create a test provider config."""
    return ProviderConfig(
        provider_type="openrouter",
        api_key=SecretStr("test-key"),
        model="anthropic/claude-3-opus-20240229",
        max_retries=3,
        timeout=30,
    )


@pytest_asyncio.fixture
async def mock_client() -> AsyncMock:
    """Create mock aiohttp client."""
    mock = AsyncMock()
    mock.post = AsyncMock()
    mock.close = AsyncMock()
    return mock


@pytest_asyncio.fixture
async def provider(
    provider_config: ProviderConfig,
    mock_client: AsyncMock,
) -> AsyncIterator[OpenRouterProvider]:
    """Create and initialize test provider."""
    with patch("aiohttp.ClientSession", return_value=mock_client):
        provider = OpenRouterProvider(provider_config)
        await provider.initialize()
        try:
            yield provider
        finally:
            await provider.cleanup()
