"""Tests for lifecycle protocol implementations."""

import pytest

from pepperpy.core.protocols.lifecycle import (
    Lifecycle,
    LifecycleObserver,
)


class TestLifecycleComponent:
    """Test component implementing lifecycle protocols."""

    def __init__(self) -> None:
        """Initialize component."""
        self._id = "test"
        self._name = "Test Component"
        self._state = "created"
        self._observers: list[LifecycleObserver] = []
        self._initialized = False
        self._cleaned = False
        self._started = False
        self._stopped = False

    # Lifecycle methods
    async def initialize(self) -> None:
        """Initialize component."""
        self._initialized = True
        self._state = "initialized"
        self._notify_observers("initialized")

    async def cleanup(self) -> None:
        """Clean up component."""
        self._cleaned = True
        self._state = "cleaned"
        self._notify_observers("cleaned")

    async def start(self) -> None:
        """Start component."""
        self._started = True
        self._state = "running"
        self._notify_observers("started")

    async def stop(self) -> None:
        """Stop component."""
        self._stopped = True
        self._state = "stopped"
        self._notify_observers("stopped")

    # Observer methods
    def add_observer(self, observer: LifecycleObserver) -> None:
        """Add observer."""
        self._observers.append(observer)

    def remove_observer(self, observer: LifecycleObserver) -> None:
        """Remove observer."""
        self._observers.remove(observer)

    def _notify_observers(self, event: str) -> None:
        """Notify observers."""
        for observer in self._observers:
            observer.on_state_change(self, event)


class TestLifecycleManager:
    """Test lifecycle manager implementation."""

    def __init__(self) -> None:
        """Initialize manager."""
        self._components: dict[str, Lifecycle] = {}

    def register(self, component: Lifecycle) -> None:
        """Register component."""
        self._components[component.id] = component

    def unregister(self, component: Lifecycle) -> None:
        """Unregister component."""
        del self._components[component.id]

    def get_component(self, component_id: str) -> Lifecycle:
        """Get component by ID."""
        return self._components[component_id]

    def list_components(self) -> list[Lifecycle]:
        """List all components."""
        return list(self._components.values())

    def get_state(self, component_id: str) -> str:
        """Get component state."""
        return self._components[component_id].state

    def is_running(self, component_id: str) -> bool:
        """Check if component is running."""
        return self.get_state(component_id) == "running"


class TestLifecycleHook:
    """Test lifecycle hook implementation."""

    def __init__(self) -> None:
        """Initialize hook."""
        self.events: list[tuple[str, str]] = []

    async def before_initialize(self, component: Lifecycle) -> None:
        """Before initialize hook."""
        self.events.append(("before_initialize", component.id))

    async def after_initialize(self, component: Lifecycle) -> None:
        """After initialize hook."""
        self.events.append(("after_initialize", component.id))

    async def before_cleanup(self, component: Lifecycle) -> None:
        """Before cleanup hook."""
        self.events.append(("before_cleanup", component.id))

    async def after_cleanup(self, component: Lifecycle) -> None:
        """After cleanup hook."""
        self.events.append(("after_cleanup", component.id))

    async def before_start(self, component: Lifecycle) -> None:
        """Before start hook."""
        self.events.append(("before_start", component.id))

    async def after_start(self, component: Lifecycle) -> None:
        """After start hook."""
        self.events.append(("after_start", component.id))

    async def before_stop(self, component: Lifecycle) -> None:
        """Before stop hook."""
        self.events.append(("before_stop", component.id))

    async def after_stop(self, component: Lifecycle) -> None:
        """After stop hook."""
        self.events.append(("after_stop", component.id))


class TestLifecycleObserver:
    """Test lifecycle observer implementation."""

    def __init__(self) -> None:
        """Initialize observer."""
        self.events: list[tuple[str, str]] = []

    def on_component_registered(self, component: Lifecycle) -> None:
        """Handle component registration."""
        self.events.append(("registered", component.id))

    def on_component_unregistered(self, component: Lifecycle) -> None:
        """Handle component unregistration."""
        self.events.append(("unregistered", component.id))

    def on_state_change(self, component: Lifecycle, state: str) -> None:
        """Handle state change."""
        self.events.append(("state_change", f"{component.id}:{state}"))


@pytest.mark.asyncio
async def test_lifecycle_component():
    """Test lifecycle component."""
    component = TestLifecycleComponent()
    observer = TestLifecycleObserver()

    # Add observer
    component.add_observer(observer)

    # Test lifecycle
    await component.initialize()
    assert component._initialized
    assert component._state == "initialized"
    assert observer.events[-1] == ("state_change", "test:initialized")

    await component.start()
    assert component._started
    assert component._state == "running"
    assert observer.events[-1] == ("state_change", "test:started")

    await component.stop()
    assert component._stopped
    assert component._state == "stopped"
    assert observer.events[-1] == ("state_change", "test:stopped")

    await component.cleanup()
    assert component._cleaned
    assert component._state == "cleaned"
    assert observer.events[-1] == ("state_change", "test:cleaned")


def test_lifecycle_manager():
    """Test lifecycle manager."""
    manager = TestLifecycleManager()
    component = TestLifecycleComponent()

    # Register component
    manager.register(component)
    assert manager.get_component("test") == component
    assert component in manager.list_components()
    assert manager.get_state("test") == "created"
    assert not manager.is_running("test")

    # Unregister component
    manager.unregister(component)
    with pytest.raises(KeyError):
        manager.get_component("test")


@pytest.mark.asyncio
async def test_lifecycle_hook():
    """Test lifecycle hook."""
    component = TestLifecycleComponent()
    hook = TestLifecycleHook()

    # Test hooks
    await hook.before_initialize(component)
    await hook.after_initialize(component)
    assert hook.events[-2:] == [
        ("before_initialize", "test"),
        ("after_initialize", "test"),
    ]

    await hook.before_start(component)
    await hook.after_start(component)
    assert hook.events[-2:] == [
        ("before_start", "test"),
        ("after_start", "test"),
    ]

    await hook.before_stop(component)
    await hook.after_stop(component)
    assert hook.events[-2:] == [
        ("before_stop", "test"),
        ("after_stop", "test"),
    ]

    await hook.before_cleanup(component)
    await hook.after_cleanup(component)
    assert hook.events[-2:] == [
        ("before_cleanup", "test"),
        ("after_cleanup", "test"),
    ]


def test_lifecycle_observer():
    """Test lifecycle observer."""
    component = TestLifecycleComponent()
    observer = TestLifecycleObserver()

    # Test observer methods
    observer.on_component_registered(component)
    assert observer.events[-1] == ("registered", "test")

    observer.on_state_change(component, "running")
    assert observer.events[-1] == ("state_change", "test:running")

    observer.on_component_unregistered(component)
    assert observer.events[-1] == ("unregistered", "test")


if __name__ == "__main__":
    pytest.main([__file__])
