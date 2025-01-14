"""Teams client module."""

from ..network.client import NetworkClient
from .providers.config import TeamProviderConfig


class TeamsClient:
    """Teams client."""

    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        """Initialize teams client.

        Args:
            base_url: Base URL.
            api_key: API key.
        """
        self._client = NetworkClient(base_url=base_url, api_key=api_key)

    async def initialize(self) -> None:
        """Initialize client."""
        await self._client.initialize()

    async def close(self) -> None:
        """Close client."""
        await self._client.close()

    async def get_team_config(self, team_id: str) -> TeamProviderConfig:
        """Get team configuration.

        Args:
            team_id: Team ID.

        Returns:
            Team configuration.
        """
        data = await self._client.get(f"/teams/{team_id}/config")
        return TeamProviderConfig(**data)
