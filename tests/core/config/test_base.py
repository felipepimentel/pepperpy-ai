"""Tests for base configuration module."""

from typing import Any, Dict, Optional

import pytest
from pydantic import BaseModel, Field

from pepperpy.core.config.base import (
    ConfigManager,
    ConfigProvider,
    ConfigValidator,
    DictConfigProvider,
)


class TestConfig(BaseModel):
    """Test configuration model."""

    name: str = Field(..., description="Name of the configuration")
    value: int = Field(..., description="Value of the configuration")
    optional: Optional[str] = Field(None, description="Optional value")


def test_dict_config_provider():
    """Test dictionary configuration provider."""
    provider = DictConfigProvider()

    # Test set and get
    provider.set("test.key", "value")
    assert provider.get("test.key") == "value"

    # Test exists
    assert provider.exists("test.key")
    assert not provider.exists("nonexistent.key")

    # Test delete
    provider.delete("test.key")
    assert not provider.exists("test.key")
    assert provider.get("test.key") is None

    # Test clear
    provider.set("test.key1", "value1")
    provider.set("test.key2", "value2")
    provider.clear()
    assert not provider.exists("test.key1")
    assert not provider.exists("test.key2")


def test_config_validator():
    """Test configuration validator."""
    validator = ConfigValidator(TestConfig)

    # Test valid configuration
    config: Dict[str, Any] = {"name": "test", "value": 42}
    errors = validator.validate(config)
    assert not errors

    # Test invalid configuration
    config = {"name": "test"}  # Missing required field
    errors = validator.validate(config)
    assert len(errors) == 1
    assert errors[0].field == "value"
    assert "field required" in errors[0].message.lower()

    # Test invalid type
    config = {"name": "test", "value": "not_an_integer"}
    errors = validator.validate(config)
    assert len(errors) == 1
    assert errors[0].field == "value"
    assert "integer" in errors[0].message.lower()

    # Test optional field
    config = {"name": "test", "value": 42, "optional": "test"}
    errors = validator.validate(config)
    assert not errors


def test_config_manager():
    """Test configuration manager."""
    provider = DictConfigProvider()
    manager = ConfigManager(provider)
    validator = ConfigValidator(TestConfig)

    # Register validator
    manager.register_validator("test", validator)

    # Test valid configuration
    manager.set("test.name", "test")
    manager.set("test.value", 42)
    errors = manager.validate()
    assert not errors

    # Test invalid configuration
    manager.delete("test.value")
    errors = manager.validate()
    assert len(errors) == 1
    assert errors[0].field == "value"
    assert "field required" in errors[0].message.lower()

    # Test unregister validator
    manager.unregister_validator("test")
    errors = manager.validate()
    assert not errors

    # Test get configuration by prefix
    manager.set("test.name", "test")
    manager.set("test.value", 42)
    manager.set("other.key", "value")
    config = manager._get_config_by_prefix("test")
    assert len(config) == 2
    assert config["test.name"] == "test"
    assert config["test.value"] == 42


def test_custom_config_provider():
    """Test custom configuration provider."""

    class CustomProvider(ConfigProvider):
        """Custom configuration provider for testing."""

        def __init__(self) -> None:
            """Initialize provider."""
            self._config: Dict[str, Any] = {}

        def get(self, key: str) -> Optional[Any]:
            """Get configuration value."""
            return self._config.get(key)

        def set(self, key: str, value: Any) -> None:
            """Set configuration value."""
            self._config[key] = value

        def delete(self, key: str) -> None:
            """Delete configuration value."""
            self._config.pop(key, None)

        def exists(self, key: str) -> bool:
            """Check if key exists."""
            return key in self._config

        def clear(self) -> None:
            """Clear all values."""
            self._config.clear()

    provider = CustomProvider()
    manager = ConfigManager(provider)

    # Test provider operations
    manager.set("test.key", "value")
    assert manager.get("test.key") == "value"
    assert manager.exists("test.key")
    manager.delete("test.key")
    assert not manager.exists("test.key")


if __name__ == "__main__":
    pytest.main([__file__])
