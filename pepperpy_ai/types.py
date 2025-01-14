"""Type definitions module."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, NotRequired, TypedDict


class Role(str, Enum):
    """Message role."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
    FUNCTION = "function"


class Message(TypedDict):
    """Message type."""

    role: Literal["user", "assistant", "system", "function"]
    content: str
    name: NotRequired[str]
    function_call: NotRequired[dict[str, Any]]
    tool_calls: NotRequired[list[dict[str, Any]]]


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
    """Tool."""

    function: FunctionDefinition


class ChatResponseFormat(str, Enum):
    """Chat response format."""

    TEXT = "text"
    JSON = "json"


@dataclass
class ChatMessage:
    """Chat message."""

    role: Role
    content: str
    name: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None


@dataclass
class ChatResponse:
    """Chat response."""

    id: str
    created: int
    model: str
    role: Role
    content: str
    tool_calls: list[ToolCall] | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass
class ChatResponseChunk:
    """Chat response chunk."""

    id: str
    created: int
    model: str
    role: Role | None
    content: str
    tool_calls: list[ToolCall] | None = None


JsonDict = dict[str, Any]
JsonValue = Any
MessageRole = Role
