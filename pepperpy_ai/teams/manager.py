"""Team manager module."""

from ..config.team import TeamConfig
from .base import BaseTeam
from .factory import TeamFactory
from .types import TeamClient, TeamParams


class TeamManager:
    """Team manager implementation."""

    def __init__(self, client: TeamClient) -> None:
        """Initialize team manager.

        Args:
            client: Team client instance.
        """
        self._client = client
        self._factory = TeamFactory(client)
        self._teams: dict[str, BaseTeam] = {}

    async def create_team(self, name: str, config: TeamConfig) -> BaseTeam:
        """Create and initialize team.

        Args:
            name: Team name.
            config: Team configuration.

        Returns:
            BaseTeam: Team instance.
        """
        team = self._factory.create(name, config)
        await team.initialize()
        self._teams[name] = team
        return team

    async def get_team(self, name: str) -> BaseTeam:
        """Get team by name.

        Args:
            name: Team name.

        Returns:
            BaseTeam: Team instance.

        Raises:
            ValueError: If team not found.
        """
        if name not in self._teams:
            raise ValueError(f"Team not found: {name}")
        return self._teams[name]

    async def execute_task(self, name: str, task: str, **kwargs: TeamParams) -> None:
        """Execute task with team.

        Args:
            name: Team name.
            task: Task to execute.
            **kwargs: Additional task parameters.

        Raises:
            ValueError: If team not found.
        """
        team = await self.get_team(name)
        await team.execute_task(task, **kwargs)

    async def cleanup(self) -> None:
        """Clean up all teams."""
        for team in self._teams.values():
            await team.cleanup()
        self._teams.clear()
