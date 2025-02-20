"""Tests for the Factory System.

This module contains tests for the Factory System, including:
- ComponentFactory functionality
- Factory hooks and lifecycle management
- Component registration and creation
"""

from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, Mock

import pytest

from pepperpy.core.errors import FactoryError, ValidationError
from pepperpy.core.factory import ComponentFactory, Factory
from pepperpy.core.types import ComponentConfig
from pepperpy.events import Event, EventBus, EventType


class MockComponent:
    """Mock component for testing."""

    def __init__(self, config: ComponentConfig) -> None:
        self.config = config
        self.initialized = False
        self.cleaned_up = False

    async def initialize(self) -> None:
        self.initialized = True

    async def cleanup(self) -> None:
        self.cleaned_up = True


class MockFactory(Factory[MockComponent]):
    """Mock implementation of Factory."""

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        """Initialize mock factory."""
        super().__init__(event_bus)
        self._components: Dict[str, MockComponent] = {}

    async def create(self, config: Dict[str, Any]) -> MockComponent:
        """Create a mock component."""
        component = MockComponent(**config)
        self._components[config.get("name", "default")] = component
        return component

    async def cleanup(self) -> None:
        """Clean up factory resources."""
        self._components.clear()


@pytest.fixture
def event_bus():
    """Create a mock event bus."""
    return Mock(spec=EventBus)


@pytest.fixture
def mock_factory(event_bus):
    """Create a mock factory instance."""
    return MockFactory(event_bus)


@pytest.fixture
def component_factory(event_bus):
    """Create a component factory instance."""
    return ComponentFactory(event_bus)


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


@pytest.mark.asyncio
async def test_factory_creation(mock_factory: MockFactory):
    """Test basic factory creation."""
    config = {"name": "test", "value": 42}
    component = await mock_factory.create(config)
    assert component.config == config


@pytest.mark.asyncio
async def test_factory_hooks(mock_factory: MockFactory):
    """Test factory hooks."""
    hook_calls = []

    def test_hook(component: MockComponent) -> None:
        hook_calls.append(component)

    mock_factory.add_hook("component_created", test_hook)
    config = {"name": "test"}
    component = await mock_factory.create(config)

    assert len(hook_calls) == 1
    assert hook_calls[0] == component

    # Test hook removal
    mock_factory.remove_hook("component_created", test_hook)
    await mock_factory.create({"name": "another"})
    assert len(hook_calls) == 1


@pytest.mark.asyncio
async def test_factory_events(mock_factory: MockFactory, event_bus: AsyncMock):
    """Test factory events."""
    config = {"name": "test"}
    await mock_factory.create(config)

    event_bus.publish.assert_called_once()
    event = event_bus.publish.call_args[0][0]
    assert isinstance(event, Event)
    assert event.type == EventType.COMPONENT_CREATED


@pytest.mark.asyncio
async def test_factory_cleanup(mock_factory: MockFactory):
    """Test factory cleanup."""
    config = {"name": "test"}
    await mock_factory.create(config)
    await mock_factory.cleanup()
    assert not mock_factory._components


@pytest.mark.asyncio
async def test_component_factory_registration(component_factory: ComponentFactory):
    """Test component type registration."""
    component_factory.register("test_type", MockComponent)
    config = {"type": "test_type", "name": "test"}
    component = await component_factory.create(config)
    assert isinstance(component, MockComponent)
    assert component.config == config


@pytest.mark.asyncio
async def test_component_factory_validation(component_factory: ComponentFactory):
    """Test component factory validation."""
    # Test missing type
    with pytest.raises(ValidationError, match="Missing required field: type"):
        await component_factory.create({"name": "test"})

    # Test unknown type
    with pytest.raises(ValidationError, match="Component type not found"):
        await component_factory.create({"type": "unknown", "name": "test"})

    # Test duplicate registration
    component_factory.register("test_type", MockComponent)
    with pytest.raises(ValueError, match="Component type already registered"):
        component_factory.register("test_type", MockComponent)


@pytest.mark.asyncio
async def test_component_factory_events(
    component_factory: ComponentFactory,
    event_bus: AsyncMock,
):
    """Test component factory events."""
    component_factory.register("test_type", MockComponent)
    config = {"type": "test_type", "name": "test"}
    await component_factory.create(config)

    event_bus.publish.assert_called_once()
    event = event_bus.publish.call_args[0][0]
    assert isinstance(event, Event)
    assert event.type == EventType.COMPONENT_CREATED
    assert event.data["component_type"] == "test_type"
    assert event.data["config"] == config


@pytest.mark.asyncio
async def test_component_factory_error_handling(component_factory: ComponentFactory):
    """Test component factory error handling."""

    class ErrorComponent:
        """Component that raises an error on creation."""

        def __init__(self, **kwargs: Any) -> None:
            """Raise an error."""
            raise RuntimeError("Test error")

    component_factory.register("error_type", ErrorComponent)
    with pytest.raises(FactoryError, match="Failed to create component"):
        await component_factory.create({"type": "error_type", "name": "test"})


async def test_factory_initialization(factory):
    """Test factory initialization."""
    assert factory._component_types == {}
    assert factory._event_bus is not None


async def test_component_registration(factory):
    """Test component type registration."""
    # Register a component type
    factory.register("mock_component", MockComponent)
    assert "mock_component" in factory._component_types
    assert factory._component_types["mock_component"] == MockComponent

    # Test duplicate registration
    with pytest.raises(ValueError):
        factory.register("mock_component", MockComponent)


async def test_component_creation(factory, component_config, event_bus):
    """Test component creation."""
    # Register component type
    factory.register("mock_component", MockComponent)

    # Create component
    component = await factory.create(component_config)
    assert isinstance(component, MockComponent)
    assert component.config == component_config

    # Verify event was emitted
    event_bus.emit.assert_called_once()
    event = event_bus.emit.call_args[0][0]
    assert event.type == EventType.COMPONENT_CREATED


async def test_component_creation_error(factory, component_config):
    """Test component creation with invalid type."""
    with pytest.raises(FactoryError) as exc_info:
        await factory.create(component_config)

    assert "Component type not found" in str(exc_info.value)
    assert exc_info.value.details.get("component_type") == "mock_component"


async def test_component_lifecycle(factory, component_config):
    """Test component lifecycle management."""
    factory.register("mock_component", MockComponent)

    # Create and initialize component
    component = await factory.create(component_config)
    assert component.initialized

    # Clean up component
    await factory.cleanup(component)
    assert component.cleaned_up


async def test_factory_lifecycle_hooks(factory, component_config):
    """Test factory lifecycle hooks."""
    factory.register("mock_component", MockComponent)

    # Set up hooks
    before_create = AsyncMock()
    after_create = AsyncMock()
    factory.add_hook("before_create", before_create)
    factory.add_hook("after_create", after_create)

    # Create component
    component = await factory.create(component_config)

    # Verify hooks were called
    before_create.assert_called_once_with(component_config)
    after_create.assert_called_once_with(component)


async def test_factory_hook_removal(factory):
    """Test hook removal."""
    hook = AsyncMock()
    factory.add_hook("before_create", hook)
    assert hook in factory._hooks["before_create"]

    factory.remove_hook("before_create", hook)
    assert hook not in factory._hooks["before_create"]
