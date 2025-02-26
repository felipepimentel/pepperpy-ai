"""
Core protocols module defining fundamental protocols used throughout PepperPy.

This module provides protocol definitions that define the interfaces that various
components must implement.
"""

from abc import abstractmethod
from typing import Any, Dict, Protocol, TypeVar
from uuid import UUID

from ..types import Event, Result

T = TypeVar("T")


class Initializable(Protocol):
    """Protocol for components that can be initialized."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the component."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources used by the component."""
        pass


class Configurable(Protocol):
    """Protocol for components that can be configured."""

    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the component with the given configuration."""
        pass

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration."""
        pass


class Observable(Protocol):
    """Protocol for components that can emit events."""

    @abstractmethod
    def add_observer(self, observer: "Observer") -> None:
        """Add an observer to this component."""
        pass

    @abstractmethod
    def remove_observer(self, observer: "Observer") -> None:
        """Remove an observer from this component."""
        pass

    @abstractmethod
    def notify_observers(self, event: Event) -> None:
        """Notify all observers of an event."""
        pass


class Observer(Protocol):
    """Protocol for components that can receive events."""

    @abstractmethod
    def update(self, observable: Observable, event: Event) -> None:
        """Handle an update from an observable component."""
        pass


class Identifiable(Protocol):
    """Protocol for components that have a unique identifier."""

    @property
    @abstractmethod
    def id(self) -> UUID:
        """Get the component's unique identifier."""
        pass


class Validatable(Protocol):
    """Protocol for components that can be validated."""

    @abstractmethod
    def validate(self) -> Result:
        """Validate the component's state."""
        pass


class Serializable(Protocol):
    """Protocol for components that can be serialized."""

    @abstractmethod
    def serialize(self) -> Dict[str, Any]:
        """Serialize the component to a dictionary."""
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, data: Dict[str, Any]) -> "Serializable":
        """Create a component from a serialized dictionary."""
        pass


class Factory(Protocol[T]):
    """Protocol for component factories."""

    @abstractmethod
    def create(self, **kwargs: Any) -> T:
        """Create a new component instance."""
        pass


class Provider(Protocol):
    """Protocol for service providers."""

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the service."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the service."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the service is available."""
        pass


class Manager(Protocol[T]):
    """Protocol for component managers."""

    @abstractmethod
    def add(self, component: T) -> None:
        """Add a component to be managed."""
        pass

    @abstractmethod
    def remove(self, component: T) -> None:
        """Remove a component from management."""
        pass

    @abstractmethod
    def get(self, id: UUID) -> T:
        """Get a managed component by ID."""
        pass

    @abstractmethod
    def list(self) -> Dict[UUID, T]:
        """List all managed components."""
        pass


# Export all protocols
__all__ = [
    "Initializable",
    "Configurable",
    "Observable",
    "Observer",
    "Identifiable",
    "Validatable",
    "Serializable",
    "Factory",
    "Provider",
    "Manager",
]
