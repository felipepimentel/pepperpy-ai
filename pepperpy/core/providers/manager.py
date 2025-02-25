"""Provider management module.

This module provides the provider management functionality for the Pepperpy framework.
It is a thin wrapper around the unified provider system.
"""

from pepperpy.core.providers.unified import (
    BaseProvider,
    ProviderConfig,
    ProviderError,
    ProviderNotFoundError,
    UnifiedProviderRegistry,
)

# Re-export the unified provider registry as ProviderManager for backward compatibility
ProviderManager = UnifiedProviderRegistry

__all__ = [
    "BaseProvider",
    "ProviderConfig",
    "ProviderError",
    "ProviderManager",
    "ProviderNotFoundError",
]
"""Provider registration and lifecycle management.

This module handles provider registration, creation, and lifecycle
management. It includes:
- Provider registration
- Provider creation
- Provider lifecycle management
- Provider discovery
"""

import asyncio
from typing import Any

from pepperpy.core.logging import get_logger
from pepperpy.core.providers.base import BaseProvider, ProviderConfig
from pepperpy.core.providers.errors import (
    ProviderConfigurationError,
    ProviderNotFoundError,
    ProviderRuntimeError,
)

# Configure logging
logger = get_logger(__name__)


class ProviderManager:
    """Provider management system.

    This class handles provider registration, creation, and lifecycle
    management. It ensures providers are properly initialized and
    cleaned up.
    """

    def __init__(self) -> None:
        """Initialize provider manager."""
        self._providers: dict[str, BaseProvider] = {}
        self._provider_types: dict[str, type[BaseProvider]] = {}
        self._lock = asyncio.Lock()

    def register_provider(self, type: str, provider_class: type[BaseProvider]) -> None:
        """Register a provider type.

        Args:
            type: Provider type identifier
            provider_class: Provider class to register

        Raises:
            ProviderConfigurationError: If provider type is already registered
        """
        if type in self._provider_types:
            raise ProviderConfigurationError(
                f"Provider type already registered: {type}", provider_type=type
            )

        self._provider_types[type] = provider_class
        logger.info(
            "Registered provider type",
            extra={"type": type, "class": provider_class.__name__},
        )

    async def get_provider(
        self, type: str, config: dict[str, Any] | None = None
    ) -> BaseProvider:
        """Get or create a provider instance.

        Args:
            type: Provider type identifier
            config: Optional provider configuration

        Returns:
            Provider instance

        Raises:
            ProviderNotFoundError: If provider type is not found
            ProviderConfigurationError: If provider configuration is invalid
            ProviderRuntimeError: If provider initialization fails
        """
        async with self._lock:
            if type in self._providers:
                return self._providers[type]

            try:
                provider_config = ProviderConfig(type=type, config=config or {})
                provider = await self._create_provider(provider_config)
                self._providers[type] = provider
                return provider

            except Exception as e:
                logger.error(
                    "Failed to get provider", extra={"type": type, "error": str(e)}
                )
                if isinstance(
                    e,
                    (
                        ProviderNotFoundError,
                        ProviderConfigurationError,
                        ProviderRuntimeError,
                    ),
                ):
                    raise
                raise ProviderRuntimeError(
                    f"Failed to get provider: {e}", provider_type=type
                )

    async def cleanup(self) -> None:
        """Clean up all provider resources.

        This method should be called when shutting down to ensure
        all provider resources are properly cleaned up.
        """
        async with self._lock:
            for type, provider in self._providers.items():
                try:
                    await provider.cleanup()
                except Exception as e:
                    logger.error(
                        "Failed to clean up provider",
                        extra={"type": type, "error": str(e)},
                    )

            self._providers.clear()

    async def _create_provider(self, config: ProviderConfig) -> BaseProvider:
        """Create a new provider instance.

        Args:
            config: Provider configuration

        Returns:
            Provider instance

        Raises:
            ProviderNotFoundError: If provider type is not found
            ProviderConfigurationError: If provider configuration is invalid
            ProviderRuntimeError: If provider initialization fails
        """
        if config.type not in self._provider_types:
            raise ProviderNotFoundError(config.type)

        try:
            provider_class = self._provider_types[config.type]
            provider = provider_class(config)
            await provider.initialize()
            return provider

        except ProviderConfigurationError:
            raise
        except Exception as e:
            raise ProviderRuntimeError(
                f"Failed to create provider: {e}", provider_type=config.type
            )
