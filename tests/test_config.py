"""Configuration tests."""

from pepperpy.types import CapabilityConfig


def test_capability_config_defaults() -> None:
    """Test capability config defaults."""
    config = CapabilityConfig(
        name="test",
        version="1.0.0",
    )

    assert config.name == "test"
    assert config.version == "1.0.0"
    assert config.enabled is True
    assert config.metadata == {}
    assert config.settings is None
    assert config.model is None
    assert config.max_retries == 3
    assert config.retry_delay == 1.0
    assert config.timeout == 30.0
    assert config.batch_size == 32
    assert config.api_key is None
    assert config.api_base is None
    assert config.api_version is None
    assert config.organization_id is None
