"""Base lifecycle functionality for the Pepperpy framework.

This module provides base classes and protocols for lifecycle management.
"""

from abc import ABC, abstractmethod

from pepperpy.core.types.states import ComponentState
from pepperpy.monitoring.logging import get_logger


class LifecycleComponent(ABC):
    """Base class for components with lifecycle management."""

    def __init__(self, name: str) -> None:
        """Initialize the component.

        Args:
            name: Component name
        """
        self._name = name
        self._state = ComponentState.UNREGISTERED
        self._logger = get_logger(__name__)

    @property
    def name(self) -> str:
        """Get component name."""
        return self._name

    @property
    def state(self) -> ComponentState:
        """Get component state."""
        return self._state

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component.

        This method should be called before using the component.
        It should set up any necessary resources and put the component
        in a ready state.

        Raises:
            LifecycleError: If initialization fails
        """
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up the component.

        This method should be called when the component is no longer needed.
        It should release any resources and put the component in a cleaned state.

        Raises:
            LifecycleError: If cleanup fails
        """
        ...


__all__ = ["LifecycleComponent"]
