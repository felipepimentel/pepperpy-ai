"""Service providers for the Pepperpy library.

This module contains the implementation of various service providers
that can be used with Pepperpy, such as OpenAI, Anthropic, etc.

This module also provides common functionality for provider implementations,
reducing code duplication and standardizing error handling.
"""

from typing import Final, cast

from pepperpy.core.errors import ProviderError
from pepperpy.monitoring import logger

from ..base import BaseProvider, ProviderConfig
from ..domain import ProviderInitError
from ..engine import ProviderEngine
from .gemini import GeminiConfig, GeminiProvider
from .openai import OpenAIConfig, OpenAIProvider

# Provider types
OPENAI: Final[str] = "openai"
GEMINI: Final[str] = "gemini"

REQUIRED_PROVIDERS: Final[list[str]] = [OPENAI]
OPTIONAL_PROVIDERS: Final[list[str]] = [GEMINI]

# Track registered providers
REGISTERED_PROVIDERS: dict[str, type[BaseProvider]] = {}


class ProviderRegistry:
    """Registry for managing provider registration."""

    def __init__(self) -> None:
        """Initialize the provider registry."""
        self.engine = ProviderEngine()
        self.providers: dict[str, type[BaseProvider]] = {}

    async def initialize(self) -> None:
        """Initialize the registry and engine."""
        await self.engine.initialize()

    async def cleanup(self) -> None:
        """Clean up registry resources."""
        await self.engine.cleanup()

    async def register_provider(
        self,
        provider_type: str,
        provider_class: type[BaseProvider],
        config: ProviderConfig | None = None,
    ) -> None:
        """Register a provider with the registry.

        Args:
            provider_type: Type identifier for the provider
            provider_class: Provider class to register
            config: Optional provider configuration

        Raises:
            ProviderInitError: If registration fails
        """
        try:
            # Create provider instance if config provided
            if config:
                provider = provider_class(config)
                await self.engine.register_provider(provider, provider_type)

            # Store provider class for later instantiation
            self.providers[provider_type] = provider_class

        except Exception as e:
            raise ProviderInitError(
                message=f"Failed to register provider {provider_type}: {e}",
                provider_type=provider_type,
            ) from e


async def register_providers() -> dict[str, type[BaseProvider]]:
    """Register all available providers.

    Returns:
        Dictionary mapping provider types to their classes

    Raises:
        ProviderInitError: If a required provider fails to register
    """
    registry = ProviderRegistry()
    await registry.initialize()

    try:
        # Register required providers
        try:
            from .openai import OpenAIProvider

            provider_class = cast(type[BaseProvider], OpenAIProvider)
            await registry.register_provider(OPENAI, provider_class)
            registry.providers[OPENAI] = provider_class
        except ImportError as e:
            raise ProviderInitError(
                message=f"Required provider 'openai' not available: {e}",
                provider_type=OPENAI,
            ) from e

        # Register optional providers
        try:
            from .gemini import GeminiProvider

            provider_class = cast(type[BaseProvider], GeminiProvider)
            await registry.register_provider(GEMINI, provider_class)
            registry.providers[GEMINI] = provider_class
        except ImportError as e:
            logger.warning(
                "Optional provider not available",
                extra={"provider": GEMINI, "error": str(e)},
            )

        return dict(registry.providers)

    finally:
        await registry.cleanup()


# Initialize registry asynchronously
REGISTRY = ProviderRegistry()


__all__ = [
    "GEMINI",
    "OPENAI",
    "OPTIONAL_PROVIDERS",
    "REGISTERED_PROVIDERS",
    "REQUIRED_PROVIDERS",
    "BaseProvider",
    "GeminiConfig",
    "GeminiProvider",
    "OpenAIConfig",
    "OpenAIProvider",
    "ProviderConfig",
    "ProviderError",
    "ProviderRegistry",
    "register_providers",
]
