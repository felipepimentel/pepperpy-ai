"""Team factory implementation."""

from typing import Any, Type, cast

from ..exceptions import ConfigurationError as ConfigError
from .base import BaseTeamProvider
from .config import TeamConfig
from .providers.autogen import AutogenTeamProvider
from .providers.crew import CrewTeamProvider
from .providers.langchain import LangchainTeamProvider

# Map of provider names to their implementations
PROVIDERS: dict[str, Type[BaseTeamProvider]] = {
    "autogen": cast(Type[BaseTeamProvider], AutogenTeamProvider),
    "crew": cast(Type[BaseTeamProvider], CrewTeamProvider),
    "langchain": cast(Type[BaseTeamProvider], LangchainTeamProvider),
}


class TeamFactory:
    """Team factory implementation."""

    def __init__(self, client: Any) -> None:
        """Initialize factory.

        Args:
            client: AI client instance
        """
        self._client = client
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if factory is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize factory."""
        if not self._initialized:
            if not self._client.is_initialized:
                await self._client.initialize()
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup factory resources."""
        if self._initialized:
            self._initialized = False

    def _ensure_initialized(self) -> None:
        """Ensure factory is initialized."""
        if not self._initialized:
            raise RuntimeError("Factory not initialized")

    async def create_team(self, config: TeamConfig) -> BaseTeamProvider:
        """Create team from configuration.

        Args:
            config: Team configuration

        Returns:
            Team instance

        Raises:
            ConfigError: If provider is not supported
            RuntimeError: If factory not initialized
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
        return team

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """Get list of supported provider names.

        Returns:
            List of provider names
        """
        return list(PROVIDERS.keys())
