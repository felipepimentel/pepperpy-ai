"""Common type definitions for PepperPy AI."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, Optional, Protocol


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
    metadata: Optional[Dict[str, Any]] = None


class JsonDict(Dict[str, Any]):
    """Type alias for JSON-like dictionaries."""


class Serializable(Protocol):
    """Protocol for serializable objects."""

    def to_dict(self) -> JsonDict:
        """Convert object to dictionary.
        
        Returns:
            Dictionary representation of the object
        """
        ...
