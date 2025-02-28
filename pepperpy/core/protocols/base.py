"""Core protocols for the Pepperpy framework.

This module defines core protocols (interfaces) used throughout the framework
for dependency injection and loose coupling between components.
"""

from abc import abstractmethod
from collections.abc import AsyncIterator, Callable
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from typing_extensions import runtime_checkable

from pepperpy.core.common.events import EventBus, EventType
from pepperpy.core.common.lifecycle import Lifecycle
from pepperpy.core.common.metrics.types import MetricType

# Type variables for generic implementations
T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)

# Type aliases for better readability
MetricLabels = dict[str, str]
MetricCallback = Callable[[], int | float]

# Define type variables with proper variance
K_contra = TypeVar("K_contra", contravariant=True)  # For input keys
V_co = TypeVar("V_co", covariant=True)  # For output values
V_in = TypeVar("V_in")  # For input values (invariant)


class MemoryScope(str, Enum):
    """Memory scope types."""

    SESSION = "session"
    CONVERSATION = "conversation"
    GLOBAL = "global"


class ToolScope(str, Enum):
    """Tool scope types."""

    SESSION = "session"
    CONVERSATION = "conversation"
    GLOBAL = "global"


class ToolPermission(str, Enum):
    """Tool permission levels."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"


class MemoryEntry(Protocol[V_co]):
    """Protocol for memory entries."""

    @property
    def key(self) -> str:
        """Get entry key."""
        ...

    @property
    def value(self) -> V_co:
        """Get entry value."""
        ...

    @property
    def scope(self) -> MemoryScope:
        """Get entry scope."""
        ...

    @property
    def metadata(self) -> dict[str, Any]:
        """Get entry metadata."""
        ...

    @property
    def expires_at(self) -> datetime | None:
        """Get entry expiration time."""
        ...


@runtime_checkable
class Memory(Protocol[K_contra, V_co]):
    """Protocol for agent memory systems."""

    @abstractmethod
    async def store(
        self,
        key: K_contra,
        value: V_in,
        scope: MemoryScope = MemoryScope.SESSION,
        metadata: dict[str, Any] | None = None,
        expires_at: datetime | None = None,
    ) -> MemoryEntry[V_co]:
        """Store data in memory.

        Args:
            key: Memory key
            value: Value to store
            scope: Storage scope
            metadata: Optional metadata
            expires_at: Optional expiration time

        Returns:
            Created memory entry

        Raises:
            ValueError: If key is invalid
            TypeError: If value type is not supported
        """
        ...

    @abstractmethod
    async def retrieve(self, key: K_contra) -> MemoryEntry[V_co]:
        """Retrieve data from memory.

        Args:
            key: Memory key

        Returns:
            Memory entry

        Raises:
            KeyError: If key not found
            ValueError: If key is invalid
        """
        ...

    @abstractmethod
    async def delete(self, key: K_contra) -> bool:
        """Delete data from memory.

        Args:
            key: Memory key

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If key is invalid
        """
        ...

    @abstractmethod
    async def exists(self, key: K_contra) -> bool:
        """Check if key exists in memory.

        Args:
            key: Memory key

        Returns:
            True if exists, False otherwise

        Raises:
            ValueError: If key is invalid
        """
        ...

    @abstractmethod
    async def list(
        self,
        scope: MemoryScope | None = None,
        pattern: str | None = None,
    ) -> AsyncIterator[MemoryEntry[V_co]]:
        """List memory entries.

        Args:
            scope: Optional scope filter
            pattern: Optional key pattern filter

        Yields:
            Memory entries matching criteria
        """
        ...

    @abstractmethod
    async def clear(self, scope: MemoryScope | None = None) -> int:
        """Clear memory entries.

        Args:
            scope: Optional scope to clear

        Returns:
            Number of entries cleared
        """
        ...


class ToolMetadata(BaseModel):
    """Tool metadata."""

    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    permissions: list[ToolPermission] = Field(default_factory=list)
    scope: ToolScope = Field(default=ToolScope.SESSION)
    parameters: dict[str, Any] = Field(default_factory=dict)
    examples: list[dict[str, Any]] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    events: list[EventType] = Field(default_factory=list)

    @classmethod
    @field_validator("permissions")
    def validate_permissions(cls, v: list[ToolPermission]) -> list[ToolPermission]:
        """Validate permissions list."""
        if not v:
            v = [ToolPermission.READ]  # Default to read-only
        return sorted(set(v), key=lambda x: x.value)

    @classmethod
    @field_validator("events")
    def validate_events(cls, v: list[EventType]) -> list[EventType]:
        """Validate event types."""
        return sorted(set(v), key=lambda x: x.name)


@runtime_checkable
class Tool(Protocol):
    """Protocol for agent tools."""

    metadata: ToolMetadata
    event_bus: EventBus | None

    @abstractmethod
    async def execute(
        self,
        params: dict[str, Any],
        context_id: UUID,
    ) -> dict[str, Any]:
        """Execute the tool.

        Args:
            params: Execution parameters
            context_id: Execution context ID

        Returns:
            Execution results

        Raises:
            ValueError: If parameters are invalid
            PermissionError: If execution not permitted
            RuntimeError: If execution fails
        """
        ...

    @abstractmethod
    def validate_permissions(
        self,
        context_id: UUID,
        required_permissions: list[ToolPermission],
    ) -> bool:
        """Validate execution permissions.

        Args:
            context_id: Execution context ID
            required_permissions: Required permissions

        Returns:
            True if permitted, False otherwise
        """
        ...

    @abstractmethod
    async def validate_params(self, params: dict[str, Any]) -> bool:
        """Validate execution parameters.

        Args:
            params: Parameters to validate

        Returns:
            True if valid, False otherwise

        Raises:
            ValueError: If parameters are invalid
        """
        ...

    @abstractmethod
    async def record_metrics(
        self,
        operation: str,
        duration: float,
        success: bool,
        params: dict[str, Any],
    ) -> None:
        """Record tool metrics.

        Args:
            operation: Operation being measured
            duration: Operation duration in seconds
            success: Whether operation succeeded
            params: Operation parameters
        """
        ...

    @abstractmethod
    async def emit_event(
        self,
        event_type: EventType,
        data: dict[str, Any],
        context_id: UUID,
    ) -> None:
        """Emit a tool event.

        Args:
            event_type: Type of event
            data: Event data
            context_id: Context ID
        """
        ...


class MetricValue(BaseModel):
    """Value of a recorded metric.

    Attributes:
        name: Name of the metric
        type: Type of metric
        value: Current value
        timestamp: Time of recording
        labels: Additional metric labels
        metadata: Additional metadata
    """

    name: str = Field(description="Name of the metric")
    type: MetricType = Field(description="Type of metric")
    value: int | float = Field(description="Current value")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Time of recording"
    )
    labels: MetricLabels = Field(
        default_factory=dict, description="Additional metric labels"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class MetricsCollector(Protocol):
    """Protocol for metrics collection."""

    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        labels: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MetricValue:
        """Record a metric.

        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            labels: Optional metric labels
            metadata: Optional metric metadata

        Returns:
            Recorded metric value

        Raises:
            ValueError: If metric name or value is invalid
        """
        ...

    def get_metric(
        self,
        name: str,
        labels: dict[str, str] | None = None,
    ) -> MetricValue | None:
        """Get a metric value.

        Args:
            name: Metric name
            labels: Optional metric labels

        Returns:
            Metric value if found, None otherwise
        """
        ...

    def list_metrics(
        self,
        pattern: str | None = None,
        metric_type: MetricType | None = None,
        labels: dict[str, str] | None = None,
    ) -> list[MetricValue]:
        """List metrics.

        Args:
            pattern: Optional name pattern filter
            metric_type: Optional type filter
            labels: Optional metric labels

        Returns:
            List of matching metrics
        """
        ...

    def clear_metrics(
        self,
        pattern: str | None = None,
        metric_type: MetricType | None = None,
        labels: dict[str, str] | None = None,
    ) -> int:
        """Clear metrics.

        Args:
            pattern: Optional name pattern filter
            metric_type: Optional type filter
            labels: Optional metric labels

        Returns:
            Number of metrics cleared
        """
        ...

    async def export_metrics(
        self,
        format: str = "prometheus",
        pattern: str | None = None,
    ) -> str:
        """Export metrics in specified format.

        Args:
            format: Output format (prometheus, json, etc.)
            pattern: Optional name pattern filter

        Returns:
            Formatted metrics string
        """
        ...

    def counter(
        self,
        name: str,
        value: float = 1.0,
        labels: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MetricValue:
        """Record a counter metric.

        Args:
            name: Metric name
            value: Value to add to counter
            labels: Optional metric labels
            metadata: Optional metric metadata

        Returns:
            Recorded metric value
        """
        ...

    def gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MetricValue:
        """Record a gauge metric.

        Args:
            name: Metric name
            value: Current value
            labels: Optional metric labels
            metadata: Optional metric metadata

        Returns:
            Recorded metric value
        """
        ...

    def histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MetricValue:
        """Record a histogram metric.

        Args:
            name: Metric name
            value: Value to add to histogram
            labels: Optional metric labels
            metadata: Optional metric metadata

        Returns:
            Recorded metric value
        """
        ...

    def summary(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MetricValue:
        """Record a summary metric.

        Args:
            name: Metric name
            value: Value to add to summary
            labels: Optional metric labels
            metadata: Optional metric metadata

        Returns:
            Recorded metric value
        """
        ...

    def timer(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MetricValue:
        """Record a timer metric.

        Args:
            name: Metric name
            value: Duration in seconds
            labels: Optional metric labels
            metadata: Optional metric metadata

        Returns:
            Recorded metric value
        """
        ...


class AdapterConfig(BaseModel):
    """Framework adapter configuration."""

    name: str = Field(..., min_length=1)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    settings: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    events: list[EventType] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    @field_validator("settings", "metadata", "metrics")
    def validate_dicts(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate dictionary fields."""
        return dict(v)

    @classmethod
    @field_validator("events")
    def validate_events(cls, v: list[EventType]) -> list[EventType]:
        """Validate event types."""
        return sorted(set(v), key=lambda x: x.name)


