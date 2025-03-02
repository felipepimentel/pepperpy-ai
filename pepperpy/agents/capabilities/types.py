"""Type definitions for agent capabilities.

This module defines the type system for agent capabilities.
"""

from enum import Enum, auto
from typing import Any, Dict, Protocol


class CapabilityType(Enum):
    """Capability type enumeration."""

    GENERIC = auto()
    PLANNING = auto()
    REASONING = auto()
    RESEARCH = auto()
    LEARNING = auto()
    INTERACTION = auto()
    KNOWLEDGE = auto()
    CUSTOM = auto()

    def __str__(self) -> str:
        """Return string representation."""
        return self.name.lower()


class CapabilityProtocol(Protocol):
    """Protocol for capability objects."""

    capability_id: str
    name: str
    description: str
    capability_type: CapabilityType
    initialized: bool
    config: Dict[str, Any]

    async def initialize(self) -> None:
        """Initialize the capability."""
        ...

    async def cleanup(self) -> None:
        """Clean up resources used by the capability."""
        ...

    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the capability with the provided configuration."""
        ...
