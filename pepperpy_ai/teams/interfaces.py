"""Team interfaces."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from ..ai_types import AIResponse
from .config import TeamResult


@runtime_checkable
class TeamTool(Protocol):
    """Team tool protocol."""

    @property
    def name(self) -> str:
        """Get tool name."""
        ...

    @property
    def description(self) -> str:
        """Get tool description."""
        ...

    async def execute(self, **kwargs: Any) -> TeamResult:
        """Execute tool."""
        ...


@runtime_checkable
class TeamAgent(Protocol):
    """Team agent protocol."""

    @property
    def name(self) -> str:
        """Get agent name."""
        ...

    @property
    def role(self) -> str:
        """Get agent role."""
        ...

    async def execute_task(self, task: str, **kwargs: Any) -> TeamResult:
        """Execute task."""
        ...

    async def get_tools(self) -> Sequence[TeamTool]:
        """Get available tools."""
        ...


class BaseTeamInterface(ABC):
    """Base team interface."""

    @abstractmethod
    async def execute_task(self, task: str, **kwargs: Any) -> AIResponse:
        """Execute team task."""
        pass

    @abstractmethod
    async def get_team_members(self) -> Sequence[str]:
        """Get team members."""
        pass

    @abstractmethod
    async def get_team_roles(self) -> dict[str, str]:
        """Get team roles."""
        pass
