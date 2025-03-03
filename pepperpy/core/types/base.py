"""Base types for core components.

Defines the base types and interfaces used by core components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


class ComponentID(UUID):
    """Component identifier type."""



Metadata = Dict[str, Any]


class BaseComponent(ABC):
    """Base class for all components in the framework."""

    def __init__(self, name: str, id: Optional[UUID] = None) -> None:
        """Initialize component.

        Args:
            name: Component name
            id: Optional component ID (auto-generated if not provided)

        """
        self._id = id or uuid4()
        self._name = name
        self._metadata: Metadata = {}

    @property
    def id(self) -> ComponentID:
        """Get component ID."""
        return ComponentID(str(self._id))

    @property
    def name(self) -> str:
        """Get component name."""
        return self._name

    @property
    def metadata(self) -> Metadata:
        """Get component metadata."""
        return self._metadata

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata.

        Args:
            key: Metadata key
            value: Metadata value

        """
        self._metadata[key] = value

    def get_metadata(self, key: str) -> Optional[Any]:
        """Get metadata value.

        Args:
            key: Metadata key

        Returns:
            Metadata value if found, None otherwise

        """
        return self._metadata.get(key)

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the basecomponent.

        This method must be implemented by subclasses.
        """
