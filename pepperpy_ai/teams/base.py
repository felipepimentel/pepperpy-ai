"""Base team implementation."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Sequence
from typing import Any, List, Optional, Protocol, runtime_checkable

from ..ai_types import Message
from ..exceptions import ProviderError
from ..responses import AIResponse
from .config import TeamConfig


@runtime_checkable
class BaseTeam(Protocol):
    """Base team protocol."""

    def __init__(self, config: TeamConfig) -> None:
        """Initialize team.

        Args:
            config: Team configuration
        """
        ...

    @property
    def is_initialized(self) -> bool:
        """Check if team is initialized."""
        ...

    async def initialize(self) -> None:
        """Initialize team."""
        ...

    async def cleanup(self) -> None:
        """Cleanup team resources."""
        ...

    async def execute_task(self, task: str, **kwargs: Any) -> AIResponse:
        """Execute team task."""
        ...

    async def get_team_members(self) -> Sequence[str]:
        """Get team members."""
        ...

    async def get_team_roles(self) -> dict[str, str]:
        """Get team roles."""
        ...


class BaseTeamProvider(ABC):
    """Base team provider implementation."""

    def __init__(self, config: TeamConfig) -> None:
        """Initialize provider.

        Args:
            config: Team configuration
        """
        self.config = config
        self._client = config.settings.get("client")
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize provider."""
        if not self._initialized:
            await self._setup()
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup provider resources."""
        if self._initialized:
            await self._teardown()
            self._initialized = False

    def _ensure_initialized(self) -> None:
        """Ensure provider is initialized."""
        if not self._initialized:
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
    async def stream(
        self,
        messages: List[Message],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from the provider.

        Args:
            messages: List of messages to send to provider
            model: Optional model to use
            temperature: Optional temperature parameter
            max_tokens: Optional maximum tokens parameter

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            ProviderError: If provider is not initialized
        """
        if not self.is_initialized:
            raise ProviderError("Provider not initialized", provider="base")
        yield AIResponse(content="Not implemented")

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
