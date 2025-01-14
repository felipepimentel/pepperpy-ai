"""Team manager module."""

from typing import Any

from pepperpy.teams.config import TeamConfig
from pepperpy.teams.factory import TeamFactory
from pepperpy.teams.providers.base import BaseTeamProvider


class TeamManager:
    """Team manager."""

    def __init__(self) -> None:
        """Initialize team manager."""
        self._teams: dict[str, BaseTeamProvider] = {}

    def create_team(self, config: TeamConfig, **kwargs: Any) -> BaseTeamProvider:
        """Create team provider.

        Args:
            config: Team configuration.
            **kwargs: Additional arguments.

        Returns:
            BaseTeamProvider: Team provider.
        """
        team = TeamFactory.create_team(config, **kwargs)
        self._teams[config.name] = team
        return team

    def get_team(self, name: str) -> BaseTeamProvider:
        """Get team provider.

        Args:
            name: Team name.

        Returns:
            BaseTeamProvider: Team provider.

        Raises:
            ValueError: If team is not found.
        """
        team = self._teams.get(name)
        if team is None:
            raise ValueError(f"Team not found: {name}")
        return team
