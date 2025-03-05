"""Observable protocols for PepperPy.

This module defines protocols for the observer pattern implementation
in the PepperPy framework.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Generic, List, Optional, Protocol, Set, TypeVar

T = TypeVar("T")  # Event type


class Observer(Generic[T], Protocol):
    """Protocol for observers in the system.

    Observers receive notifications from observables when events occur.
    """

    async def update(self, observable: "Observable", event: T) -> None:
        """Update the observer with a new event.

        Args:
            observable: Observable that triggered the event
            event: Event data
        """
        ...


class Observable(ABC):
    """Abstract base class for observable objects.

    Observable objects notify registered observers when events occur.
    """

    def __init__(self):
        """Initialize the observable."""
        self._observers: Set[Observer] = set()

    def add_observer(self, observer: Observer) -> None:
        """Add an observer.

        Args:
            observer: Observer to add
        """
        self._observers.add(observer)

    def remove_observer(self, observer: Observer) -> None:
        """Remove an observer.

        Args:
            observer: Observer to remove
        """
        self._observers.discard(observer)

    async def notify_observers(self, event: Any) -> None:
        """Notify all observers of an event.

        Args:
            event: Event data
        """
        for observer in self._observers:
            await observer.update(self, event)

    @property
    def observer_count(self) -> int:
        """Get the number of registered observers.

        Returns:
            Number of observers
        """
        return len(self._observers)


class EventObservable(Observable):
    """Observable that supports multiple event types.

    This class extends the basic Observable to support registering
    observers for specific event types.
    """

    def __init__(self):
        """Initialize the event observable."""
        super().__init__()
        self._event_observers: Dict[str, Set[Observer]] = {}

    def add_event_observer(self, event_type: str, observer: Observer) -> None:
        """Add an observer for a specific event type.

        Args:
            event_type: Event type to observe
            observer: Observer to add
        """
        if event_type not in self._event_observers:
            self._event_observers[event_type] = set()
        self._event_observers[event_type].add(observer)

    def remove_event_observer(self, event_type: str, observer: Observer) -> None:
        """Remove an observer for a specific event type.

        Args:
            event_type: Event type to stop observing
            observer: Observer to remove
        """
        if event_type in self._event_observers:
            self._event_observers[event_type].discard(observer)
            if not self._event_observers[event_type]:
                del self._event_observers[event_type]

    async def notify_event_observers(self, event_type: str, event: Any) -> None:
        """Notify observers of a specific event type.

        Args:
            event_type: Event type
            event: Event data
        """
        # Notify specific event observers
        if event_type in self._event_observers:
            for observer in self._event_observers[event_type]:
                await observer.update(self, event)

        # Also notify general observers
        await super().notify_observers(event)


class PropertyObservable(Observable):
    """Observable that notifies observers of property changes.

    This class extends the basic Observable to support notifying
    observers when properties change.
    """

    def __init__(self):
        """Initialize the property observable."""
        super().__init__()
        self._properties: Dict[str, Any] = {}

    def set_property(self, name: str, value: Any) -> None:
        """Set a property value.

        Args:
            name: Property name
            value: Property value
        """
        old_value = self._properties.get(name)
        if old_value != value:
            self._properties[name] = value
            self._notify_property_change(name, old_value, value)

    def get_property(self, name: str, default: Any = None) -> Any:
        """Get a property value.

        Args:
            name: Property name
            default: Default value if property doesn't exist

        Returns:
            Property value or default
        """
        return self._properties.get(name, default)

    def has_property(self, name: str) -> bool:
        """Check if a property exists.

        Args:
            name: Property name

        Returns:
            True if property exists, False otherwise
        """
        return name in self._properties

    def _notify_property_change(
        self, name: str, old_value: Any, new_value: Any
    ) -> None:
        """Notify observers of a property change.

        Args:
            name: Property name
            old_value: Old property value
            new_value: New property value
        """
        event = {
            "type": "property_change",
            "property": name,
            "old_value": old_value,
            "new_value": new_value,
        }
        # Use asyncio.create_task to avoid blocking
        import asyncio

        asyncio.create_task(self.notify_observers(event))
