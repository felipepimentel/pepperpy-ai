"""Autogen team provider module."""

from typing import Any, cast

from pepperpy.responses import ResponseData, ResponseMetadata
from pepperpy.teams.config import TeamConfig
from pepperpy.teams.providers.base import BaseTeamProvider
from pepperpy.types.params import ToolParams


class AutogenTeamProvider(BaseTeamProvider):
    """Autogen team provider."""

    def __init__(self, config: TeamConfig) -> None:
        """Initialize autogen team provider.

        Args:
            config: Team configuration.
        """
        super().__init__()
        self._config = config

    @property
    def config(self) -> TeamConfig:
        """Get provider configuration.

        Returns:
            TeamConfig: Provider configuration.
        """
        return self._config

    async def execute_task(self, task: str, **kwargs: ToolParams) -> ResponseData:
        """Execute team task.

        Args:
            task: Task to execute.
            **kwargs: Additional arguments.

        Returns:
            ResponseData: Task execution result.
        """
        return ResponseData(
            content=f"Executing task: {task}",
            metadata=ResponseMetadata(provider=self.config.provider),
        )
