"""LLM types module"""

from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    """Message role types"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """Chat message"""

    role: Role
    content: str


@dataclass
class LLMResponse:
    """LLM response"""

    content: str
    role: Role
    model: str
    usage: dict[str, int]


AIResponse = LLMResponse  # Alias para compatibilidade
