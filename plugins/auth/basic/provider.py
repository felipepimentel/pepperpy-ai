"""
Basic authentication provider for AI Gateway.

This provider implements simple API key authentication.
"""

from typing import Any

from pepperpy.core.logging import get_logger
from pepperpy.plugin import PepperpyPlugin

logger = get_logger(__name__)


class BasicAuthProvider(PepperpyPlugin):
    """Basic authentication provider using API keys."""

    plugin_type = "auth"
    provider_name = "basic"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the auth provider.

        Args:
            **kwargs: Provider configuration
        """
        super().__init__()
        self.config = kwargs or {}
        self.api_key_header = self.config.get("api_key_header", "X-API-Key")
        self.api_keys = self.config.get("api_keys", {})
        self.require_auth = self.config.get("require_auth", True)
        self.initialized = False
        self.host = None
        self.port = None

    async def initialize(self) -> None:
        """Initialize the auth provider."""
        if self.initialized:
            return

        logger.info("Initializing Basic Auth Provider")
        logger.info(f"API Key Header: {self.api_key_header}")
        logger.info(f"Number of API Keys: {len(self.api_keys)}")
        logger.info(f"Require Auth: {self.require_auth}")

        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        logger.info("Cleaning up Basic Auth Provider")
        self.initialized = False

    async def configure(self, host: str, port: int) -> None:
        """Configure the auth provider.

        Args:
            host: The host to bind to
            port: The port to listen on
        """
        self.host = host
        self.port = port
        logger.info(f"Configured Basic Auth Provider for {host}:{port}")

    async def authenticate(self, headers: dict[str, str]) -> dict[str, Any]:
        """Authenticate a request.

        Args:
            headers: Request headers

        Returns:
            Authentication result with user_id if successful
        """
        if not self.require_auth:
            return {"authenticated": True, "user_id": "anonymous"}

        api_key = headers.get(self.api_key_header)
        if not api_key:
            # Try Authorization header as fallback
            auth_header = headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                api_key = auth_header[7:]  # Remove 'Bearer ' prefix

        if not api_key:
            return {"authenticated": False, "error": "No API key provided"}

        user_id = self.api_keys.get(api_key)
        if not user_id:
            return {"authenticated": False, "error": "Invalid API key"}

        return {
            "authenticated": True,
            "user_id": user_id,
        }

    async def add_api_key(self, api_key: str, user_id: str) -> dict[str, Any]:
        """Add a new API key.

        Args:
            api_key: The API key to add
            user_id: The user ID for the key

        Returns:
            Result of the operation
        """
        if api_key in self.api_keys:
            return {"status": "error", "message": "API key already exists"}

        self.api_keys[api_key] = user_id
        return {"status": "success", "message": "API key added"}

    async def remove_api_key(self, api_key: str) -> dict[str, Any]:
        """Remove an API key.

        Args:
            api_key: The API key to remove

        Returns:
            Result of the operation
        """
        if api_key not in self.api_keys:
            return {"status": "error", "message": "API key not found"}

        del self.api_keys[api_key]
        return {"status": "success", "message": "API key removed"}

    async def get_api_keys(self) -> dict[str, Any]:
        """Get all API keys.

        Returns:
            Dictionary of API keys and their user IDs
        """
        return {"status": "success", "api_keys": self.api_keys}
