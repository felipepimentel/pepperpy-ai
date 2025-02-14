"""Tests for configuration management."""

import os
from typing import Dict

import pytest

from pepperpy.core.config import (
    ConfigSource,
    ConfigurationError,
    ConfigurationManager,
)
from pepperpy.core.config.types import ConfigValidationError

from .conftest import MockConfigWatcher, TestConfig


@pytest.mark.asyncio
async def test_config_manager_basic(
    config_manager: ConfigurationManager[TestConfig],
) -> None:
    """Test basic configuration manager functionality."""
    # Initial state
    assert config_manager.config is None

    # Initialize with no sources
    await config_manager.initialize()
    assert isinstance(config_manager.config, TestConfig)
    assert config_manager.config is not None  # For type checker
    assert config_manager.config.name == "test"  # Default value


@pytest.mark.asyncio
async def test_config_manager_env_source(
    config_manager: ConfigurationManager[TestConfig],
    env_source: ConfigSource,
) -> None:
    """Test configuration from environment variables."""
    os.environ["TEST_NAME"] = "env_test"
    os.environ["TEST_VALUE"] = "123"

    config_manager.add_source(env_source)
    await config_manager.initialize()

    assert config_manager.config is not None  # For type checker
    assert config_manager.config.name == "env_test"
    assert config_manager.config.value == 123


@pytest.mark.asyncio
async def test_config_manager_json_source(
    config_manager: ConfigurationManager[TestConfig],
    json_source: ConfigSource,
) -> None:
    """Test configuration from JSON file."""
    config_manager.add_source(json_source)
    await config_manager.initialize()

    assert config_manager.config is not None  # For type checker
    assert config_manager.config.name == "json_test"
    assert config_manager.config.value == 100


@pytest.mark.asyncio
async def test_config_manager_yaml_source(
    config_manager: ConfigurationManager[TestConfig],
    yaml_source: ConfigSource,
) -> None:
    """Test configuration from YAML file."""
    config_manager.add_source(yaml_source)
    await config_manager.initialize()

    assert config_manager.config is not None  # For type checker
    assert config_manager.config.name == "yaml_test"
    assert config_manager.config.value == 200


@pytest.mark.asyncio
async def test_config_manager_multiple_sources(
    config_manager: ConfigurationManager[TestConfig],
    env_source: ConfigSource,
    json_source: ConfigSource,
    yaml_source: ConfigSource,
) -> None:
    """Test configuration from multiple sources."""
    os.environ["TEST_NAME"] = "env_test"

    # Add sources in order (later sources override earlier ones)
    config_manager.add_source(json_source)  # value=100
    config_manager.add_source(yaml_source)  # value=200
    config_manager.add_source(env_source)  # name=env_test

    await config_manager.initialize()

    assert config_manager.config is not None  # For type checker
    # env_source overrides name, yaml_source overrides value
    assert config_manager.config.name == "env_test"
    assert config_manager.config.value == 200


@pytest.mark.asyncio
async def test_config_manager_validation(
    config_manager: ConfigurationManager[TestConfig],
) -> None:
    """Test configuration validation."""

    class InvalidSource(ConfigSource):
        async def load(self) -> Dict[str, str]:
            return {"value": "invalid"}  # Should be int

    config_manager.add_source(InvalidSource())

    with pytest.raises(ConfigValidationError):
        await config_manager.initialize()


@pytest.mark.asyncio
async def test_config_manager_watcher(
    config_manager: ConfigurationManager[TestConfig],
    mock_watcher: MockConfigWatcher,
    env_source: ConfigSource,
) -> None:
    """Test configuration change notifications."""
    config_manager.add_source(env_source)
    config_manager.add_watcher(mock_watcher)

    # Initial load
    await config_manager.initialize()
    assert not mock_watcher.called

    # Change configuration
    os.environ["TEST_NAME"] = "changed"
    await config_manager.reload()

    assert mock_watcher.called
    assert isinstance(mock_watcher.old_config, TestConfig)
    assert isinstance(mock_watcher.new_config, TestConfig)
    assert mock_watcher.old_config.name == "test"
    assert mock_watcher.new_config.name == "changed"


@pytest.mark.asyncio
async def test_config_manager_source_error(
    config_manager: ConfigurationManager[TestConfig],
) -> None:
    """Test configuration source error handling."""

    class ErrorSource(ConfigSource):
        async def load(self) -> Dict[str, str]:
            raise RuntimeError("Test error")

    config_manager.add_source(ErrorSource())

    with pytest.raises(ConfigurationError):
        await config_manager.initialize()


@pytest.mark.asyncio
async def test_config_manager_cleanup(
    config_manager: ConfigurationManager[TestConfig],
    env_source: ConfigSource,
    mock_watcher: MockConfigWatcher,
) -> None:
    """Test configuration manager cleanup."""
    config_manager.add_source(env_source)
    config_manager.add_watcher(mock_watcher)

    await config_manager.initialize()
    assert config_manager.config is not None

    await config_manager.cleanup()
    assert config_manager.config is None
