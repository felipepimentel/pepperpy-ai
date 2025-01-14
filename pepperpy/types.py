"""Type definitions module."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal, NotRequired, TypedDict, cast

# Type aliases
type JsonDict = dict[str, Any]
type JsonValue = Any
type ToolParams = dict[str, Any]
type Role = MessageRole


class MessageRole(str, Enum):
    """Message role enumeration."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"

    @classmethod
    def from_str(cls, value: str) -> "MessageRole":
        """Create message role from string.

        Args:
            value: String value.

        Returns:
            MessageRole: Message role.

        Raises:
            ValueError: If value is not a valid message role.
        """
        try:
            return cls(value.lower())
        except ValueError as err:
            raise ValueError(f"Invalid message role: {value}") from err

    def __str__(self) -> str:
        """Convert message role to string.

        Returns:
            str: String representation.
        """
        return self.value


# Message types
class Message(TypedDict):
    """Base message type."""

    role: Literal["user", "assistant", "system", "function", "tool"]
    content: str
    name: NotRequired[str]
    function_call: NotRequired[dict[str, Any]]
    tool_calls: NotRequired[list[dict[str, Any]]]


@dataclass
class BaseResponse:
    """Base response type with common fields."""

    id: str
    created: int
    model: str
    role: MessageRole
    content: str


@dataclass
class ChatMessage:
    """Structured chat message."""

    role: MessageRole
    content: str
    name: str | None = None
    tool_calls: list["ToolCall"] | None = None
    tool_call_id: str | None = None


# Function and tool types
@dataclass
class FunctionDefinition:
    """Function definition."""

    name: str
    description: str
    parameters: dict[str, Any]


@dataclass
class FunctionCall:
    """Function call."""

    name: str
    arguments: dict[str, Any]


@dataclass
class ToolCall:
    """Tool call."""

    id: str
    type: str
    function: FunctionCall


@dataclass
class Tool:
    """Tool definition."""

    function: FunctionDefinition


# Response types
class ChatResponseFormat(str, Enum):
    """Chat response format."""

    TEXT = "text"
    JSON = "json"


@dataclass
class ChatResponse(BaseResponse):
    """Chat response with token information."""

    tool_calls: list[ToolCall] | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass
class ChatResponseChunk(BaseResponse):
    """Streaming chat response chunk."""

    tool_calls: list[ToolCall] | None = None


# Configuration types
@dataclass
class BaseConfig:
    """Base configuration class.

    Attributes:
        name: Configuration name.
        version: Configuration version.
        enabled: Whether configuration is enabled.
        metadata: Additional metadata.
        settings: Additional settings.
    """

    name: str
    version: str
    enabled: bool = True
    metadata: JsonDict = field(default_factory=dict)
    settings: dict[str, Any] | None = None

    def to_dict(self) -> JsonDict:
        """Convert configuration to dictionary.

        Returns:
            JsonDict: Dictionary representation.
        """
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "metadata": self.metadata,
            "settings": self.settings,
        }

    @classmethod
    def from_dict(cls, data: JsonDict) -> "BaseConfig":
        """Create configuration from dictionary.

        Args:
            data: Dictionary data.

        Returns:
            BaseConfig: Configuration instance.
        """
        name = cast(str, data["name"])
        version = cast(str, data["version"])
        enabled = cast(bool, data.get("enabled", True))
        metadata = cast(JsonDict, data.get("metadata", {}))
        settings = cast(dict[str, Any] | None, data.get("settings"))

        return cls(
            name=name,
            version=version,
            enabled=enabled,
            metadata=metadata,
            settings=settings,
        )


@dataclass
class CapabilityConfig(BaseConfig):
    """Configuration for capabilities.

    This class provides configuration options for capabilities, including
    model settings, resource limits, and other parameters that control
    capability behavior.

    Attributes:
        model: Model name or path.
        max_retries: Maximum number of retries.
        retry_delay: Delay between retries in seconds.
        timeout: Operation timeout in seconds.
        batch_size: Batch size for operations.
        api_key: API key for authentication.
        api_base: Base URL for API requests.
        api_version: API version to use.
        organization_id: Organization ID for API requests.
    """

    model: str | None = None
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0
    batch_size: int = 32
    api_key: str | None = None
    api_base: str | None = None
    api_version: str | None = None
    organization_id: str | None = None
