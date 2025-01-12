"""Test configuration functionality."""

import pytest

from pepperpy_ai.capabilities.base import CapabilityConfig


@pytest.fixture
def test_config() -> CapabilityConfig:
    """Create test configuration."""
    return CapabilityConfig(
        name="test",
        version="1.0.0",
        enabled=True,
        model_name="test-model",
        device="cpu",
        normalize_embeddings=True,
        batch_size=32,
    )


def test_capability_config_defaults() -> None:
    """Test capability configuration defaults."""
    config = CapabilityConfig()
    assert config.name == "capability"
    assert config.version == "1.0.0"
    assert config.enabled is True
    assert config.model_name == "default"
    assert config.device == "cpu"
    assert config.normalize_embeddings is True
    assert config.batch_size == 32
    assert config.metadata == {}
    assert config.settings == {}
