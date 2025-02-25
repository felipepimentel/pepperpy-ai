"""Lifecycle protocol for the Pepperpy framework.

This module defines the Lifecycle protocol used throughout the framework
for managing component lifecycles.
"""

from abc import abstractmethod
from typing import Protocol


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


# Export public API
__all__ = [
    "Lifecycle",
]
