"""Base team provider module."""

from abc import ABC, abstractmethod

from ...responses import ResponseData
from ..interfaces import TeamProvider, ToolParams


class BaseTeamProvider(TeamProvider, ABC):
    """Base team provider implementation."""

    def __init__(self) -> None:
        """Initialize provider."""
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized.

        Returns:
            bool: True if provider is initialized, False otherwise.
        """
        return self._initialized

    async def initialize(self) -> None:
        """Initialize provider."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        self._initialized = False

    @abstractmethod
    async def execute_task(self, task: str, **kwargs: ToolParams) -> ResponseData:
        """Execute team task.

        Args:
            task: Task to execute.
            **kwargs: Additional task parameters.

        Returns:
            ResponseData: Task execution response.
        """
        pass
