"""Tests for Hub-based resource management."""

from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

from pepperpy.core.errors import HubError, NotFoundError
from pepperpy.hub.resource_manager import ResourceManager, get_resource_manager


@pytest.fixture
def hub_path(tmp_path: Path) -> Path:
    """Create temporary Hub directory."""
    return tmp_path / ".pepper_hub"


@pytest.fixture
def resource_manager(hub_path: Path) -> ResourceManager:
    """Create resource manager with temporary Hub."""
    hub_path.mkdir(parents=True)
    return ResourceManager(str(hub_path))


@pytest.fixture
def memory_config() -> Dict[str, Any]:
    """Sample memory configuration."""
    return {
        "name": "memory_resources",
        "version": "v1.0.0",
        "type": "resource_config",
        "config": {
            "auto_cleanup": True,
            "cleanup_interval": 3600,
            "max_entries": 10000,
            "default_expiration": 86400,
        },
    }


def test_resource_manager_init(hub_path: Path):
    """Test resource manager initialization."""
    # Test with existing Hub
    hub_path.mkdir(parents=True)
    manager = ResourceManager(str(hub_path))
    assert manager.hub_path == hub_path.resolve()

    # Test with non-existent Hub
    with pytest.raises(HubError):
        ResourceManager("/nonexistent/path")


def test_load_config(
    resource_manager: ResourceManager,
    hub_path: Path,
    memory_config: Dict[str, Any],
):
    """Test loading resource configuration."""
    # Create config file
    config_path = hub_path / "resources" / "memory" / "memory_resources" / "v1.0.0.yaml"
    config_path.parent.mkdir(parents=True)
    with config_path.open("w") as f:
        yaml.safe_dump(memory_config, f)

    # Load config
    config = resource_manager.load_config(
        "memory",
        "memory_resources",
        version="v1.0.0",
    )
    assert config == memory_config

    # Test non-existent config
    with pytest.raises(NotFoundError):
        resource_manager.load_config(
            "memory",
            "nonexistent",
            version="v1.0.0",
        )


def test_save_config(
    resource_manager: ResourceManager,
    hub_path: Path,
    memory_config: Dict[str, Any],
):
    """Test saving resource configuration."""
    # Save config
    resource_manager.save_config(
        "memory",
        "memory_resources",
        memory_config,
        version="v1.0.0",
    )

    # Verify file was created
    config_path = hub_path / "resources" / "memory" / "memory_resources" / "v1.0.0.yaml"
    assert config_path.exists()

    # Verify content
    with config_path.open("r") as f:
        saved_config = yaml.safe_load(f)
    assert saved_config == memory_config


def test_list_resources(
    resource_manager: ResourceManager,
    hub_path: Path,
    memory_config: Dict[str, Any],
):
    """Test listing available resources."""
    # Create multiple configs
    configs = {
        "memory/config1": {**memory_config, "name": "config1"},
        "memory/config2": {**memory_config, "name": "config2"},
        "agent/config3": {**memory_config, "name": "config3"},
    }

    for path, config in configs.items():
        type_name, name = path.split("/")
        resource_manager.save_config(type_name, name, config)

    # List all resources
    resources = resource_manager.list_resources()
    assert len(resources) == 3
    assert all(path in resources for path in configs)

    # List by type
    memory_resources = resource_manager.list_resources("memory")
    assert len(memory_resources) == 2
    assert all(
        path in memory_resources for path in configs if path.startswith("memory")
    )


def test_get_resource_manager(hub_path: Path):
    """Test global resource manager instance."""
    # Create Hub directory
    hub_path.mkdir(parents=True)

    # Get manager
    manager1 = get_resource_manager(str(hub_path))
    assert manager1 is not None

    # Get same instance
    manager2 = get_resource_manager(str(hub_path))
    assert manager2 is manager1
