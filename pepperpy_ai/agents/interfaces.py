"""Agent interfaces module."""

from typing import Protocol, TypedDict

from ..ai_types import AIResponse


class AgentKwargs(TypedDict, total=False):
    """Type hints for agent kwargs."""
    temperature: float
    max_tokens: int
    model: str

class Agent(Protocol):
    """Agent protocol."""

    async def execute(self, task: str, **kwargs: AgentKwargs) -> AIResponse:
        """Execute agent task."""
        ...
