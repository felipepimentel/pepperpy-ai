"""Tests for the Registry System.

This module contains tests for the Registry System, including:
- Component registration and versioning
- Metadata tracking
- Event-driven updates and notifications
"""

from unittest.mock import Mock

import pytest

from pepperpy.core.errors import NotFoundError, ValidationError
from pepperpy.core.registry import Registry
from pepperpy.core.types import ComponentConfig
from pepperpy.events import EventBus, EventType


class MockComponent:
    """Mock component for testing."""

    def __init__(self, config: ComponentConfig) -> None:
        self.config = config
        self.initialized = False

    async def initialize(self) -> None:
        self.initialized = True


@pytest.fixture
def event_bus():
    """Create a mock event bus."""
    return Mock(spec=EventBus)


@pytest.fixture
def registry(event_bus):
    """Create a registry instance."""
    return Registry[MockComponent](name="test_registry", event_bus=event_bus)


@pytest.fixture
def component_config():
    """Create a test component configuration."""
    return ComponentConfig(
        type="mock_component",
        name="test_component",
        version="1.0.0",
        settings={"key": "value"},
        metadata={"test": True},
    )


async def test_registry_initialization(registry):
    """Test registry initialization."""
    assert registry._components == {}
    assert registry._event_bus is not None


async def test_component_registration(registry, component_config, event_bus):
    """Test component registration."""
    # Create component
    component = MockComponent(component_config)

    # Register component
    await registry.register(component)

    # Verify component is registered
    assert component.config.name in registry._components
    assert (
        registry._components[component.config.name][component.config.version]
        == component
    )

    # Verify event was emitted
    event_bus.emit.assert_called_once()
    event = event_bus.emit.call_args[0][0]
    assert event.type == EventType.PROVIDER_REGISTERED


async def test_component_registration_validation(registry, component_config):
    """Test component registration validation."""
    # Test invalid version format
    invalid_config = component_config.copy()
    invalid_config.version = "invalid"
    component = MockComponent(invalid_config)

    with pytest.raises(ValidationError):
        await registry.register(component)


async def test_component_versioning(registry, component_config):
    """Test component versioning."""
    # Register v1.0.0
    component_v1 = MockComponent(component_config)
    await registry.register(component_v1)

    # Register v2.0.0
    config_v2 = component_config.copy()
    config_v2.version = "2.0.0"
    component_v2 = MockComponent(config_v2)
    await registry.register(component_v2)

    # Get all versions
    versions = registry.list_items()[component_config.name]
    assert len(versions) == 2
    assert "1.0.0" in versions
    assert "2.0.0" in versions


async def test_component_retrieval(registry, component_config):
    """Test component retrieval."""
    # Register component
    component = MockComponent(component_config)
    await registry.register(component)

    # Get component by name and version
    retrieved = await registry.get(component.config.name, component.config.version)
    assert retrieved == component

    # Get latest version
    latest = await registry.get(component.config.name)
    assert latest == component


async def test_component_not_found(registry):
    """Test component not found error."""
    with pytest.raises(NotFoundError):
        await registry.get("nonexistent")


async def test_component_metadata(registry, component_config):
    """Test component metadata tracking."""
    # Register component with metadata
    component = MockComponent(component_config)
    await registry.register(component)

    # Get component metadata
    metadata = registry.get_metadata(component.config.name, component.config.version)
    assert metadata == component.config.metadata


async def test_component_deregistration(registry, component_config, event_bus):
    """Test component deregistration."""
    # Register component
    component = MockComponent(component_config)
    await registry.register(component)

    # Deregister component
    await registry.deregister(component.config.name, component.config.version)

    # Verify component is removed
    with pytest.raises(NotFoundError):
        await registry.get(component.config.name, component.config.version)

    # Verify event was emitted
    assert event_bus.emit.call_count == 2  # One for register, one for deregister
    deregister_event = event_bus.emit.call_args[0][0]
    assert deregister_event.type == EventType.PROVIDER_UNREGISTERED
