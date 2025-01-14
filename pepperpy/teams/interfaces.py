"""Team interfaces module."""

from abc import ABC, abstractmethod
from typing import TypedDict

from ..responses import AIResponse


class ToolParams(TypedDict, total=False):
    """Tool parameters."""

    model: str | None
    temperature: float | None
    max_tokens: int | None
    top_p: float | None
    frequency_penalty: float | None
    presence_penalty: float | None
    timeout: float | None


class TeamResult(TypedDict, total=False):
    """Team result."""

    content: str
    metadata: dict[str, str | None]


class TeamTool(ABC):
    """Team tool interface."""

    @abstractmethod
    async def execute(self, **kwargs: ToolParams) -> TeamResult:
        """Execute tool."""
        ...


class TeamAgent(ABC):
    """Team agent interface."""

    @abstractmethod
    async def execute_task(self, task: str, **kwargs: ToolParams) -> TeamResult:
        """Execute task."""
        ...


class TeamProvider(ABC):
    """Team provider interface."""

    @abstractmethod
    async def execute_task(self, task: str, **kwargs: ToolParams) -> AIResponse:
        """Execute team task."""
        pass
