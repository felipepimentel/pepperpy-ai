"""Adapter type system.

This module defines the type system for adapters.
"""

from enum import Enum, auto
from typing import Any, Dict, Optional, Protocol, Type


class AdapterType(Enum):
    """Adapter type enumeration."""

    GENERIC = auto()
    LANGCHAIN = auto()
    AUTOGEN = auto()
    LLAMAINDEX = auto()
    CUSTOM = auto()

    def __str__(self) -> str:
        """Return string representation."""
        return self.name.lower()


class AdapterCapability(Enum):
    """Adapter capability enumeration."""

    CHAT = auto()
    COMPLETION = auto()
    EMBEDDING = auto()
    FUNCTION_CALLING = auto()
    TOOL_CALLING = auto()
    VISION = auto()
    AUDIO = auto()
    CUSTOM = auto()

    def __str__(self) -> str:
        """Return string representation."""
        return self.name.lower()


class AdapterProtocol(Protocol):
    """Protocol for adapter objects."""

    adapter_id: str
    name: str
    description: str
    adapter_type: AdapterType
    initialized: bool
    config: Dict[str, Any]

    async def initialize(self) -> None:
        """Initialize the adapter."""
        ...

    async def cleanup(self) -> None:
        """Clean up resources used by the adapter."""
        ...

    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the adapter with the provided configuration."""
        ...


class AdapterPluginProtocol(Protocol):
    """Protocol for adapter plugin objects."""

    adapter_id: str
    name: str
    description: str
    enabled: bool
    adapter_class: Optional[Type[AdapterProtocol]]

    def register_adapter(self, adapter_class: Type[AdapterProtocol]) -> None:
        """Register an adapter class with this plugin."""
        ...

    def enable(self) -> None:
        """Enable this adapter plugin."""
        ...

    def disable(self) -> None:
        """Disable this adapter plugin."""
        ...

    @property
    def is_enabled(self) -> bool:
        """Check if this adapter plugin is enabled."""
        ...