@runtime_checkable
class FrameworkAdapter(Protocol):
    """Protocol for framework adapters."""

    event_bus: EventBus | None

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the adapter name."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Get the adapter version."""
        ...

    @abstractmethod
    async def initialize(self, config: AdapterConfig) -> bool:
        """Initialize the framework adapter.

        Args:
            config: Adapter configuration

        Returns:
            True if initialization successful

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If initialization fails
        """
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up framework resources.

        Raises:
            RuntimeError: If cleanup fails
        """
        ...

    @abstractmethod
    async def validate_config(self, config: AdapterConfig) -> bool:
        """Validate adapter configuration.

        Args:
            config: Configuration to validate

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        ...

    @abstractmethod
    async def record_metrics(
        self,
        operation: str,
        duration: float,
        success: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record adapter metrics.

        Args:
            operation: Operation being measured
            duration: Operation duration in seconds
            success: Whether operation succeeded
            metadata: Optional metric metadata
        """
        ...

    @abstractmethod
    async def emit_event(
        self,
        event_type: EventType,
        data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Emit an adapter event.

        Args:
            event_type: Type of event
            data: Event data
            metadata: Optional event metadata
        """
        ...


@runtime_checkable
class KeyValueStore(Protocol[K_contra, V_co]):
    """Protocol for key-value stores."""

    async def get(self, key: K_contra) -> V_co | None:
        """Get value by key.

        Args:
            key: Key to look up

        Returns:
            Value if found, None otherwise
        """
        ...

    async def set(self, key: K_contra, value: V_in) -> None:
        """Set value for key.

        Args:
            key: Key to set
            value: Value to store
        """
        ...

    async def delete(self, key: K_contra) -> None:
        """Delete value by key.

        Args:
            key: Key to delete
        """
        ...

    async def exists(self, key: K_contra) -> bool:
        """Check if key exists.

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise
        """
        ...


@runtime_checkable
class Lifecycle(Protocol):
    """Protocol for components with lifecycle management."""

    async def initialize(self) -> None:
        """Initialize the component.

        This method should be called before using the component.
        It should set up any necessary resources and put the component
        in a ready state.

        Raises:
            LifecycleError: If initialization fails
        """
        ...

    async def cleanup(self) -> None:
        """Clean up the component.

        This method should be called when the component is no longer needed.
        It should release any resources and put the component in a cleaned state.

        Raises:
            LifecycleError: If cleanup fails
        """
        ...
