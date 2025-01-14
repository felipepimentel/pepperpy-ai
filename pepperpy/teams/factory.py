"""Team factory module."""

from typing import Any, ClassVar, cast

from pepperpy.teams.config import TeamConfig
from pepperpy.teams.providers.autogen import AutogenTeamProvider
from pepperpy.teams.providers.base import BaseTeamProvider
from pepperpy.teams.providers.crew import CrewTeamProvider
from pepperpy.teams.providers.langchain import LangchainTeamProvider


class TeamFactory:
    """Team factory."""

    _providers: ClassVar[dict[str, type[BaseTeamProvider]]] = {
        "autogen": AutogenTeamProvider,
        "crew": CrewTeamProvider,
        "langchain": LangchainTeamProvider,
    }

    @classmethod
    def create_team(cls, config: TeamConfig, **kwargs: Any) -> BaseTeamProvider:
        """Create team provider.

        Args:
            config: Team configuration.
            **kwargs: Additional arguments.

        Returns:
            BaseTeamProvider: Team provider.

        Raises:
            ValueError: If provider type is not supported.
        """
        provider_type = config.provider
        if provider_type not in cls._providers:
            raise ValueError(f"Unsupported provider type: {provider_type}")

        provider_class = cls._providers[provider_type]
        provider = provider_class()
        provider._config = config  # type: ignore
        if provider_type == "crew":
            crew_provider = cast(CrewTeamProvider, provider)
            crew_provider._llm = kwargs.get("llm")
            crew_provider._tools = kwargs.get("tools", [])
            crew_provider._retriever = kwargs.get("retriever")
            crew_provider._memory = kwargs.get("memory")
            crew_provider._kwargs = kwargs
        return provider
