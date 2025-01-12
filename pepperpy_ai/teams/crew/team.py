"""Crew team implementation."""

from typing import cast

from ...config.team import TeamConfig
from ...responses import AIResponse, ResponseMetadata
from ..base import BaseTeam
from ..interfaces import ToolParams


class CrewTeam(BaseTeam):
    """Crew team implementation."""

    def __init__(self, config: TeamConfig) -> None:
        """Initialize team.

        Args:
            config: Team configuration.
        """
        super().__init__(config)

    async def execute_task(self, task: str, **kwargs: ToolParams) -> AIResponse:
        """Execute team task.

        Args:
            task: Task to execute.
            **kwargs: Additional task parameters.

        Returns:
            AIResponse: Task execution response.
        """
        if not self.is_initialized:
            raise RuntimeError("Team not initialized")

        return AIResponse(
            content=f"Executing task: {task}",
            metadata=cast(ResponseMetadata, {
                "model": self.config.model,
                "provider": "crew",
                "usage": {"total_tokens": 0},
                "finish_reason": "stop",
            }),
        )
