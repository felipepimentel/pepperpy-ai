"""Tests for the unified configuration system."""

from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, Field

from pepperpy.core.config.unified import (
    ConfigSource,
    ConfigState,
    ConfigurationError,
    UnifiedConfig,
)


class TestConfig(BaseModel):
    """Test configuration model."""

    name: str = Field(default="test")
    debug: bool = Field(default=False)
    timeout: float = Field(default=30.0)
    retries: int = Field(default=3)
    api_key: str = Field(default="", json_schema_extra={"sensitive": True})
    nested: dict[str, Any] = Field(default_factory=dict)


class ChildConfig(TestConfig):
    """Child configuration model for testing inheritance."""

    child_specific: str = Field(default="child")


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    """Create a temporary configuration file."""
    config = {
        "name": "from_file",
        "debug": True,
        "nested": {"key": "value"},
        "api_key": "test_key",
    }

    import yaml

    config_path = tmp_path / "config.yml"
    with config_path.open("w") as f:
        yaml.dump(config, f)

    return config_path


@pytest.fixture
def env_vars() -> dict[str, str]:
    """Environment variables for testing."""
    return {
        "PEPPERPY_NAME": "from_env",
        "PEPPERPY_DEBUG": "true",
        "PEPPERPY_TIMEOUT": "60.5",
        "PEPPERPY_RETRIES": "5",
        "PEPPERPY_NESTED__KEY": "env_value",
        "PEPPERPY_API_KEY": "env_key",
    }


@pytest.fixture
def parent_config() -> UnifiedConfig[TestConfig]:
    """Create a parent configuration instance."""
    return UnifiedConfig(TestConfig, version=(1, 0, 0))


@pytest.fixture
def config_manager(parent_config: UnifiedConfig[TestConfig]) -> UnifiedConfig[ChildConfig]:
    """Create a configuration manager instance."""
    return UnifiedConfig(
        ChildConfig,
        parent=parent_config,
        version=(1, 0, 0),
        encrypt_sensitive=True,
    )


@pytest.mark.asyncio
async def test_config_initialization(
    config_manager: UnifiedConfig[ChildConfig],
    config_file: Path,
    env_vars: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
):
    """Test configuration initialization from multiple sources."""
    # Set environment variables
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    # Override default paths
    monkeypatch.setattr(
        "pepperpy.core.config.unified.DEFAULT_CONFIG_PATHS",
        [config_file],
    )

    # Initialize configuration
    await config_manager.initialize()

    assert config_manager.state == ConfigState.READY
    assert ConfigSource.ENV in config_manager.sources
    assert ConfigSource.FILE in config_manager.sources

    # Environment variables should override file values
    config = config_manager.config
    assert config is not None
    assert config.name == "from_env"
    assert config.debug is True
    assert config.timeout == 60.5
    assert config.retries == 5
    assert config.nested["key"] == "env_value"
    # API key should be encrypted
    assert config.api_key != "env_key"


@pytest.mark.asyncio
async def test_config_inheritance(
    parent_config: UnifiedConfig[TestConfig],
    config_manager: UnifiedConfig[ChildConfig],
):
    """Test configuration inheritance."""
    # Initialize parent first
    await parent_config.initialize()
    assert parent_config.state == ConfigState.READY

    # Initialize child
    await config_manager.initialize()
    assert config_manager.state == ConfigState.READY
    assert ConfigSource.PARENT in config_manager.sources

    config = config_manager.config
    assert config is not None
    assert config.child_specific == "child"  # Child-specific field
    assert config.name == "test"  # Inherited field


@pytest.mark.asyncio
async def test_config_validation(config_manager: UnifiedConfig[ChildConfig]):
    """Test configuration validation."""
    def validate_timeout(config: ChildConfig) -> list[str]:
        if config.timeout <= 0:
            return ["Timeout must be positive"]
        return []

    config_manager.add_validation_rule(validate_timeout)
    await config_manager.initialize()

    # Test valid configuration
    assert await config_manager.validate() == []

    # Test invalid configuration
    await config_manager.update({"timeout": -1})
    errors = await config_manager.validate()
    assert len(errors) == 1
    assert "Timeout must be positive" in errors[0]


@pytest.mark.asyncio
async def test_config_version_compatibility(
    parent_config: UnifiedConfig[TestConfig],
):
    """Test configuration version compatibility."""
    # Create child with incompatible version
    child_config = UnifiedConfig(
        ChildConfig,
        parent=parent_config,
        version=(2, 0, 0),  # Major version bump
    )

    await parent_config.initialize()
    
    # Should raise error due to version incompatibility
    with pytest.raises(ConfigurationError) as exc:
        await child_config.initialize()
    assert "Incompatible configuration version" in str(exc.value)


@pytest.mark.asyncio
async def test_sensitive_field_encryption(
    config_manager: UnifiedConfig[ChildConfig],
    env_vars: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
):
    """Test encryption of sensitive configuration fields."""
    # Set API key through environment
    monkeypatch.setenv("PEPPERPY_API_KEY", "secret_key")

    await config_manager.initialize()
    config = config_manager.config
    assert config is not None

    # API key should be encrypted
    assert config.api_key != "secret_key"
    assert len(config.api_key) > 0  # Should contain encrypted value

    # Update with new API key
    await config_manager.update({"api_key": "new_secret"})
    assert config.api_key != "new_secret"
    assert len(config.api_key) > 0
