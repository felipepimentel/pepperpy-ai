"""Common base classes for PepperPy components.

This module provides the core base classes and interfaces used throughout the framework.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol


@dataclass
class ComponentConfig:
    """Base configuration for components."""

    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)


class ComponentCallback(Protocol):
    """Protocol for component callbacks."""

    async def on_state_change(self, component_id: str, state: str) -> None:
        """Called when component state changes."""
        ...

    async def on_error(self, component_id: str, error: Exception) -> None:
        """Called when component encounters an error."""
        ...


class Lifecycle(ABC):
    """Base class for components with lifecycle management."""

    async def initialize(self) -> None:
        """Initialize component.

        This method should be called before using the component.
        It sets up any required resources and prepares the component for use.
        """
        await self._initialize()

    async def cleanup(self) -> None:
        """Clean up component resources.

        This method should be called when the component is no longer needed.
        It releases any resources held by the component.
        """
        await self._cleanup()

    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize component resources.

        This method should be implemented by subclasses to perform
        component-specific initialization.
        """
        pass

    @abstractmethod
    async def _cleanup(self) -> None:
        """Clean up component resources.

        This method should be implemented by subclasses to perform
        component-specific cleanup.
        """
        pass
