"""Base adapter module.

This module provides the base classes and interfaces for adapters.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Type, TypeVar

from pepperpy.adapters.types import AdapterType
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound="BaseAdapter")


class BaseAdapter(ABC):
    """Base class for all adapters."""

    adapter_type: AdapterType = AdapterType.GENERIC

    def __init__(self, adapter_id: str, name: str, description: str = ""):
        """Initialize the adapter.

        Args:
            adapter_id: Unique identifier for the adapter
            name: Human-readable name for the adapter
            description: Description of the adapter's functionality
        """
        self.adapter_id = adapter_id
        self.name = name
        self.description = description
        self.initialized = False
        self.config: Dict[str, Any] = {}

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the adapter.

        This method should be called before using the adapter.
        """
        self.initialized = True

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources used by the adapter.

        This method should be called when the adapter is no longer needed.
        """
        self.initialized = False

    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the adapter with the provided configuration.

        Args:
            config: Configuration dictionary
        """
        self.config.update(config)

    @classmethod
    def create(cls: Type[T], adapter_id: str, name: str, **kwargs) -> T:
        """Create a new instance of the adapter.

        Args:
            adapter_id: Unique identifier for the adapter
            name: Human-readable name for the adapter
            **kwargs: Additional arguments to pass to the constructor

        Returns:
            A new instance of the adapter
        """
        return cls(adapter_id, name, **kwargs)


class AdapterFactory(ABC):
    """Factory for creating adapters."""

    def __init__(self, adapter_type: AdapterType):
        """Initialize the adapter factory.

        Args:
            adapter_type: Type of adapters this factory creates
        """
        self.adapter_type = adapter_type

    @abstractmethod
    async def create(self, config: Dict[str, Any]) -> BaseAdapter:
        """Create a new adapter instance.

        Args:
            config: Configuration for the adapter

        Returns:
            A new adapter instance
        """
        pass
