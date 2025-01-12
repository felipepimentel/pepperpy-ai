"""Team client module."""

from ..config.client import ClientConfig
from ..network.client import HTTPClient


class TeamClient:
    """Team client implementation."""

    def __init__(self, config: ClientConfig) -> None:
        """Initialize client.

        Args:
            config: Client configuration.
        """
        self._config = config
        self._client = HTTPClient()
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if client is initialized.

        Returns:
            bool: True if client is initialized, False otherwise.
        """
        return self._initialized

    async def initialize(self) -> None:
        """Initialize client."""
        if not self._initialized:
            await self._client.initialize()
            self._initialized = True

    async def cleanup(self) -> None:
        """Clean up client resources."""
        if self._initialized:
            await self._client.cleanup()
            self._initialized = False
