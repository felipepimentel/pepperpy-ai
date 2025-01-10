"""AI types module."""

from dataclasses import dataclass, field

from .types import AIMessage, JsonDict


@dataclass
class AIResponse:
    """AI response type."""

    content: str
    messages: list[AIMessage] = field(default_factory=list)
    metadata: JsonDict = field(default_factory=dict)
