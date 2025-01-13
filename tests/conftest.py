"""Test configuration."""

import pytest

from pepperpy_ai.providers.config import ProviderConfig


@pytest.fixture
def provider_config() -> ProviderConfig:
    """Create test provider configuration."""
    return {
        "model": "test-model",
        "api_key": "test-key",
        "temperature": 0.7,
        "max_tokens": 1000,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "timeout": 30.0,
    }
