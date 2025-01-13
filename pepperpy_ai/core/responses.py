"""Response types module."""

from dataclasses import dataclass
from typing import Any

from ..types import JsonDict


@dataclass
class ResponseMetadata:
    """Response metadata."""

    model: str | None = None
    provider: str | None = None
    usage: dict[str, Any] | None = None
    finish_reason: str | None = None


@dataclass
class AIResponse:
    """AI response."""

    content: str
    metadata: ResponseMetadata | None = None

    def to_dict(self) -> JsonDict:
        """Convert response to dictionary."""
        return {
            "content": self.content,
            "metadata": self.metadata.__dict__ if self.metadata else {},
        }
