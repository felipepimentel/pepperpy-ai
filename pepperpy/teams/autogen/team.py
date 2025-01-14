"""Autogen team implementation."""

from typing import cast

from ...config.team import TeamConfig
from ...responses import ResponseData, ResponseMetadata
from ..base import BaseTeam
from ..interfaces import ToolParams


class AutogenTeam(BaseTeam):
    """Autogen team implementation."""

    def __init__(self, config: TeamConfig) -> None:
        """Initialize team.

        Args:
            config: Team configuration.
        """
        super().__init__(config)

    async def execute_task(self, task: str, **kwargs: ToolParams) -> ResponseData:
        """Execute team task.

        Args:
            task: Task to execute.
            **kwargs: Additional task parameters.

        Returns:
            ResponseData: Task execution response.
        """
        if not self.is_initialized:
            raise RuntimeError("Team not initialized")

        return ResponseData(
            content=f"Executing task: {task}",
            metadata=cast(
                ResponseMetadata,
                {
                    "model": self.config.model,
                    "provider": "autogen",
                    "usage": {"total_tokens": 0},
                    "finish_reason": "stop",
                },
            ),
        )