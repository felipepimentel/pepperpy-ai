"""LLM types module."""

from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    """Message role types."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """Chat message."""

    role: Role
    content: str


@dataclass
class LLMResponse:
    """LLM response."""

    content: str
    model: str | None = None
    provider: str | None = None
    metadata: dict[str, str | int | float | bool | None] | None = None


AIResponse = LLMResponse  # Alias para compatibilidade
