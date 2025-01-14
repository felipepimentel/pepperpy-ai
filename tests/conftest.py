"""Test configuration."""

import pytest

from pepperpy.providers.config import ProviderConfig


@pytest.fixture
def provider_config() -> ProviderConfig:
    """Create test provider configuration."""
    return {
        "name": "test-provider",
        "version": "1.0.0",
        "api_base": "https://api.test.com",
        "model": "test-model",
        "api_key": "test-key",
        "temperature": 0.7,
        "max_tokens": 1000,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "timeout": 30.0,
    }
