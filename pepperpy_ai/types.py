"""Common type definitions for PepperPy AI."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, Optional


class MessageRole(Enum):
    """Role of a message in a conversation."""

    SYSTEM = auto()
    USER = auto()
    ASSISTANT = auto()


@dataclass
class Message:
    """A message in a conversation."""

    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AIResponse:
    """Response from an AI provider."""

    content: str
    metadata: Optional[Dict[str, Any]] = None
