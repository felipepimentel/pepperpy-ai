"""Teams client module."""

from typing import Any, cast

import aiohttp

from pepperpy.network import HTTPClient

from .providers.config import TeamProviderConfig


class TeamsClient:
    """Teams client."""

    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        """Initialize teams client.

        Args:
            base_url: Base URL.
            api_key: API key.
        """
        self._client = HTTPClient()
        self._base_url = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    async def initialize(self) -> None:
        """Initialize client."""
        await self._client.initialize()

    async def close(self) -> None:
        """Close client."""
        await self._client.cleanup()

    async def get_team_config(self, team_id: str) -> TeamProviderConfig:
        """Get team configuration.

        Args:
            team_id: Team ID.

        Returns:
            Team configuration.

        Raises:
            HTTPError: If the request fails.
        """
        response = cast(
            aiohttp.ClientResponse,
            await self._client.get(
                f"{self._base_url}/teams/{team_id}/config",
                headers=self._headers,
            ),
        )
        data = cast(dict[str, Any], await response.json())
        return TeamProviderConfig(
            members=data.get("members", []),
            roles=data.get("roles", {}),
            tools=data.get("tools", {}),
        )
