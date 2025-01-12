"""Team factory module."""

from typing import Type

from ..config.team import TeamConfig
from .base import BaseTeam
from .providers.autogen import AutogenTeamProvider
from .providers.crew import CrewTeamProvider
from .providers.langchain import LangchainTeamProvider
from .providers.base import BaseTeamProvider
from .types import TeamClient


class TeamFactory:
    """Team factory implementation."""

    def __init__(self, client: TeamClient) -> None:
        """Initialize factory.

        Args:
            client: Team client instance.
        """
        self._client = client
        self._teams: dict[str, Type[BaseTeamProvider]] = {
            "autogen": AutogenTeamProvider,
            "crew": CrewTeamProvider,
            "langchain": LangchainTeamProvider,
        }

    def create(self, name: str, config: TeamConfig) -> BaseTeamProvider:
        """Create team instance.

        Args:
            name: Team name.
            config: Team configuration.

        Returns:
            BaseTeamProvider: Team instance.

        Raises:
            ValueError: If team type is not found.
        """
        team_class = self._teams.get(name)
        if team_class is None:
            raise ValueError(f"Team type not found: {name}")
        return team_class(config)
