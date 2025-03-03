"""Base manager module for the Pepperpy framework.

This module provides a base manager implementation that can be extended
by specific subsystem managers throughout the framework.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pepperpy.core.protocols.lifecycle import Lifecycle


# Define component states for managers
class ComponentState(Enum):
    """Component execution states."""

    UNREGISTERED = "unregistered"
    INITIALIZING = "initializing"
    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"
    ERROR = "error"


T = TypeVar("T")  # Type of managed components


class BaseManager(Lifecycle, Generic[T], ABC):
    """Base class for component managers.

    This class provides common functionality for managing components
    of a specific type, including registration, retrieval, and lifecycle
    management.

    Attributes:
        config: Configuration dictionary
        _components: Dictionary of registered components
        _state: Current component state

    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the manager.

        Args:
            config: Optional configuration dictionary

        """
        super().__init__()
        self.config = config or {}
        self._components: Dict[str, T] = {}
        self._state = ComponentState.UNREGISTERED

    async def initialize(self) -> None:
        """Initialize the manager and all registered components.

        This method initializes all registered components that implement
        the Lifecycle protocol.

        Raises:
            RuntimeError: If initialization fails

        """
        try:
            # Initialize all components that implement Lifecycle
            for name, component in self._components.items():
                if isinstance(component, Lifecycle):
                    try:
                        await component.initialize()
                    except Exception as e:
                        raise RuntimeError(
                            f"Failed to initialize component '{name}': {e!s}",
                        ) from e

            self._state = ComponentState.RUNNING
        except Exception as e:
            self._state = ComponentState.ERROR
            raise RuntimeError(f"Failed to initialize manager: {e!s}") from e

    async def cleanup(self) -> None:
        """Clean up the manager and all registered components.

        This method cleans up all registered components that implement
        the Lifecycle protocol.

        Raises:
            RuntimeError: If cleanup fails

        """
        try:
            # Clean up all components that implement Lifecycle
            for name, component in self._components.items():
                if isinstance(component, Lifecycle):
                    try:
                        await component.cleanup()
                    except Exception as e:
                        # Log error but continue cleanup
                        print(f"Error cleaning up component '{name}': {e!s}")

            # Clear components
            self._components.clear()

            self._state = ComponentState.UNREGISTERED
        except Exception as e:
            self._state = ComponentState.ERROR
            raise RuntimeError(f"Failed to clean up manager: {e!s}") from e

    def register(self, name: str, component: T) -> None:
        """Register a component with the manager.

        Args:
            name: Component name
            component: Component instance

        Raises:
            ValueError: If a component with the same name is already registered

        """
        if name in self._components:
            raise ValueError(f"Component '{name}' is already registered")

        self._components[name] = component

    def unregister(self, name: str) -> Optional[T]:
        """Unregister a component from the manager.

        Args:
            name: Component name

        Returns:
            The unregistered component, or None if not found

        """
        return self._components.pop(name, None)

    def get(self, name: str) -> Optional[T]:
        """Get a registered component by name.

        Args:
            name: Component name

        Returns:
            The component, or None if not found

        """
        return self._components.get(name)

    def get_all(self) -> Dict[str, T]:
        """Get all registered components.

        Returns:
            Dictionary of all registered components

        """
        return self._components.copy()

    def get_names(self) -> List[str]:
        """Get names of all registered components.

        Returns:
            List of component names

        """
        return list(self._components.keys())

    def has(self, name: str) -> bool:
        """Check if a component is registered.

        Args:
            name: Component name

        Returns:
            True if the component is registered, False otherwise

        """
        return name in self._components

    @abstractmethod
    def create(self, name: str, **kwargs: Any) -> T:
        """Create a new component instance.

        This method must be implemented by subclasses to create
        components specific to their domain.

        Args:
            name: Component name
            **kwargs: Component-specific arguments

        Returns:
            New component instance

        """
