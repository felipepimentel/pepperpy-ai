"""AI types module."""

from dataclasses import dataclass, field
from enum import Enum

from .types import JsonDict
from .types import Message as AIMessage


class MessageRole(str, Enum):
    """Role of a message in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class Message:
    """A message in a conversation."""
    role: MessageRole
    content: str
    name: str | None = None
    function_call: dict | None = None


@dataclass
class AIResponse:
    """AI response type."""

    content: str
    messages: list[AIMessage] = field(default_factory=list)
    metadata: JsonDict = field(default_factory=dict)
