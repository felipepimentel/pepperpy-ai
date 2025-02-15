"""Tests for the unified configuration system."""

from pathlib import Path
from typing import Any, Dict

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
    nested: Dict[str, Any] = Field(default_factory=dict)


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    """Create a temporary configuration file."""
    config = {"name": "from_file", "debug": True, "nested": {"key": "value"}}

    import yaml

    config_path = tmp_path / "config.yml"
    with config_path.open("w") as f:
        yaml.dump(config, f)

    return config_path


@pytest.fixture
def env_vars() -> Dict[str, str]:
    """Environment variables for testing."""
    return {
        "PEPPERPY_NAME": "from_env",
        "PEPPERPY_DEBUG": "true",
        "PEPPERPY_TIMEOUT": "60.5",
        "PEPPERPY_RETRIES": "5",
        "PEPPERPY_NESTED__KEY": "env_value",
    }


@pytest.fixture
def config_manager() -> UnifiedConfig[TestConfig]:
    """Create a configuration manager instance."""
    return UnifiedConfig(TestConfig)


@pytest.mark.asyncio
async def test_config_initialization(
    config_manager: UnifiedConfig[TestConfig],
    config_file: Path,
    env_vars: Dict[str, str],
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


@pytest.mark.asyncio
async def test_config_update(config_manager: UnifiedConfig[TestConfig]):
    """Test configuration updates."""
    # Initialize with defaults
    await config_manager.initialize()

    # Update configuration
    updates = {"name": "updated", "debug": True, "nested": {"new": "value"}}
    await config_manager.update(updates)

    assert config_manager.state == ConfigState.READY
    config = config_manager.config
    assert config is not None
    assert config.name == "updated"
    assert config.debug is True
    assert config.nested["new"] == "value"


@pytest.mark.asyncio
async def test_config_hooks(config_manager: UnifiedConfig[TestConfig]):
    """Test configuration lifecycle hooks."""
    load_called = False
    update_called = False
    error_called = False

    def on_load(config: TestConfig) -> None:
        nonlocal load_called
        load_called = True
        assert config.name == "test"

    def on_update(config: TestConfig) -> None:
        nonlocal update_called
        update_called = True
        assert config.name == "updated"

    def on_error(config: TestConfig) -> None:
        nonlocal error_called
        error_called = True

    # Add hooks
    config_manager.add_hook("on_load", on_load)
    config_manager.add_hook("on_update", on_update)
    config_manager.add_hook("on_error", on_error)

    # Initialize and update
    await config_manager.initialize()
    await config_manager.update({"name": "updated"})

    assert load_called
    assert update_called
    assert not error_called


@pytest.mark.asyncio
async def test_config_validation(config_manager: UnifiedConfig[TestConfig]):
    """Test configuration validation."""
    # Try to update with invalid values
    with pytest.raises(ConfigurationError):
        await config_manager.update({"timeout": "invalid"})

    # State should be ERROR
    assert config_manager.state == ConfigState.ERROR


@pytest.mark.asyncio
async def test_config_cleanup(config_manager: UnifiedConfig[TestConfig]):
    """Test configuration cleanup."""
    # Initialize and add hooks
    await config_manager.initialize()
    config_manager.add_hook("on_load", lambda _: None)

    # Cleanup
    await config_manager.cleanup()

    assert config_manager.state == ConfigState.UNINITIALIZED
    assert config_manager.config is None
    assert not config_manager.sources
    assert not config_manager._hooks["on_load"]


@pytest.mark.asyncio
async def test_hook_source_filtering(
    config_manager: UnifiedConfig[TestConfig],
    env_vars: Dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
):
    """Test hook filtering by source."""
    env_hook_called = False
    any_hook_called = False

    def env_hook(config: TestConfig) -> None:
        nonlocal env_hook_called
        env_hook_called = True

    def any_hook(config: TestConfig) -> None:
        nonlocal any_hook_called
        any_hook_called = True

    # Add hooks
    config_manager.add_hook("on_load", env_hook, source=ConfigSource.ENV)
    config_manager.add_hook("on_load", any_hook)

    # Set environment variables
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    # Initialize
    await config_manager.initialize()

    assert env_hook_called
    assert any_hook_called


@pytest.mark.asyncio
async def test_hook_removal(config_manager: UnifiedConfig[TestConfig]):
    """Test hook removal."""
    hook_called = False

    def test_hook(config: TestConfig) -> None:
        nonlocal hook_called
        hook_called = True

    # Add and remove hook
    config_manager.add_hook("on_load", test_hook)
    config_manager.remove_hook("on_load", test_hook)

    # Initialize
    await config_manager.initialize()

    assert not hook_called


@pytest.mark.asyncio
async def test_invalid_hook_event(config_manager: UnifiedConfig[TestConfig]):
    """Test adding/removing hooks with invalid events."""
    with pytest.raises(ValueError, match="Invalid hook event"):
        config_manager.add_hook("invalid", lambda _: None)

    with pytest.raises(ValueError, match="Invalid hook event"):
        config_manager.remove_hook("invalid", lambda _: None)
