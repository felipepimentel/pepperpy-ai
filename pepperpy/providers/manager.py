"""Provider manager for handling multiple providers.

This module provides a manager class for handling multiple providers and their
lifecycle.
"""

from collections.abc import AsyncGenerator
from typing import Any, Dict, Optional, TypeAlias
from uuid import uuid4

from pepperpy.core.errors import ConfigurationError
from pepperpy.core.messages import Message, Response
from pepperpy.monitoring import bind_logger
from pepperpy.providers.base import BaseProvider
from pepperpy.providers.domain import ProviderAPIError
from pepperpy.providers.services.openai import OpenAIProvider
from pepperpy.providers.services.openrouter import OpenRouterProvider

CompletionResult: TypeAlias = Response | AsyncGenerator[Response, None]

# Configure logger
logger = bind_logger(module="providers.manager")


class ProviderManager:
    """Manager for handling multiple providers."""

    def __init__(self) -> None:
        """Initialize the provider manager."""
        self._providers: Dict[str, BaseProvider] = {}
        self._default_provider: Optional[BaseProvider] = None

    async def get_provider(
        self,
        provider_type: str,
        config: Dict[str, Any],
    ) -> BaseProvider:
        """Get a provider instance.

        Args:
            provider_type: Type of provider to get
            config: Provider configuration

        Returns:
            Provider instance

        Raises:
            ConfigurationError: If provider type is unknown

        """
        if provider_type in self._providers:
            return self._providers[provider_type]

        provider_class = {
            "services.openai": OpenAIProvider,
            "services.openrouter": OpenRouterProvider,
        }.get(provider_type)

        if not provider_class:
            raise ConfigurationError(f"Unknown provider type: {provider_type}")

        provider = provider_class(config)
        self._providers[provider_type] = provider
        return provider

    async def cleanup(self) -> None:
        """Clean up all providers."""
        for provider in self._providers.values():
            await provider.cleanup()
        self._providers.clear()
        self._default_provider = None

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
                response = await self._default_provider.generate(
                    [message],
                    model_params={"temperature": temperature},
                )
                return response
            except ProviderAPIError as e:
                warning_msg = f"Primary provider {self._default_provider.__class__.__name__} failed: {e!s}"
                logger.warning(message=warning_msg)

                if not self._providers:
                    raise

                response = await self._providers["services.openrouter"].generate(
                    [message],
                    model_params={"temperature": temperature},
                )
                return response

        # Streaming response
        async def stream_generator() -> AsyncGenerator[Response, None]:
            try:
                async for response in self._default_provider.stream(
                    [message],
                    model_params={"temperature": temperature},
                ):
                    yield response
            except ProviderAPIError as e:
                warning_msg = f"Primary provider {self._default_provider.__class__.__name__} failed: {e!s}"
                logger.warning(message=warning_msg)

                if not self._providers:
                    raise

                async for response in self._providers["services.openrouter"].stream(
                    [message],
                    model_params={"temperature": temperature},
                ):
                    yield response

        return stream_generator()
