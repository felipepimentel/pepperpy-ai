"""
Core types module defining fundamental types used throughout PepperPy.

This module provides type definitions, protocols, and type aliases that are used
across the framework.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Protocol, TypeVar
from uuid import UUID, uuid4

# Type variables
ComponentT = TypeVar("ComponentT", bound="BaseComponent")
ConfigT = TypeVar("ConfigT", bound=Dict[str, Any])
EventT = TypeVar("EventT", bound="Event")


class BaseComponent(ABC):
    """Base protocol for all components in PepperPy."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the component."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources used by the component."""
        pass


class Event:
    """Base class for all events in PepperPy."""

    def __init__(self, event_type: str, source: str, data: Any = None):
        self.id = uuid4()
        self.type = event_type
        self.source = source
        self.data = data
        self.timestamp = datetime.utcnow()

    def __repr__(self) -> str:
        return f"Event(id={self.id}, type={self.type}, source={self.source})"


@dataclass
class Result:
    """Generic result type for operations."""

    success: bool
    data: Any = None
    error: Optional[str] = None


class Status(Enum):
    """Common status values for components and operations."""

    UNKNOWN = auto()
    INITIALIZING = auto()
    READY = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPED = auto()
    ERROR = auto()


class Priority(Enum):
    """Priority levels for tasks and operations."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Metadata:
    """Metadata for components and artifacts."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    version: str = "0.1.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)


class Serializable(Protocol):
    """Protocol for objects that can be serialized to and from dictionaries."""

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert the object to a dictionary."""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Serializable":
        """Create an object from a dictionary."""
        pass


class Validatable(Protocol):
    """Protocol for objects that can be validated."""

    @abstractmethod
    def validate(self) -> Result:
        """Validate the object's state."""
        pass


class Identifiable(Protocol):
    """Protocol for objects that have a unique identifier."""

    @property
    @abstractmethod
    def id(self) -> UUID:
        """Get the object's unique identifier."""
        pass


class Versionable(Protocol):
    """Protocol for objects that have version information."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Get the object's version."""
        pass


# Common type aliases
Json = Dict[str, Any]
ConfigDict = Dict[str, Any]
MetadataDict = Dict[str, Any]
EventData = Any
ComponentID = UUID
ProviderID = UUID

# Export all types
__all__ = [
    "ComponentT",
    "ConfigT",
    "EventT",
    "BaseComponent",
    "Event",
    "Result",
    "Status",
    "Priority",
    "Metadata",
    "Serializable",
    "Validatable",
    "Identifiable",
    "Versionable",
    "Json",
    "ConfigDict",
    "MetadataDict",
    "EventData",
    "ComponentID",
    "ProviderID",
]
