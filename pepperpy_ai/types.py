"""Common type definitions for PepperPy AI."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Protocol, TypeAlias, Union

# Define tipos básicos para JSON
JsonValue = Union[str, int, float, bool, None, list[Any], dict[str, Any]]
JsonDict: TypeAlias = dict[str, JsonValue]

class MessageRole(Enum):
    """Role of a message in a conversation."""

    SYSTEM = auto()
    USER = auto()
    ASSISTANT = auto()


@dataclass
class Message:
    """A message in a conversation.
    
    Attributes:
        role: The role of the message sender
        content: The message content
        metadata: Optional metadata associated with the message
    """

    role: MessageRole
    content: str
    metadata: JsonDict | None = None


class Serializable(Protocol):
    """Protocol for serializable objects."""

    def to_dict(self) -> JsonDict:
        """Convert object to dictionary.
        
        Returns:
            Dictionary representation of the object
        """
        ...
