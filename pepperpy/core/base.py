"""@file: base.py
@purpose: Core base interfaces and classes for the Pepperpy framework
@component: Core
@created: 2024-02-15
@task: TASK-003
@status: active
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Protocol, TypeVar, Union
from uuid import UUID, uuid4

from pepperpy.core.types import (
    AgentID,
    CapabilityID,
    MemoryID,
    ProviderID,
    ResourceID,
    WorkflowID,
)


class AgentState(str, Enum):
    """Agent execution states."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentContext:
    """Context for agent execution."""

    agent_id: AgentID
    state: AgentState
    start_time: datetime
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentCallback(Protocol):
    """Protocol for agent execution callbacks."""

    async def on_start(self, context: AgentContext) -> None:
        """Called when agent execution starts.

        Args:
            context: Agent execution context
        """
        ...

    async def on_pause(self, context: AgentContext) -> None:
        """Called when agent execution is paused.

        Args:
            context: Agent execution context
        """
        ...

    async def on_resume(self, context: AgentContext) -> None:
        """Called when agent execution resumes.

        Args:
            context: Agent execution context
        """
        ...

    async def on_complete(self, context: AgentContext) -> None:
        """Called when agent execution completes successfully.

        Args:
            context: Agent execution context
        """
        ...

    async def on_error(self, context: AgentContext) -> None:
        """Called when agent execution fails.

        Args:
            context: Agent execution context
        """
        ...


# Base Protocols and Interfaces


class Identifiable(Protocol):
    """Base protocol for objects that have a unique identifier."""

    @property
    def id(self) -> UUID:
        """Get the unique identifier."""
        ...


class Lifecycle(ABC):
    """Base class for components with lifecycle management."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up the component."""
        pass


class Validatable(Protocol):
    """Base protocol for objects that can be validated."""

    @abstractmethod
    def validate(self) -> None:
        """Validate the object state."""
        ...


# Base Data Classes


class Metadata:
    """Component metadata."""

    def __init__(
        self,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        version: Optional[str] = None,
        tags: Optional[list[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize metadata.

        Args:
            created_at: Creation timestamp
            updated_at: Last update timestamp
            version: Component version
            tags: Component tags
            properties: Additional properties
        """
        self.created_at = created_at or datetime.now(UTC)
        self.updated_at = updated_at or datetime.now(UTC)
        self.version = version or "0.1.0"
        self.tags = tags or []
        self.properties = properties or {}


# Base Classes


class BaseComponent:
    """Base component with metadata and lifecycle management."""

    def __init__(
        self,
        id: Optional[UUID] = None,
        metadata: Optional[Metadata] = None,
    ) -> None:
        """Initialize component.

        Args:
            id: Component ID
            metadata: Component metadata
        """
        self.id = id or uuid4()
        self.metadata = metadata or Metadata()

    async def initialize(self) -> None:
        """Initialize component.

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement initialize()")

    async def cleanup(self) -> None:
        """Clean up component.

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement cleanup()")


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

    def __init__(
        self,
        id: UUID,
        metadata: Optional[Metadata] = None,
        callback: Optional[AgentCallback] = None,
    ) -> None:
        super().__init__(id, metadata)
        self._callback = callback
        self._context = AgentContext(
            agent_id=AgentID(id),
            state=AgentState.IDLE,
            start_time=datetime.utcnow(),
        )

    @property
    def context(self) -> AgentContext:
        """Get the agent's execution context."""
        return self._context

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


# Expose public interface
__all__ = [
    # Protocols
    "Identifiable",
    "Lifecycle",
    "Validatable",
    # Data classes
    "Metadata",
    "AgentContext",
    # Enums
    "AgentState",
    # Base classes
    "BaseComponent",
    "BaseProvider",
    "BaseAgent",
    "BaseResource",
    "BaseCapability",
    "BaseWorkflow",
    # Protocols
    "AgentCallback",
    # Generic types
    "Registry",
    # Type aliases
    "ComponentID",
]
