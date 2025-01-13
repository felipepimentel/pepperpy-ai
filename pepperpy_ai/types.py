"""Type definitions."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

# Type aliases for JSON values
JsonValue = str | int | float | bool | None | list[Any] | dict[str, Any]
JsonDict = dict[str, str | int | float | bool | None | list[Any] | dict[str, Any]]


class MessageRole(str, Enum):
    """Message role enum."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class Message:
    """Message type."""

    content: str
    role: MessageRole
    metadata: JsonDict | None = None

    def to_dict(self) -> JsonDict:
        """Convert message to dictionary."""
        return {
            "content": self.content,
            "role": self.role.value,
            "metadata": self.metadata or {},
        }


__all__ = ["JsonDict", "JsonValue", "Message", "MessageRole"]
