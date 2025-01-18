"""Agent type definitions."""

from dataclasses import dataclass
from typing import Any


@dataclass
class AgentConfig:
    """Agent configuration."""

    name: str
    type: str
    model: str
    temperature: float = 0.7
    max_tokens: int | None = None
    stop_sequences: list[str] | None = None
    model_kwargs: dict[str, Any] | None = None


@dataclass
class AgentResponse:
    """Agent response with metadata."""

    text: str
    metadata: dict[str, Any] | None = None
