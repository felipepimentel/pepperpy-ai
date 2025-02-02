"""Pepperpy client for interacting with language models.

This module provides the main client interface for interacting with
language models through various providers.
"""

from collections.abc import AsyncGenerator
from typing import Any

from pepperpy.common.config import AutoConfig
from pepperpy.providers.manager import ProviderManager
from pepperpy.providers.services.openrouter import OpenRouterProvider


class PepperpyClient:
    """Main client for interacting with language models."""

    def __init__(self) -> None:
        """Initialize the client."""
        self._manager: ProviderManager | None = None

    async def __aenter__(self) -> "PepperpyClient":
        """Initialize the client for use in async context."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Clean up resources when exiting async context."""
        await self.cleanup()

    async def initialize(self) -> None:
        """Initialize the client.

        This loads configuration and sets up the provider manager.
        """
        config = AutoConfig.from_env()
        provider_config = config.get_provider_config()
        primary_provider = OpenRouterProvider(provider_config)
        self._manager = ProviderManager(primary_provider)
        await self._manager.initialize()

    async def cleanup(self) -> None:
        """Clean up client resources."""
        if self._manager:
            await self._manager.cleanup()
            self._manager = None

    async def chat(self, message: str) -> str:
        """Send a chat message and get a response.

        Args:
            message: The message to send

        Returns:
            The response from the provider

        Raises:
            RuntimeError: If client is not initialized
            TypeError: If provider returns a streaming response
        """
        if not self._manager:
            raise RuntimeError("Client not initialized")

        response = await self._manager.complete(message, stream=False)
        if isinstance(response, AsyncGenerator):
            raise TypeError("Provider returned a streaming response")
        return response

    async def chat_stream(self, message: str) -> AsyncGenerator[str, None]:
        """Send a chat message and get a streaming response.

        Args:
            message: The message to send

        Returns:
            An async generator yielding response chunks

        Raises:
            RuntimeError: If client is not initialized
        """
        if not self._manager:
            raise RuntimeError("Client not initialized")

        response = await self._manager.complete(message, stream=True)
        if isinstance(response, AsyncGenerator):
            return response
        else:
            # If provider doesn't support streaming, yield the entire response
            async def single_response() -> AsyncGenerator[str, None]:
                yield response

            return single_response()
