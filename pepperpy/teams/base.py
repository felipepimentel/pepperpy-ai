"""Base team module."""

from abc import ABC, abstractmethod

from ..config.team import TeamConfig
from ..responses import AIResponse
from .interfaces import ToolParams


class BaseTeam(ABC):
    """Base team implementation."""

    def __init__(self, config: TeamConfig) -> None:
        """Initialize team.

        Args:
            config: Team configuration.
        """
        self._config = config
        self._initialized = False

    @property
    def config(self) -> TeamConfig:
        """Get team configuration.

        Returns:
            TeamConfig: Team configuration.
        """
        return self._config

    @property
    def is_initialized(self) -> bool:
        """Check if team is initialized.

        Returns:
            bool: True if team is initialized, False otherwise.
        """
        return self._initialized

    async def initialize(self) -> None:
        """Initialize team."""
        if not self._initialized:
            self._initialized = True

    async def cleanup(self) -> None:
        """Clean up team resources."""
        if self._initialized:
            self._initialized = False

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
