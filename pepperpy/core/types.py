"""Core type definitions for the Pepperpy framework.

This module provides a comprehensive type system for the framework, including:
- Message and event types
- Configuration and context types
- Agent and component types
- Capability and permission types
- Metric and monitoring types
- Memory and storage types
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import (
    Any,
    ClassVar,
    Generic,
    NewType,
    Protocol,
    TypeVar,
    runtime_checkable,
)
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

# Type variables for generic implementations
T = TypeVar("T")
T_Input = TypeVar("T_Input")  # Input data type
T_Output = TypeVar("T_Output")  # Output data type
T_Config = TypeVar("T_Config", bound=BaseModel)  # Configuration type
T_Context = TypeVar("T_Context", bound=BaseModel)  # Context type


class MessageType(str, Enum):
    """Types of messages in the system."""

    COMMAND = "command"  # Command messages
    QUERY = "query"  # Query messages
    RESPONSE = "response"  # Response messages
    EVENT = "event"  # Event messages
    ERROR = "error"  # Error messages


class ResponseStatus(str, Enum):
    """Possible response statuses."""

    SUCCESS = "success"  # Operation succeeded
    ERROR = "error"  # Operation failed
    PENDING = "pending"  # Operation in progress
    CANCELLED = "cancelled"  # Operation cancelled


class AgentState(Enum):
    """Represents the possible states of an agent."""

    INITIALIZED = auto()
    STARTING = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPING = auto()
    STOPPED = auto()
    ERROR = auto()


class MemoryScope(str, Enum):
    """Scope of memory storage."""

    SESSION = "session"  # Persists for session duration
    AGENT = "agent"  # Persists for agent lifetime
    GLOBAL = "global"  # Persists globally


class MemoryBackend(str, Enum):
    """Supported memory backend types."""

    DICT = "dict"  # In-memory dictionary
    REDIS = "redis"  # Redis backend
    SQLITE = "sqlite"  # SQLite backend
    POSTGRES = "postgres"  # PostgreSQL backend


class ToolPermission(str, Enum):
    """Tool permission levels."""

    READ = "read"  # Read-only access
    WRITE = "write"  # Write access
    EXECUTE = "exec"  # Execution access
    ADMIN = "admin"  # Administrative access


class ToolScope(str, Enum):
    """Tool scope levels."""

    AGENT = "agent"  # Agent-specific scope
    SESSION = "session"  # Session-specific scope
    GLOBAL = "global"  # Global scope


class MetricType(str, Enum):
    """Types of metrics."""

    COUNTER = "counter"  # Monotonically increasing counter
    GAUGE = "gauge"  # Value that can go up and down
    HISTOGRAM = "histogram"  # Distribution of values
    SUMMARY = "summary"  # Statistical summary
    TIMER = "timer"  # Duration measurements


class ErrorCategory(str, Enum):
    """Categories of errors in the system."""

    CONFIGURATION = "configuration"  # Configuration-related errors
    VALIDATION = "validation"  # Input/data validation errors
    PROVIDER = "provider"  # Provider-related errors
    MEMORY = "memory"  # Memory system errors
    SECURITY = "security"  # Security-related errors
    RUNTIME = "runtime"  # Runtime errors
    SYSTEM = "system"  # System-level errors
    NETWORK = "network"  # Network-related errors
    RESOURCE = "resource"  # Resource management errors
    UNKNOWN = "unknown"  # Uncategorized errors


class Message(BaseModel):
    """Represents a message in the system."""

    id: UUID = Field(default_factory=uuid4, description="Unique message identifier")
    type: MessageType = Field(..., description="Type of message")
    sender: str = Field(..., description="Message sender identifier")
    receiver: str | None = Field(None, description="Message receiver identifier")
    content: dict[str, Any] = Field(..., description="Message content")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Message metadata"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Message timestamp"
    )

    class Config:
        """Pydantic model configuration."""

        frozen = True
        json_encoders: ClassVar[dict[Any, Any]] = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            MessageType: lambda v: v.value,
        }

    @validator("sender", "receiver")
    def validate_identifiers(self, v: str | None) -> str | None:
        """Validate sender and receiver identifiers."""
        if v is not None and not v.strip():
            raise ValueError("Identifier cannot be empty")
        return v

    @validator("content", "metadata")
    def validate_dicts(self, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure dictionaries are immutable."""
        return dict(v)


