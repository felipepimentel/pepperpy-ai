"""Base classes and interfaces for PepperPy core components.

This module provides the foundational classes and interfaces that form the
core of the PepperPy framework. These components are used throughout the
framework to provide consistent behavior and interfaces.

It includes:
- Base component classes
- Common interfaces
- Core client functionality
- Lifecycle management
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


class BaseComponent(ABC):
    """Base class for all components in the system.

    Provides common functionality for component identification,
    configuration, and lifecycle management.
    """

    def __init__(self, name: str = "", **kwargs):
        """Initialize the component with optional name and keyword arguments.

        Args:
            name: Component name
            **kwargs: Additional configuration parameters
        """
        self._name = name
        self.config = kwargs
        self._metadata: Dict[str, Any] = {}

    @property
    def name(self) -> str:
        """Get component name.

        Returns:
            Component name
        """
        return self._name

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to component.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        return self._metadata.get(key, default)

    def has_metadata(self, key: str) -> bool:
        """Check if metadata key exists.

        Args:
            key: Metadata key

        Returns:
            True if key exists
        """
        return key in self._metadata

    @abstractmethod
    def initialize(self):
        """Initialize the component. Must be implemented by subclasses."""
        pass


class BaseProvider(BaseComponent):
    """Base class for all providers in the system."""

    @abstractmethod
    def validate(self):
        """Validate the provider configuration. Must be implemented by subclasses."""
        pass


# Import from submodules
from .manager import BaseManager, ComponentState

__all__ = [
    "BaseComponent",
    "BaseProvider",
    "BaseManager",
    "ComponentState",
    "ComponentConfig",
    "ComponentCallback",
    "Lifecycle",
]
