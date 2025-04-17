"""
Basic authentication provider for AI Gateway.

This provider implements simple API key authentication.
"""

from typing import Any

from pepperpy.plugin.provider import BasePluginProvider


class BasicAuthProvider(BasePluginProvider):
    """Basic authentication provider using API keys."""

    async def initialize(self) -> None:
        """Initialize the provider.

        This method is called automatically when the provider is first used.
        """
        # Initialize state
        self.initialized = True

        # Get configuration
        self.api_key_header = self.config.get("api_key_header", "X-API-Key")
        self.api_keys = self.config.get("api_keys", {})
        self.require_auth = self.config.get("require_auth", True)
        self.host = None
        self.port = None

        self.logger.info("Initializing Basic Auth Provider")
        self.logger.info(f"API Key Header: {self.api_key_header}")
        self.logger.info(f"Number of API Keys: {len(self.api_keys)}")
        self.logger.info(f"Require Auth: {self.require_auth}")

    async def cleanup(self) -> None:
        """Clean up resources.

        This method is called automatically when the context manager exits.
        """
        if not self.initialized:
            return

        self.logger.info("Cleaning up Basic Auth Provider")
        self.initialized = False

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute an authentication task.

        Args:
            input_data: Task data containing:
                - task: Task name (authenticate, add_api_key, remove_api_key, get_api_keys)
                - headers: Request headers (for authenticate)
                - api_key: API key to add/remove
                - user_id: User ID for the API key

        Returns:
            Authentication result or task result
        """
        task = input_data.get("task")

        if not task:
            return {"status": "error", "message": "No task specified"}

        try:
            if task == "authenticate":
                headers = input_data.get("headers", {})
                result = await self.authenticate(headers)
                return {"status": "success", "result": result}

            elif task == "add_api_key":
                api_key = input_data.get("api_key")
                user_id = input_data.get("user_id")

                if not api_key or not user_id:
                    return {
                        "status": "error",
                        "message": "API key and user ID are required",
                    }

                return await self.add_api_key(api_key, user_id)

            elif task == "remove_api_key":
                api_key = input_data.get("api_key")

                if not api_key:
                    return {"status": "error", "message": "API key is required"}

                return await self.remove_api_key(api_key)

            elif task == "get_api_keys":
                return await self.get_api_keys()

            elif task == "configure":
                host = input_data.get("host")
                port = input_data.get("port")

                if not host or not port:
                    return {"status": "error", "message": "Host and port are required"}

                await self.configure(host, port)
                return {"status": "success", "message": "Auth provider configured"}

            else:
                return {"status": "error", "message": f"Unknown task: {task}"}

        except Exception as e:
            self.logger.error(f"Error executing task '{task}': {e}")
            return {"status": "error", "message": str(e)}

    async def configure(self, host: str, port: int) -> None:
        """Configure the auth provider.

        Args:
            host: The host to bind to
            port: The port to listen on
        """
        self.host = host
        self.port = port
        self.logger.info(f"Configured Basic Auth Provider for {host}:{port}")

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
