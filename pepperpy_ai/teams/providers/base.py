"""Base team provider implementation."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from ...ai_types import AIResponse
from ..config import TeamConfig


class TeamProvider(ABC):
    """Base team provider implementation."""

    def __init__(self, config: TeamConfig) -> None:
        """Initialize provider."""
        self.config = config
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize provider."""
        await self._setup()
        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup provider resources."""
        await self._teardown()
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Ensure provider is initialized."""
        if not self.is_initialized:
            raise RuntimeError("Provider not initialized")

    @abstractmethod
    async def _setup(self) -> None:
        """Setup provider resources."""
        pass

    @abstractmethod
    async def _teardown(self) -> None:
        """Teardown provider resources."""
        pass

    @abstractmethod
    async def execute_task(self, task: str, **kwargs: Any) -> AIResponse:
        """Execute team task."""
        pass

    @abstractmethod
    async def get_team_members(self) -> Sequence[str]:
        """Get team member names."""
        pass

    @abstractmethod
    async def get_team_roles(self) -> dict[str, str]:
        """Get team member roles."""
        pass
