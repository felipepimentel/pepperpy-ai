"""Base protocols module.

This module provides core protocol definitions used throughout the framework.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Initializable(Protocol):
    """Protocol for components that can be initialized."""

    async def initialize(self) -> None:
        """Initialize component."""
        ...


@runtime_checkable
class Cleanable(Protocol):
    """Protocol for components that can be cleaned up."""

    async def cleanup(self) -> None:
        """Clean up component."""
        ...


@runtime_checkable
class Startable(Protocol):
    """Protocol for components that can be started."""

    async def start(self) -> None:
        """Start component."""
        ...


@runtime_checkable
class Stoppable(Protocol):
    """Protocol for components that can be stopped."""

    async def stop(self) -> None:
        """Stop component."""
        ...


@runtime_checkable
class Pausable(Protocol):
    """Protocol for components that can be paused."""

    async def pause(self) -> None:
        """Pause component."""
        ...

    async def resume(self) -> None:
        """Resume component."""
        ...


@runtime_checkable
class Configurable(Protocol):
    """Protocol for components that can be configured."""

    def configure(self, config: dict[str, Any]) -> None:
        """Configure component.

        Args:
            config: Configuration dictionary
        """
        ...


@runtime_checkable
class Observable(Protocol):
    """Protocol for components that can be observed."""

    def add_observer(self, observer: Observer) -> None:
        """Add observer.

        Args:
            observer: Observer to add
        """
        ...

    def remove_observer(self, observer: Observer) -> None:
        """Remove observer.

        Args:
            observer: Observer to remove
        """
        ...


@runtime_checkable
class Observer(Protocol):
    """Protocol for observers."""

    def update(self, subject: Observable, event: str, data: Any) -> None:
        """Update observer.

        Args:
            subject: Subject that triggered the update
            event: Event name
            data: Event data
        """
        ...


@runtime_checkable
class Validatable(Protocol):
    """Protocol for components that can be validated."""

    def validate(self) -> bool:
        """Validate component.

        Returns:
            bool: True if valid
        """
        ...


@runtime_checkable
class Identifiable(Protocol):
    """Protocol for components that have an identifier."""

    @property
    def id(self) -> str:
        """Get component identifier.

        Returns:
            str: Component identifier
        """
        ...


@runtime_checkable
class Nameable(Protocol):
    """Protocol for components that have a name."""

    @property
    def name(self) -> str:
        """Get component name.

        Returns:
            str: Component name
        """
        ...


@runtime_checkable
class Describable(Protocol):
    """Protocol for components that have a description."""

    @property
    def description(self) -> str:
        """Get component description.

        Returns:
            str: Component description
        """
        ...


@runtime_checkable
class Versionable(Protocol):
    """Protocol for components that have a version."""

    @property
    def version(self) -> str:
        """Get component version.

        Returns:
            str: Component version
        """
        ...


@runtime_checkable
class Stateful(Protocol):
    """Protocol for components that have state."""

    @property
    def state(self) -> str:
        """Get component state.

        Returns:
            str: Component state
        """
        ...


# Export public API
__all__ = [
    "Cleanable",
    "Configurable",
    "Describable",
    "Identifiable",
    "Initializable",
    "Nameable",
    "Observable",
    "Observer",
    "Pausable",
    "Startable",
    "Stateful",
    "Stoppable",
    "Validatable",
    "Versionable",
]
