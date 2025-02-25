"""Lifecycle protocol for the Pepperpy framework.

This module defines the Lifecycle protocol used throughout the framework
for managing component lifecycles.
"""

from abc import ABC, abstractmethod
from typing import Protocol

from pepperpy.core.errors import ComponentError


class Lifecycle(Protocol):
    """Protocol for components with lifecycle management."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component.

        Raises:
            ComponentError: If initialization fails
        """
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up the component.

        Raises:
            ComponentError: If cleanup fails
        """
        ...


class LifecycleComponent(ABC):
    """Base class for components with lifecycle management."""

    def __init__(self, name: str) -> None:
        """Initialize the component.

        Args:
            name: The name of the component.
        """
        self.name = name
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the component.

        Raises:
            ComponentError: If initialization fails or if already initialized
        """
        if self._initialized:
            raise ComponentError(f"Component {self.name} is already initialized")
        try:
            await self._initialize()
            self._initialized = True
        except Exception as e:
            raise ComponentError(
                f"Failed to initialize component {self.name}: {e}"
            ) from e

    async def cleanup(self) -> None:
        """Clean up the component.

        Raises:
            ComponentError: If cleanup fails or if not initialized
        """
        if not self._initialized:
            raise ComponentError(f"Component {self.name} is not initialized")
        try:
            await self._cleanup()
            self._initialized = False
        except Exception as e:
            raise ComponentError(
                f"Failed to clean up component {self.name}: {e}"
            ) from e

    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize the component.

        This method should be implemented by subclasses to perform their
        specific initialization logic.

        Raises:
            ComponentError: If initialization fails
        """
        pass

    @abstractmethod
    async def _cleanup(self) -> None:
        """Clean up the component.

        This method should be implemented by subclasses to perform their
        specific cleanup logic.

        Raises:
            ComponentError: If cleanup fails
        """
        pass