class Response(BaseModel):
    """Represents a response in the system."""

    id: UUID = Field(default_factory=uuid4, description="Unique response identifier")
    message_id: UUID = Field(..., description="ID of the message being responded to")
    status: ResponseStatus = Field(..., description="Response status")
    content: dict[str, Any] = Field(..., description="Response content")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Response metadata"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )

    class Config:
        """Pydantic model configuration."""

        frozen = True
        json_encoders: ClassVar[dict[Any, Any]] = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            ResponseStatus: lambda v: v.value,
        }

    @validator("content", "metadata")
    def validate_dicts(self, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure dictionaries are immutable."""
        return dict(v)


@runtime_checkable
class AgentCapability(Protocol):
    """Protocol defining agent capabilities.

    This protocol defines the interface that all agent capabilities must
    implement. Capabilities provide additional functionality to agents.
    """

    name: str
    version: str
    description: str
    requirements: list[str]

    def is_available(self) -> bool:
        """Check if the capability is available in current environment."""
        ...

    async def initialize(self, config: dict[str, Any]) -> None:
        """Initialize the capability with configuration."""
        ...

    async def cleanup(self) -> None:
        """Cleanup capability resources."""
        ...

    @property
    def is_initialized(self) -> bool:
        """Check if the capability is initialized."""
        ...


class AgentConfig(BaseModel):
    """Configuration for creating an agent."""

    type: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    capabilities: list[str] = Field(default_factory=list)
    settings: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model configuration."""

        frozen = True
        json_encoders: ClassVar[dict[type, Any]] = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            AgentState: lambda v: v.value,
        }

    @validator("capabilities")
    def validate_capabilities(self, v: list[str]) -> list[str]:
        """Validate capability names."""
        return [cap.strip() for cap in v if cap.strip()]

    @validator("settings", "metadata")
    def validate_dicts(self, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure dictionaries are immutable."""
        return dict(v)


class ComponentConfig(BaseModel):
    """Configuration for creating a system component."""

    type: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    settings: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model configuration."""

        frozen = True

    @validator("settings", "metadata")
    def validate_dicts(self, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure dictionaries are immutable."""
        return dict(v)


class ProviderConfig(BaseModel):
    """Configuration for a provider."""

    type: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    api_key: str | None = Field(None, min_length=1)
    base_url: str | None = Field(None, min_length=1)
    settings: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model configuration."""

        frozen = True

    @validator("api_key", "base_url")
    def validate_optional_strings(self, v: str | None) -> str | None:
        """Validate optional string fields."""
        if v is not None and not v.strip():
            raise ValueError("Value cannot be empty")
        return v

    @validator("settings", "metadata")
    def validate_dicts(self, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure dictionaries are immutable."""
        return dict(v)


class AgentContext(BaseModel):
    """Context for agent execution."""

    agent_id: UUID = Field(default_factory=uuid4)
    session_id: UUID = Field(default_factory=uuid4)
    parent_id: UUID | None = Field(None)
    state: AgentState = Field(default=AgentState.INITIALIZED)
    settings: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic model configuration."""

        frozen = True
        json_encoders: ClassVar[dict[type, Any]] = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            AgentState: lambda v: v.value,
        }

    @validator("settings", "metadata")
    def validate_dicts(self, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure dictionaries are immutable."""
        return dict(v)


class Context:
    """Context for operations.

    A context object that carries request-scoped values.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize context.

        Args:
            **kwargs: Initial context values
        """
        self._data: dict[str, Any] = kwargs

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from context.

        Args:
            key: Context key
            default: Default value if key not found

        Returns:
            Value from context or default
        """
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set value in context.

        Args:
            key: Context key
            value: Value to set
        """
        self._data[key] = value

    def update(self, **kwargs: Any) -> None:
        """Update context with new values.

        Args:
            **kwargs: Values to update
        """
        self._data.update(kwargs)

    def clear(self) -> None:
        """Clear all values from context."""
        self._data.clear()

    def __contains__(self, key: str) -> bool:
        """Check if key exists in context.

        Args:
            key: Context key

        Returns:
            True if key exists, False otherwise
        """
        return key in self._data

    def __getitem__(self, key: str) -> Any:
        """Get value from context.

        Args:
            key: Context key

        Returns:
            Value from context

        Raises:
            KeyError: If key not found
        """
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set value in context.

        Args:
            key: Context key
            value: Value to set
        """
        self._data[key] = value


@dataclass
class Result(Generic[T]):
    """Result of an operation.

    Attributes:
        value: The operation result value
        success: Whether the operation succeeded
        error: Optional error if operation failed
    """

    value: T
    success: bool = True
    error: Exception | None = None


# Type alias for resource identifiers
ResourceId = NewType("ResourceId", str)
