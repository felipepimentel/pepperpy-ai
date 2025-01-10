"""Chat type definitions."""

from dataclasses import dataclass, field
from enum import Enum

from ..config.base import JsonDict


class ChatRole(str, Enum):
    """Chat role types."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class ChatMessage:
    """Chat message."""

    role: ChatRole
    content: str
    name: str | None = None
    metadata: JsonDict = field(default_factory=dict)


@dataclass
class ChatHistory:
    """Chat history."""

    messages: list[ChatMessage] = field(default_factory=list)
    metadata: JsonDict = field(default_factory=dict)
