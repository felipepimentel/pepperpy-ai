"""AI types module."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .types import Message as AIMessage, JsonDict


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
    name: Optional[str] = None
    function_call: Optional[dict] = None


@dataclass
class AIResponse:
    """AI response type."""

    content: str
    messages: list[AIMessage] = field(default_factory=list)
    metadata: JsonDict = field(default_factory=dict)
