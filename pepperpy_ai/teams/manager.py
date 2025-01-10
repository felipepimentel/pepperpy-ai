"""Team manager implementation."""

from collections.abc import Sequence
from typing import Any

from ..exceptions import ConfigError
from .base import BaseTeam
from .config import TeamConfig
from .providers.autogen import AutogenTeamProvider
from .providers.langchain import LangchainTeamProvider

# Map of provider names to their implementations
PROVIDERS: dict[str, type[BaseTeam]] = {
    "autogen": AutogenTeamProvider,
    "langchain": LangchainTeamProvider,
}


class TeamManager:
    """Team manager implementation."""

    def __init__(self, client: Any) -> None:
        """Initialize team manager.

        Args:
            client: AI client instance
        """
        self._client = client
        self._teams: dict[str, BaseTeam] = {}
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if manager is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize manager."""
        if not self._initialized:
            if not self._client.is_initialized:
                await self._client.initialize()
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup manager resources."""
        if self._initialized:
            for team in self._teams.values():
                await team.cleanup()
            self._teams.clear()
            self._initialized = False

    def _ensure_initialized(self) -> None:
        """Ensure manager is initialized."""
        if not self._initialized:
            raise RuntimeError("Manager not initialized")

    async def create_team(self, config: TeamConfig) -> BaseTeam:
        """Create team from configuration.

        Args:
            config: Team configuration

        Returns:
            Team instance

        Raises:
            ConfigError: If provider is not supported
            RuntimeError: If manager not initialized
        """
        self._ensure_initialized()

        provider_class = PROVIDERS.get(config.provider)
        if provider_class is None:
            raise ConfigError(
                f"Unsupported team provider: {config.provider}. "
                f"Supported providers: {', '.join(PROVIDERS.keys())}"
            )

        config.settings["client"] = self._client
        team = provider_class(config)
        await team.initialize()
        self._teams[config.name] = team
        return team

    async def get_team(self, name: str) -> BaseTeam | None:
        """Get team by name.

        Args:
            name: Team name

        Returns:
            Team instance if found, None otherwise

        Raises:
            RuntimeError: If manager not initialized
        """
        self._ensure_initialized()
        return self._teams.get(name)

    async def list_teams(self) -> Sequence[str]:
        """Get list of team names.

        Returns:
            List of team names

        Raises:
            RuntimeError: If manager not initialized
        """
        self._ensure_initialized()
        return list(self._teams.keys())

    async def remove_team(self, name: str) -> None:
        """Remove team by name.

        Args:
            name: Team name

        Raises:
            RuntimeError: If manager not initialized
        """
        self._ensure_initialized()
        if team := self._teams.pop(name, None):
            await team.cleanup()
