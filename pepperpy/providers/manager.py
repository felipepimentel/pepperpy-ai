"""Provider management and fallback handling for Pepperpy.

This module provides automatic provider management, including initialization,
fallback handling, and cleanup of providers.
"""

from collections.abc import AsyncGenerator
from typing import Any, Dict, Optional, TypeAlias
from uuid import uuid4

from pepperpy.core.messages import Message, Response
from pepperpy.monitoring.logger import structured_logger as logger
from pepperpy.providers.base import BaseProvider
from pepperpy.providers.domain import ProviderAPIError
from pepperpy.providers.openrouter import OpenRouterProvider

CompletionResult: TypeAlias = Response | AsyncGenerator[Response, None]


class ProviderManager:
    """Manages providers and handles fallback scenarios.

    This class handles provider lifecycle, fallback logic, and error recovery,
    making it easier to work with multiple providers.
    """

    def __init__(self, primary_provider: Optional[BaseProvider] = None) -> None:
        """Initialize the provider manager.

        Args:
        ----
            primary_provider: Optional primary provider instance.

        """
        self._primary_provider = primary_provider or OpenRouterProvider({})
        self._providers: Dict[str, BaseProvider] = {}

    async def get_provider(
        self, provider_type: str, provider_config: Dict[str, Any]
    ) -> BaseProvider:
        """Get a provider instance.

        Args:
        ----
            provider_type: Type of provider to get.
            provider_config: Provider configuration.

        Returns:
        -------
            BaseProvider: Provider instance.

        Raises:
        ------
            ValueError: If unknown provider type.

        """
        if provider_type not in self._providers:
            if provider_type == "openrouter":
                self._providers[provider_type] = OpenRouterProvider(provider_config)
            else:
                raise ValueError(f"Unknown provider type: {provider_type}")

        return self._providers[provider_type]

    async def initialize(self) -> None:
        """Initialize all configured providers."""
        await self._primary_provider.initialize()
        for provider in self._providers.values():
            await provider.initialize()

    async def cleanup(self) -> None:
        """Cleanup all providers."""
        await self._primary_provider.cleanup()
        for provider in self._providers.values():
            await provider.cleanup()

    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> CompletionResult:
        """Complete a prompt using the configured providers.

        Args:
        ----
            prompt: The prompt to complete
            temperature: Sampling temperature
            stream: Whether to stream responses

        Returns:
        -------
            CompletionResult: Generated completion response or stream

        Raises:
        ------
            ProviderAPIError: If all providers fail

        """
        message = Message(
            id=str(uuid4()),
            content=prompt,
            metadata={"temperature": temperature},
        )

        if not stream:
            try:
                response = await self._primary_provider.generate(
                    [message],
                    model_params={"temperature": temperature},
                )
                return response
            except ProviderAPIError as e:
                warning_msg = f"Primary provider {self._primary_provider.__class__.__name__} failed: {e!s}"
                logger.warning(message=warning_msg)

                if not self._providers:
                    raise

                response = await self._providers["openrouter"].generate(
                    [message],
                    model_params={"temperature": temperature},
                )
                return response

        # Streaming response
        async def stream_generator() -> AsyncGenerator[Response, None]:
            try:
                async for response in self._primary_provider.stream(
                    [message],
                    model_params={"temperature": temperature},
                ):
                    yield response
            except ProviderAPIError as e:
                warning_msg = f"Primary provider {self._primary_provider.__class__.__name__} failed: {e!s}"
                logger.warning(message=warning_msg)

                if not self._providers:
                    raise

                async for response in self._providers["openrouter"].stream(
                    [message],
                    model_params={"temperature": temperature},
                ):
                    yield response

        return stream_generator()
