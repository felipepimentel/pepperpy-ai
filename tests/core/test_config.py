"""Tests for the configuration management system."""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from pepperpy.core.config import (
    ConfigManager,
    PepperpyConfig,
    load_config,
    save_config,
)


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    """Create a temporary config file."""
    config_data = {
        "provider_type": "test-provider",
        "provider_config": {
            "api_key": "test-key",
            "model": "test-model",
            "max_retries": 3,
            "timeout": 30,
        },
        "memory_config": {
            "type": "inmemory",
            "cache_ttl": 3600,
        },
        "prompt_config": {
            "type": "jinja2",
            "templates_dir": "templates",
        },
        "timeout": 30.0,
        "max_retries": 3,
        "retry_delay": 1.0,
    }
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)
    return config_path


@pytest.fixture
def config_manager(tmp_path: Path) -> ConfigManager:
    """Create a test config manager."""
    return ConfigManager()


def test_load_config_from_file(config_file: Path):
    """Test loading configuration from file."""
    config = load_config(config_file)
    assert isinstance(config, PepperpyConfig)
    assert config.provider_type == "test-provider"
    assert config.provider_config["api_key"] == "test-key"
    assert config.memory_config["type"] == "inmemory"
    assert config.prompt_config["type"] == "jinja2"
    assert config.timeout == 30.0


def test_load_config_from_env():
    """Test loading configuration from environment variables."""
    env_vars = {
        "PEPPERPY_PROVIDER_TYPE": "env-provider",
        "PEPPERPY_PROVIDER_CONFIG__API_KEY": "env-key",
        "PEPPERPY_PROVIDER_CONFIG__MODEL": "env-model",
        "PEPPERPY_TIMEOUT": "45.0",
    }
    with pytest.MonkeyPatch().context() as mp:
        for key, value in env_vars.items():
            mp.setenv(key, value)
        config = load_config()
        assert config.provider_type == "env-provider"
        assert config.provider_config["api_key"] == "env-key"
        assert config.provider_config["model"] == "env-model"
        assert config.timeout == 45.0


def test_load_config_env_overrides_file(config_file: Path):
    """Test that environment variables override file configuration."""
    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("PEPPERPY_PROVIDER_TYPE", "override-provider")
        config = load_config(config_file)
        assert config.provider_type == "override-provider"
        assert config.provider_config["api_key"] == "test-key"  # From file


def test_save_config(tmp_path: Path):
    """Test saving configuration to file."""
    config = PepperpyConfig(
        provider_type="save-test",
        provider_config={
            "api_key": "save-key",
            "model": "save-model",
            "max_retries": 2,
            "timeout": 15,
        },
        memory_config={
            "type": "redis",
            "cache_ttl": 1800,
        },
        prompt_config={
            "type": "jinja2",
            "templates_dir": "custom_templates",
        },
        timeout=15.0,
        max_retries=2,
        retry_delay=0.5,
    )
    save_path = tmp_path / "saved_config.yaml"
    save_config(config, save_path)

    # Verify saved config
    loaded_config = load_config(save_path)
    assert loaded_config.provider_type == "save-test"
    assert loaded_config.provider_config["api_key"] == "save-key"
    assert loaded_config.memory_config["type"] == "redis"
    assert loaded_config.timeout == 15.0


def test_config_validation():
    """Test configuration validation."""
    with pytest.raises(ValidationError):
        PepperpyConfig(
            provider_type="test",
            timeout=-1.0,  # Invalid timeout < 0
        )

    with pytest.raises(ValidationError):
        PepperpyConfig(
            provider_type="test",
            max_retries=-1,  # Invalid max_retries < 0
        )


def test_config_manager_defaults(config_manager: ConfigManager):
    """Test config manager default values."""
    assert config_manager._config is None


def test_config_manager_load_save(config_manager: ConfigManager, config_file: Path):
    """Test config manager load and save operations."""
    # Load config
    config = config_manager.load(config_file)
    assert config.provider_type == "test-provider"

    # Modify and save
    config.provider_type = "modified-provider"
    save_path = Path(config_file.parent) / "modified_config.yaml"
    config_manager.save(save_path)

    # Verify saved config
    loaded_config = config_manager.load(save_path)
    assert loaded_config.provider_type == "modified-provider"
