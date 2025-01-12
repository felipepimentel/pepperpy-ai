"""Base team provider module."""

from abc import ABC, abstractmethod

from ...config.team import TeamConfig
from ...responses import AIResponse
from ..base import BaseTeam
from ..interfaces import ToolParams


class BaseTeamProvider(BaseTeam, ABC):
    """Base team provider implementation."""

    def __init__(self, config: TeamConfig) -> None:
        """Initialize provider.

        Args:
            config: Team configuration.
        """
        super().__init__(config)

    @abstractmethod
    async def execute_task(self, task: str, **kwargs: ToolParams) -> AIResponse:
        """Execute team task.

        Args:
            task: Task to execute.
            **kwargs: Additional task parameters.

        Returns:
            AIResponse: Task execution response.
        """
        pass
