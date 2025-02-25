"""Base lifecycle module for the Pepperpy framework.

This module provides core lifecycle functionality including:
- Component lifecycle management
- State transitions
- Error handling
"""

from __future__ import annotations

from pepperpy.core.errors import ComponentError
from pepperpy.core.protocols.lifecycle import Lifecycle
from pepperpy.core.types import ComponentState


class LifecycleComponent(Lifecycle):
    """Base class for components with lifecycle management."""

    def __init__(self, name: str) -> None:
        """Initialize component.

        Args:
            name: Component name
        """
        self.name = name
        self._state = ComponentState.CREATED

    async def initialize(self) -> None:
        """Initialize component.

        Raises:
            ComponentError: If initialization fails
        """
        try:
            self._state = ComponentState.INITIALIZING
            await self._initialize()
            self._state = ComponentState.READY
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ComponentError(f"Failed to initialize {self.name}: {e}")

    async def cleanup(self) -> None:
        """Clean up component.

        Raises:
            ComponentError: If cleanup fails
        """
        try:
            self._state = ComponentState.CLEANING
            await self._cleanup()
            self._state = ComponentState.CLEANED
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ComponentError(f"Failed to clean up {self.name}: {e}")

    async def _initialize(self) -> None:
        """Initialize component implementation.

        This method should be overridden by subclasses to perform
        component-specific initialization.
        """
        pass

    async def _cleanup(self) -> None:
        """Clean up component implementation.

        This method should be overridden by subclasses to perform
        component-specific cleanup.
        """
        pass


# Export public API
__all__ = [
    "LifecycleComponent",
]
