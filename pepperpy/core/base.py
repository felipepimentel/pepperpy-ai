"""@file: base.py
@purpose: Core base interfaces and classes for the Pepperpy framework
@component: Core
@created: 2024-02-15
@task: TASK-003
@status: active
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Protocol, TypeVar, Union
from uuid import UUID

from pepperpy.core.types import (
    AgentID,
    CapabilityID,
    MemoryID,
    ProviderID,
    ResourceID,
    WorkflowID,
)

# Base Protocols and Interfaces


class Identifiable(Protocol):
    """Base protocol for objects that have a unique identifier."""

    @property
    def id(self) -> UUID:
        """Get the unique identifier."""
        ...


class Lifecycle(Protocol):
    """Base protocol for objects with lifecycle management."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the object."""
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        ...


class Validatable(Protocol):
    """Base protocol for objects that can be validated."""

    @abstractmethod
    def validate(self) -> None:
        """Validate the object state."""
        ...


# Base Data Classes


@dataclass
class Metadata:
    """Base metadata for all framework objects."""

    created_at: datetime
    updated_at: datetime
    version: str
    tags: List[str]
    properties: Dict[str, Any]


# Base Classes


class BaseComponent(ABC, Identifiable, Lifecycle, Validatable):
    """Base class for all framework components."""

    def __init__(self, id: UUID, metadata: Optional[Metadata] = None) -> None:
        self._id = id
        self._metadata = metadata or Metadata(
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1.0.0",
            tags=[],
            properties={},
        )

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def metadata(self) -> Metadata:
        return self._metadata

    def validate(self) -> None:
        """Default validation implementation."""
        if not self._id:
            raise ValueError("Component must have a valid ID")
        if not self._metadata:
            raise ValueError("Component must have valid metadata")


class BaseProvider(BaseComponent):
    """Base class for all providers."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the provider."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the provider."""
        ...


class BaseAgent(BaseComponent):
    """Base class for all agents."""

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the agent's main functionality."""
        ...


class BaseResource(BaseComponent):
    """Base class for all resources."""

    @abstractmethod
    async def load(self) -> Any:
        """Load the resource data."""
        ...

    @abstractmethod
    async def save(self, data: Any) -> None:
        """Save the resource data."""
        ...


class BaseCapability(BaseComponent):
    """Base class for all capabilities."""

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the capability."""
        ...


class BaseWorkflow(BaseComponent):
    """Base class for all workflows."""

    @abstractmethod
    async def start(self) -> None:
        """Start the workflow."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the workflow."""
        ...


# Generic Types


T = TypeVar("T")


class Registry(Generic[T]):
    """Generic registry for managing framework components."""

    def __init__(self) -> None:
        self._items: Dict[UUID, T] = {}

    def register(self, item: T) -> None:
        """Register a new item."""
        if not isinstance(item, BaseComponent):
            raise TypeError("Item must be a BaseComponent")
        self._items[item.id] = item

    def unregister(self, id: UUID) -> None:
        """Unregister an item."""
        if id in self._items:
            del self._items[id]

    def get(self, id: UUID) -> Optional[T]:
        """Get an item by ID."""
        return self._items.get(id)

    def list(self) -> List[T]:
        """List all registered items."""
        return list(self._items.values())


# Type Aliases


ComponentID = Union[
    AgentID,
    ProviderID,
    ResourceID,
    CapabilityID,
    WorkflowID,
    MemoryID,
]
