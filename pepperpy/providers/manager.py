"""Provider management and fallback handling for Pepperpy.

This module provides automatic provider management, including initialization,
fallback handling, and cleanup of providers.
"""

from collections.abc import AsyncGenerator

from pepperpy.core.types import Message, MessageType, Response
from pepperpy.monitoring import logger
from pepperpy.providers.base import BaseProvider
from pepperpy.providers.domain import ProviderAPIError


class ProviderManager:
    """Manages providers and handles fallback scenarios.

    This class handles provider lifecycle, fallback logic, and error recovery,
    making it easier to work with multiple providers.
    """

    def __init__(
        self,
        primary_provider: BaseProvider,
        fallback_provider: BaseProvider | None = None,
    ) -> None:
        """Initialize the provider manager.

        Args:
            primary_provider: The main provider to use
            fallback_provider: Optional fallback provider if main fails
        """
        self.primary = primary_provider
        self.fallback = fallback_provider

    async def initialize(self) -> None:
        """Initialize all configured providers."""
        await self.primary.initialize()
        if self.fallback:
            await self.fallback.initialize()

    async def cleanup(self) -> None:
        """Cleanup all providers."""
        await self.primary.cleanup()
        if self.fallback:
            await self.fallback.cleanup()

    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> Response | AsyncGenerator[Response, None]:
        """Complete a prompt using the configured providers.

        Args:
            prompt: The prompt to complete
            temperature: Sampling temperature
            stream: Whether to stream responses

        Returns:
            Generated completion response or stream

        Raises:
            ProviderAPIError: If all providers fail
        """
        message = Message(
            type=MessageType.QUERY,
            sender="user",
            receiver="provider",
            content={"text": prompt},
        )

        if not stream:
            try:
                response = await self.primary.generate(
                    [message], temperature=temperature
                )
                return response
            except ProviderAPIError as e:
                warning_msg = (
                    f"Primary provider {self.primary.__class__.__name__} failed: {e!s}"
                )
                logger.warning(message=warning_msg)

                if not self.fallback:
                    raise

                response = await self.fallback.generate(
                    [message], temperature=temperature
                )
                return response

        # Streaming response
        async def stream_generator() -> AsyncGenerator[Response, None]:
            try:
                async for response in self.primary.stream(
                    [message], temperature=temperature
                ):
                    yield response
            except ProviderAPIError as e:
                warning_msg = (
                    f"Primary provider {self.primary.__class__.__name__} failed: {e!s}"
                )
                logger.warning(message=warning_msg)

                if not self.fallback:
                    raise

                async for response in self.fallback.stream(
                    [message], temperature=temperature
                ):
                    yield response

        return stream_generator()
