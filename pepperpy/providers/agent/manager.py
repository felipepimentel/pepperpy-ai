"""Provider manager for handling multiple providers.

This module provides a manager class for handling multiple providers and their
lifecycle.
"""

from collections.abc import AsyncGenerator
from typing import Optional

from pepperpy.core.common.base import Lifecycle
from pepperpy.core.errors import ConfigurationError, ProviderError
from pepperpy.core.logging import get_logger
from pepperpy.core.common.types import ComponentState, MessageType, Response

from .base import ProviderConfig
from .domain import ProviderAPIError
from .engine import ProviderEngine
from .types import ProviderMessage

logger = get_logger(__name__)


class ProviderManager(Lifecycle):
    """Manager for handling multiple providers."""

    def __init__(self) -> None:
        """Initialize the provider manager."""
        super().__init__()
        self._engine = ProviderEngine()
        self._default_provider: Optional[str] = None
        self._initialized = False
        self._state = ComponentState.UNREGISTERED

    async def initialize(self) -> None:
        """Initialize the provider manager.

        Raises:
            ConfigurationError: If manager is already initialized
            ProviderError: If initialization fails
        """
        try:
            if self._initialized:
                raise ConfigurationError("Provider manager already initialized")

            # Set initializing state
            self._state = ComponentState.INITIALIZED

            # Initialize engine
            await self._engine.initialize()
            self._initialized = True

            # Update state
            self._state = ComponentState.RUNNING
            logger.info("Provider manager initialized")

        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize provider manager: {e}")
            raise ProviderError("Failed to initialize provider manager") from e

    async def cleanup(self) -> None:
        """Clean up all providers.

        Raises:
            ConfigurationError: If manager is not initialized
            ProviderError: If cleanup fails
        """
        try:
            if not self._initialized:
                raise ConfigurationError("Provider manager not initialized")

            # Clean up engine
            await self._engine.cleanup()
            self._initialized = False

            # Update state
            self._state = ComponentState.UNREGISTERED
            logger.info("Provider manager cleaned up")

        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to cleanup provider manager: {e}")
            raise ProviderError("Failed to cleanup provider manager") from e

    def _ensure_initialized(self) -> None:
        """Ensure manager is initialized."""
        if not self._initialized:
            raise ConfigurationError("Provider manager not initialized")

    async def register_provider(
        self,
        config: ProviderConfig,
        provider_type: Optional[str] = None,
        is_default: bool = False,
    ) -> None:
        """Register a provider.

        Args:
            config: Provider configuration
            provider_type: Optional provider type override
            is_default: Whether to set as default provider

        Raises:
            ConfigurationError: If manager is not initialized
            ProviderError: If provider registration fails

        """
        self._ensure_initialized()

        provider_type = provider_type or config.provider_type
        await self._engine.register_provider(config, provider_type)

        if is_default or self._default_provider is None:
            self._default_provider = provider_type

    async def unregister_provider(self, provider_type: str) -> None:
        """Unregister a provider.

        Args:
            provider_type: Type of provider to unregister

        Raises:
            ConfigurationError: If manager is not initialized
            ProviderError: If provider unregistration fails

        """
        self._ensure_initialized()
        await self._engine.unregister_provider(provider_type)

        if self._default_provider == provider_type:
            providers = self._engine.list_providers()
            self._default_provider = (
                providers[0].config.provider_type if providers else None
            )

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
            ConfigurationError: If manager is not initialized
            ProviderError: If all providers fail

        """
        self._ensure_initialized()

        if not self._default_provider:
            raise ConfigurationError("No default provider configured")

        provider_message = ProviderMessage(
            content=prompt,
            provider_type=self._default_provider,
            type=MessageType.QUERY,
            parameters={"temperature": temperature},
        )

        try:
            provider = self._engine.get_provider(self._default_provider)
            if not stream:
                return await provider.process_message(provider_message)

            async def stream_generator() -> AsyncGenerator[Response, None]:
                response = await provider.process_message(provider_message)
                yield response

            return stream_generator()

        except ProviderAPIError as e:
            warning_msg = f"Primary provider {self._default_provider} failed: {e!s}"
            logger.warning(warning_msg)

            # Try fallback providers
            providers = self._engine.list_providers()
            for provider in providers:
                if provider.config.provider_type == self._default_provider:
                    continue

                try:
                    if not stream:
                        return await provider.process_message(provider_message)

                    async def stream_generator() -> AsyncGenerator[Response, None]:
                        response = await provider.process_message(provider_message)
                        yield response

                    return stream_generator()

                except ProviderAPIError:
                    continue

            raise ProviderError(
                "All providers failed",
                details={"original_error": str(e)},
            )
