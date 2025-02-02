"""Provider management and fallback handling for Pepperpy.

This module provides automatic provider management, including initialization,
fallback handling, and cleanup of providers.
"""

from collections.abc import AsyncGenerator
from typing import Optional

from pepperpy.monitoring import logger
from pepperpy.providers.domain import ProviderAPIError
from pepperpy.providers.provider import BaseProvider


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
    ) -> str | AsyncGenerator[str, None]:
        """Complete a prompt using available providers.

        This method will try the primary provider first, and if it fails,
        will automatically fall back to the fallback provider if configured.

        Args:
            prompt: The prompt to complete
            temperature: Sampling temperature
            stream: Whether to stream the response

        Returns:
            Either a string response or an async generator for streaming

        Raises:
            ProviderAPIError: If all providers fail
        """
        try:
            return await self.primary.complete(
                prompt=prompt,
                temperature=temperature,
                stream=stream,
            )
        except ProviderAPIError as e:
            logger.warning(
                "Primary provider %s failed: %s",
                self.primary.__class__.__name__,
                str(e),
            )

            if not self.fallback:
                raise

            return await self.fallback.complete(
                prompt=prompt,
                temperature=temperature,
                stream=stream,
            )
