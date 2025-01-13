"""AI types module."""

from dataclasses import dataclass
from enum import Enum


class MessageRole(str, Enum):
    """Message role."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class Message:
    """Message type."""

    role: MessageRole
    content: str
    name: str | None = None
