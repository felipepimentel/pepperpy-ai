"""Capabilities module for the Pepperpy framework.

This module provides functionality for managing AI capabilities:
- Base capability interface
- Capability configuration
- Common capability types
"""

from enum import Enum, auto
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from pepperpy.core.extensions import Extension, ExtensionMetadata
from pepperpy.core.events import EventBus


class CapabilityType(Enum):
    """Types of capabilities."""

    MEMORY = auto()
    STORAGE = auto()
    TASK = auto()
    CHAT = auto()
    CALENDAR = auto()
    NOTE = auto()


class CapabilityMetadata(ExtensionMetadata):
    """Metadata for capabilities.

    Attributes:
        capability_type: Type of capability
        capability_name: Name of the capability
        version: Version of the capability
        tags: Capability tags
        properties: Additional properties
    """

    capability_type: CapabilityType
    capability_name: str
    version: str
    tags: List[str] = Field(default_factory=list)
    properties: Dict[str, Any] = Field(default_factory=dict)


class BaseCapability(Extension):
    """Base class for AI capabilities.

    This class defines the interface that all capabilities must implement.
    """

    def __init__(
        self,
        metadata: CapabilityMetadata,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        """Initialize capability.

        Args:
            metadata: Capability metadata
            event_bus: Optional event bus for capability events
        """
        super().__init__(
            name=metadata.capability_name,
            version=metadata.version,
            event_bus=event_bus,
        )
        self._capability_metadata = metadata

    @property
    def metadata(self) -> ExtensionMetadata:
        """Get extension metadata."""
        return super().metadata

    @property
    def capability_metadata(self) -> CapabilityMetadata:
        """Get capability metadata.

        Returns:
            Capability metadata
        """
        return self._capability_metadata

    async def _initialize(self) -> None:
        """Initialize capability resources."""
        pass

    async def _cleanup(self) -> None:
        """Clean up capability resources."""
        pass

    async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute capability operation.

        Args:
            operation: Operation to execute
            params: Operation parameters

        Returns:
            Operation result

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Capability must implement execute method")
