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
from datetime import UTC, datetime
from enum import Enum, auto
from typing import (
    Any,
    ClassVar,
    Dict,
    Generic,
    List,
    Literal,
    NewType,
    Protocol,
    TypedDict,
    TypeVar,
    runtime_checkable,
)
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

# Type variables for generic implementations
T = TypeVar("T")
T_Input = TypeVar("T_Input")  # Input data type
T_Output = TypeVar("T_Output")  # Output data type
T_Config = TypeVar("T_Config", bound=Dict[str, Any])  # Configuration type
T_Context = TypeVar("T_Context")  # Context type
V = TypeVar("V")

# Type aliases for common types
MetadataValue = str | int | float | bool | None | list[str] | dict[str, str]  # type: ignore[valid-type]
MetadataDict = dict[str, MetadataValue]  # type: ignore[valid-type]

# Research-specific types
ResearchDepth = Literal["basic", "comprehensive", "deep"]
ResearchFocus = Literal["general", "academic", "industry", "technical", "business"]


class ResearchResults(BaseModel):
    """Results from a research operation.

    Attributes
    ----------
        topic: Research topic
        summary: Summary of findings
        sources: List of sources used
        confidence: Confidence score (0-1)
        metadata: Additional metadata

    """

    topic: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    sources: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model configuration."""

        frozen = True

    @field_validator("sources")
    @classmethod
    def validate_sources(cls, v: List[str]) -> List[str]:
        """Validate source URLs."""
        return [src.strip() for src in v if src.strip()]

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure metadata is immutable."""
        return dict(v)


class MessageType(str, Enum):
    """Types of messages that can be exchanged."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    COMMAND = "command"
    RESPONSE = "response"


class MessageContent(TypedDict):
    """Content of a message."""

    type: MessageType
    content: Dict[str, Any]


class Message(BaseModel):
    """A message that can be exchanged between components."""

    id: str
    type: MessageType
    content: Dict[str, Any]


class ResponseStatus(str, Enum):
    """Status of a response."""

    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"


class AgentState(Enum):
    """Represents the possible states of an agent."""

    CREATED = auto()
    INITIALIZING = auto()
    READY = auto()
    PROCESSING = auto()
    CLEANING = auto()
    TERMINATED = auto()
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


class MetricType(Enum):
    """Types of metrics that can be collected."""

    COUNTER = auto()
    GAUGE = auto()
    HISTOGRAM = auto()
    SUMMARY = auto()
    TIMER = auto()  # Added for completeness, but not used in the original file


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


class Response(BaseModel):
    """A response from the system."""

    id: UUID = Field(default_factory=uuid4)
    message_id: str
    content: MessageContent
    status: ResponseStatus = ResponseStatus.SUCCESS


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

    @field_validator("capabilities")
    @classmethod
    def validate_capabilities(cls, v: list[str]) -> list[str]:
        """Validate capability names."""
        return [cap.strip() for cap in v if cap.strip()]

    @field_validator("settings", "metadata")
    @classmethod
    def validate_dicts(cls, v: dict[str, Any]) -> dict[str, Any]:
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

    @field_validator("settings", "metadata")
    @classmethod
    def validate_dicts(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure dictionaries are immutable."""
        return dict(v)


class ProviderConfig(BaseModel):
    """Configuration for a provider."""

    provider_type: str = Field(default="openai", min_length=1)
    name: str = Field(default="default", min_length=1)
    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    api_key: str | None = Field(None, min_length=1)
    base_url: str | None = Field(None, min_length=1)
    model: str = Field(default="gpt-4-turbo-preview")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=1000)
    timeout: int = Field(default=30)
    max_retries: int = Field(default=3)
    settings: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model configuration."""

        frozen = True

    @field_validator("api_key", "base_url")
    @classmethod
    def validate_optional_strings(cls, v: str | None) -> str | None:
        """Validate optional string fields."""
        if v is not None and not v.strip():
            raise ValueError("Value cannot be empty")
        return v

    @field_validator("settings", "metadata")
    @classmethod
    def validate_dicts(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure dictionaries are immutable."""
        return dict(v)


class AgentContext(BaseModel):
    """Context for agent execution."""

    agent_id: UUID = Field(default_factory=uuid4)
    session_id: UUID = Field(default_factory=uuid4)
    parent_id: UUID | None = Field(None)
    state: AgentState = Field(default=AgentState.CREATED)
    settings: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Last update timestamp",
    )

    class Config:
        """Pydantic model configuration."""

        frozen = True
        json_encoders: ClassVar[dict[type, Any]] = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            AgentState: lambda v: v.value,
        }

    @field_validator("settings", "metadata")
    @classmethod
    def validate_dicts(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure dictionaries are immutable."""
        return dict(v)


@dataclass
class Context(Generic[V]):
    """Base context class for managing key-value data.

    Args:
    ----
        data: Initial key-value pairs.

    """

    _data: dict[str, V]

    def __init__(self, **kwargs: V) -> None:
        """Initialize context.

        Args:
        ----
            **kwargs: Initial key-value pairs.

        """
        self._data = kwargs

    def get(self, key: str, default: V | None = None) -> V | None:
        """Get value from context.

        Args:
        ----
            key: Key to get.
            default: Default value if key not found.

        Returns:
        -------
            Value for key or default if not found.

        """
        return self._data.get(key, default)

    def set(self, key: str, value: V) -> None:
        """Set value in context.

        Args:
        ----
            key: Key to set.
            value: Value to set.

        """
        self._data[key] = value

    def update(self, **kwargs: V) -> None:
        """Update context with new values.

        Args:
        ----
            **kwargs: Key-value pairs to update.

        """
        self._data.update(kwargs)

    def __getitem__(self, key: str) -> V:
        """Get value from context.

        Args:
        ----
            key: Key to get.

        Returns:
        -------
            Value for key.

        Raises:
        ------
            KeyError: If key not found.

        """
        return self._data[key]

    def __setitem__(self, key: str, value: V) -> None:
        """Set value in context.

        Args:
        ----
            key: Key to set.
            value: Value to set.

        """
        self._data[key] = value


@dataclass
class Result(Generic[T]):
    """Result of an operation.

    Attributes
    ----------
        value: The operation result value
        success: Whether the operation succeeded
        error: Optional error if operation failed

    """

    value: T
    success: bool = True
    error: Exception | None = None


# Type alias for resource identifiers
ResourceId = NewType("ResourceId", str)


class PepperpyClientProtocol(Protocol):
    """Protocol defining the interface for PepperpyClient."""

    async def send_message(self, message: str) -> str:
        """Send a message and get a response."""
        ...

    async def get_agent(self, agent_type: str) -> Any:
        """Get an agent instance."""
        ...


# Type aliases for better readability
HookCallbackType = "Callable[['PepperpyClient'], None]"  # type: ignore
AgentFactoryType = "Callable[[str, AgentContext, Dict[str, Any]], BaseAgent]"  # type: ignore

# Re-export provider types
__all__ = [
    "Message",
    "MessageType",
    "MessageContent",
    "Response",
    "ResponseStatus",
    "AgentState",
    "AgentCapability",
    "AgentConfig",
    "AgentContext",
    "ProviderConfig",
    "ComponentConfig",
    "Context",
    "Result",
    "ResourceId",
    "PepperpyClientProtocol",
]
