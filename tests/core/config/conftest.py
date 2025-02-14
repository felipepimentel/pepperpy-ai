"""Test fixtures for configuration management tests."""

import os
from pathlib import Path
from typing import AsyncGenerator, Dict, Optional

import pytest
from pydantic import BaseModel

from pepperpy.core.config import (
    ConfigurationManager,
    ConfigWatcher,
    EnvSource,
    JSONSource,
    YAMLSource,
)


class TestConfig(BaseModel):
    """Test configuration model."""

    name: str = "test"
    value: int = 42
    nested: Dict[str, str] = {}
    optional: Optional[str] = None


class MockConfigWatcher(ConfigWatcher):
    """Mock configuration watcher for testing."""

    def __init__(self) -> None:
        self.called = False
        self.old_config = None
        self.new_config = None

    async def on_config_change(
        self, old_config: BaseModel, new_config: BaseModel
    ) -> None:
        self.called = True
        self.old_config = old_config
        self.new_config = new_config


@pytest.fixture
def test_config_class() -> type[TestConfig]:
    """Provide test configuration class."""
    return TestConfig


@pytest.fixture
async def config_manager(
    test_config_class: type[TestConfig],
) -> AsyncGenerator[ConfigurationManager[TestConfig], None]:
    """Provide configuration manager instance."""
    manager = ConfigurationManager(test_config_class)
    yield manager
    await manager.cleanup()


@pytest.fixture
def mock_watcher() -> MockConfigWatcher:
    """Provide mock configuration watcher."""
    return MockConfigWatcher()


@pytest.fixture
def env_source() -> EnvSource:
    """Provide environment variable configuration source."""
    return EnvSource(prefix="TEST_")


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Provide temporary directory for configuration files."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def json_config_file(temp_config_dir: Path) -> Path:
    """Provide temporary JSON configuration file."""
    config_file = temp_config_dir / "config.json"
    config_file.write_text('{"name": "json_test", "value": 100}')
    return config_file


@pytest.fixture
def yaml_config_file(temp_config_dir: Path) -> Path:
    """Provide temporary YAML configuration file."""
    config_file = temp_config_dir / "config.yaml"
    config_file.write_text("name: yaml_test\nvalue: 200")
    return config_file


@pytest.fixture
def json_source(json_config_file: Path) -> JSONSource:
    """Provide JSON configuration source."""
    return JSONSource(json_config_file)


@pytest.fixture
def yaml_source(yaml_config_file: Path) -> YAMLSource:
    """Provide YAML configuration source."""
    return YAMLSource(yaml_config_file)


@pytest.fixture(autouse=True)
def clean_env() -> None:
    """Clean environment variables before each test."""
    # Store original environment
    original_env = dict(os.environ)

    # Clean test variables
    for key in list(os.environ.keys()):
        if key.startswith("TEST_"):
            del os.environ[key]

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
