"""Tests for protocol implementations."""

from typing import Any

import pytest

from pepperpy.core.protocols.base import (
    Cleanable,
    Configurable,
    Describable,
    Identifiable,
    Initializable,
    Nameable,
    Observable,
    Observer,
    Pausable,
    Startable,
    Stateful,
    Stoppable,
    Validatable,
    Versionable,
)


class TestComponent:
    """Test component implementing all protocols."""

    def __init__(self) -> None:
        """Initialize component."""
        self._id = "test"
        self._name = "Test Component"
        self._description = "Test component description"
        self._version = "1.0.0"
        self._state = "created"
        self._observers: list[Observer] = []
        self._initialized = False
        self._cleaned = False
        self._started = False
        self._stopped = False
        self._paused = False

    # Identifiable
    @property
    def id(self) -> str:
        """Get component ID."""
        return self._id

    # Nameable
    @property
    def name(self) -> str:
        """Get component name."""
        return self._name

    # Describable
    @property
    def description(self) -> str:
        """Get component description."""
        return self._description

    # Versionable
    @property
    def version(self) -> str:
        """Get component version."""
        return self._version

    # Stateful
    @property
    def state(self) -> str:
        """Get component state."""
        return self._state

    # Observable
    def add_observer(self, observer: Observer) -> None:
        """Add observer."""
        self._observers.append(observer)

    def remove_observer(self, observer: Observer) -> None:
        """Remove observer."""
        self._observers.remove(observer)

    def notify(self, event: str, data: Any) -> None:
        """Notify observers."""
        for observer in self._observers:
            observer.update(self, event, data)

    # Initializable
    async def initialize(self) -> None:
        """Initialize component."""
        self._initialized = True
        self._state = "initialized"
        self.notify("initialized", None)

    # Cleanable
    async def cleanup(self) -> None:
        """Clean up component."""
        self._cleaned = True
        self._state = "cleaned"
        self.notify("cleaned", None)

    # Startable
    async def start(self) -> None:
        """Start component."""
        self._started = True
        self._state = "running"
        self.notify("started", None)

    # Stoppable
    async def stop(self) -> None:
        """Stop component."""
        self._stopped = True
        self._state = "stopped"
        self.notify("stopped", None)

    # Pausable
    async def pause(self) -> None:
        """Pause component."""
        self._paused = True
        self._state = "paused"
        self.notify("paused", None)

    async def resume(self) -> None:
        """Resume component."""
        self._paused = False
        self._state = "running"
        self.notify("resumed", None)

    # Configurable
    def configure(self, config: dict[str, Any]) -> None:
        """Configure component."""
        self._config = config
        self.notify("configured", config)

    # Validatable
    def validate(self) -> bool:
        """Validate component."""
        return True


class TestObserver:
    """Test observer implementation."""

    def __init__(self) -> None:
        """Initialize observer."""
        self.events: list[tuple[Observable, str, Any]] = []

    def update(self, subject: Observable, event: str, data: Any) -> None:
        """Update observer."""
        self.events.append((subject, event, data))


def test_protocol_implementations():
    """Test protocol implementations."""
    component = TestComponent()

    # Test protocol implementations
    assert isinstance(component, Identifiable)
    assert isinstance(component, Nameable)
    assert isinstance(component, Describable)
    assert isinstance(component, Versionable)
    assert isinstance(component, Stateful)
    assert isinstance(component, Observable)
    assert isinstance(component, Initializable)
    assert isinstance(component, Cleanable)
    assert isinstance(component, Startable)
    assert isinstance(component, Stoppable)
    assert isinstance(component, Pausable)
    assert isinstance(component, Configurable)
    assert isinstance(component, Validatable)


@pytest.mark.asyncio
async def test_lifecycle():
    """Test lifecycle protocol."""
    component = TestComponent()
    observer = TestObserver()

    # Add observer
    component.add_observer(observer)

    # Test lifecycle
    await component.initialize()
    assert component._initialized
    assert component.state == "initialized"
    assert observer.events[-1] == (component, "initialized", None)

    await component.start()
    assert component._started
    assert component.state == "running"
    assert observer.events[-1] == (component, "started", None)

    await component.pause()
    assert component._paused
    assert component.state == "paused"
    assert observer.events[-1] == (component, "paused", None)

    await component.resume()
    assert not component._paused
    assert component.state == "running"
    assert observer.events[-1] == (component, "resumed", None)

    await component.stop()
    assert component._stopped
    assert component.state == "stopped"
    assert observer.events[-1] == (component, "stopped", None)

    await component.cleanup()
    assert component._cleaned
    assert component.state == "cleaned"
    assert observer.events[-1] == (component, "cleaned", None)


def test_observer():
    """Test observer protocol."""
    component = TestComponent()
    observer = TestObserver()

    # Add observer
    component.add_observer(observer)
    assert observer in component._observers

    # Notify observers
    component.notify("test", "data")
    assert observer.events[-1] == (component, "test", "data")

    # Remove observer
    component.remove_observer(observer)
    assert observer not in component._observers


def test_configuration():
    """Test configuration protocol."""
    component = TestComponent()
    observer = TestObserver()
    component.add_observer(observer)

    # Configure component
    config = {"key": "value"}
    component.configure(config)
    assert component._config == config
    assert observer.events[-1] == (component, "configured", config)


def test_validation():
    """Test validation protocol."""
    component = TestComponent()
    assert component.validate()


if __name__ == "__main__":
    pytest.main([__file__])
