"""Tests for component sharing functionality."""

import pytest
import yaml

from pepperpy.core.errors import ConfigurationError
from pepperpy.hub.sharing import ComponentRegistry


@pytest.fixture
def registry(tmp_path):
    """Create a test registry."""
    return ComponentRegistry(hub_path=tmp_path)


@pytest.fixture
def mock_config():
    """Create a mock component config."""
    return {
        "name": "test-agent",
        "version": "0.1.0",
        "description": "Test agent",
        "metadata": {
            "author": "Test Author",
            "tags": ["test", "example"],
        },
    }


def test_registry_initialization(tmp_path):
    """Test registry initialization."""
    registry = ComponentRegistry(hub_path=tmp_path)
    assert registry.hub_path == tmp_path
    assert registry.registry_path == tmp_path / "registry.json"
    assert registry._registry == {
        "agent": {},
        "workflow": {},
        "team": {},
    }


def test_register_component(registry, mock_config):
    """Test registering a component."""
    registry.register_component("agent", "test-agent", mock_config["metadata"])

    # Verify registration
    component = registry.get_component("agent", "test-agent")
    assert component["name"] == "test-agent"
    assert component["type"] == "agent"
    assert component["metadata"] == mock_config["metadata"]
    assert component["path"] == "agents/test-agent.yaml"


def test_register_invalid_component_type(registry, mock_config):
    """Test registering a component with invalid type."""
    with pytest.raises(ValueError, match="Invalid component type"):
        registry.register_component("invalid", "test", mock_config["metadata"])


def test_get_nonexistent_component(registry):
    """Test getting a component that doesn't exist."""
    with pytest.raises(ValueError, match="not found in registry"):
        registry.get_component("agent", "nonexistent")


def test_list_components(registry, mock_config):
    """Test listing components."""
    # Register test components
    registry.register_component("agent", "agent1", mock_config["metadata"])
    registry.register_component("workflow", "workflow1", mock_config["metadata"])

    # List all components
    components = registry.list_components()
    assert len(components) == 2

    # List by type
    agents = registry.list_components("agent")
    assert len(agents) == 1
    assert agents[0]["name"] == "agent1"


def test_list_components_invalid_type(registry):
    """Test listing components with invalid type."""
    with pytest.raises(ValueError, match="Invalid component type"):
        registry.list_components("invalid")


def test_publish_component(registry, tmp_path, mock_config):
    """Test publishing a component."""
    # Create test config file
    config_path = tmp_path / "agents" / "test-agent.yaml"
    config_path.parent.mkdir(parents=True)

    with open(config_path, "w") as f:
        yaml.dump(mock_config, f)

    # Publish component
    registry.publish_component("agent", "test-agent", config_path)

    # Verify registration
    component = registry.get_component("agent", "test-agent")
    assert component["name"] == "test-agent"
    assert component["metadata"]["version"] == "0.1.0"
    assert component["metadata"]["author"] == "Test Author"


def test_publish_nonexistent_config(registry, tmp_path):
    """Test publishing with nonexistent config file."""
    config_path = tmp_path / "nonexistent.yaml"
    with pytest.raises(ConfigurationError, match="Configuration not found"):
        registry.publish_component("agent", "test", config_path)


def test_publish_invalid_component_type(registry, tmp_path, mock_config):
    """Test publishing with invalid component type."""
    config_path = tmp_path / "test.yaml"
    with open(config_path, "w") as f:
        yaml.dump(mock_config, f)

    with pytest.raises(ValueError, match="Invalid component type"):
        registry.publish_component("invalid", "test", config_path)
