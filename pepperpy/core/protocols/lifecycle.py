"""Lifecycle protocol.

This module defines the standard lifecycle interface that all components
must implement.
"""

from abc import ABC, abstractmethod
from typing import Protocol


class Lifecycle(ABC):
    """Base class for components with lifecycle management.

    All components that need initialization and cleanup must inherit
    from this class.

    Example:
        >>> class MyComponent(Lifecycle):
        ...     async def initialize(self) -> None:
        ...         # Setup resources
        ...         pass
        ...
        ...     async def cleanup(self) -> None:
        ...         # Cleanup resources
        ...         pass

    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component.

        This method should be called before using the component.
        It should set up any required resources and put the component
        in a ready state.

        Raises:
            ConfigurationError: If initialization fails due to configuration
            StateError: If component is in invalid state
            ResourceError: If resource allocation fails

        """

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up component resources.

        This method should be called when the component is no longer needed.
        It should release any resources and put the component in a cleaned state.

        Raises:
            StateError: If component is in invalid state
            ResourceError: If resource cleanup fails

        """


class LifecycleHook(Protocol):
    """Protocol for lifecycle hooks.

    Hooks are called during component lifecycle events to allow
    monitoring and customization of behavior.

    Example:
        >>> class LoggingHook(LifecycleHook):
        ...     async def pre_initialize(self, component: Lifecycle) -> None:
        ...         print(f"Initializing {component}")
        ...
        ...     async def post_initialize(self, component: Lifecycle) -> None:
        ...         print(f"Initialized {component}")
        ...
        ...     async def pre_cleanup(self, component: Lifecycle) -> None:
        ...         print(f"Cleaning up {component}")
        ...
        ...     async def post_cleanup(self, component: Lifecycle) -> None:
        ...         print(f"Cleaned up {component}")
        ...
        ...     async def on_error(self, component: Lifecycle, error: Exception) -> None:
        ...         print(f"Error in {component}: {error}")

    """

    async def pre_initialize(self, component: Lifecycle) -> None:
        """Called before component initialization.

        Args:
            component: Component being initialized

        """
        ...

    async def post_initialize(self, component: Lifecycle) -> None:
        """Called after component initialization.

        Args:
            component: Component that was initialized

        """
        ...

    async def pre_cleanup(self, component: Lifecycle) -> None:
        """Called before component cleanup.

        Args:
            component: Component being cleaned up

        """
        ...

    async def post_cleanup(self, component: Lifecycle) -> None:
        """Called after component cleanup.

        Args:
            component: Component that was cleaned up

        """
        ...

    async def on_error(self, component: Lifecycle, error: Exception) -> None:
        """Called when a lifecycle operation fails.

        Args:
            component: Component that failed
            error: Error that occurred

        """
        ...


__all__ = ["Lifecycle", "LifecycleHook"]
