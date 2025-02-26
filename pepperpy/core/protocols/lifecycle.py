"""Lifecycle protocol for Pepperpy components.

This module defines the base lifecycle protocol that all components must implement.
"""

from abc import ABC, abstractmethod


class Lifecycle(ABC):
    """Base lifecycle protocol for all components.

    All components must implement this interface to ensure consistent
    lifecycle management across the framework.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component.

        This method should be called before using the component.
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up component resources.

        This method should be called when the component is no longer needed.
        """
        pass 