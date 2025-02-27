"""Common base classes for PepperPy components.

This module provides base classes and interfaces used across the PepperPy ecosystem:
- BaseComponent: Abstract base class for all components
"""

from abc import ABC
from typing import Any, Dict


class BaseComponent(ABC):
    """Base class for all PepperPy components.

    Provides common functionality for component identification,
    configuration, and lifecycle management.
    """

    def __init__(self, name: str) -> None:
        """Initialize component.

        Args:
            name: Component name
        """
        self._name = name
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
