"""Provider engine for managing language model providers.

This module provides the provider engine functionality for:
- Provider registration and discovery
- Provider lifecycle management
- Provider selection and routing
- Error handling and recovery
"""

from typing import Dict, Optional
from uuid import uuid4

from pepperpy.common.base import Lifecycle
from pepperpy.common.errors import ProviderError, ValidationError
from pepperpy.common.logging import get_logger
from pepperpy.common.types import ComponentState

from .base import BaseProvider, ProviderConfig
from .factory import ProviderFactory

logger = get_logger(__name__)


class ProviderEngine(Lifecycle):
    """Engine for managing language model providers.

    This class provides functionality for:
    - Provider registration and discovery
    - Provider lifecycle management
    - Provider selection and routing
    - Error handling and recovery
    """

    def __init__(self) -> None:
        """Initialize the provider engine."""
        super().__init__()
        self._factory = ProviderFactory(id=uuid4())
        self._providers: Dict[str, BaseProvider] = {}
        self._initialized = False
        self._state = ComponentState.UNREGISTERED

    @property
    def is_initialized(self) -> bool:
        """Check if engine is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize the provider engine.

        Raises:
            ValidationError: If engine is already initialized
            ProviderError: If initialization fails
        """
        try:
            if self._initialized:
                raise ValidationError("Provider engine already initialized")

            # Set initializing state
            self._state = ComponentState.INITIALIZED

            # Initialize factory
            await self._factory.execute()
            self._initialized = True

            # Update state
            self._state = ComponentState.RUNNING
            logger.info("Provider engine initialized")

        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize provider engine: {e}")
            raise ProviderError("Failed to initialize provider engine") from e

    async def cleanup(self) -> None:
        """Clean up provider engine resources.

        Raises:
            ValidationError: If engine is not initialized
            ProviderError: If cleanup fails
        """
        try:
            if not self._initialized:
                raise ValidationError("Provider engine not initialized")

            # Clean up providers
            for provider in self._providers.values():
                try:
                    await provider.cleanup()
                except Exception as e:
                    logger.error(
                        "Provider cleanup failed",
                        extra={
                            "provider_type": provider.config.provider_type,
                            "error": str(e),
                        },
                    )

            # Clean up factory and state
            await self._factory.cleanup()
            self._providers.clear()
            self._initialized = False

            # Update state
            self._state = ComponentState.UNREGISTERED
            logger.info("Provider engine cleaned up")

        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to cleanup provider engine: {e}")
            raise ProviderError("Failed to cleanup provider engine") from e

    def _ensure_initialized(self) -> None:
        """Ensure engine is initialized."""
        if not self._initialized:
            raise ValidationError("Provider engine not initialized")

    async def register_provider(
        self,
        config: ProviderConfig,
        provider_type: Optional[str] = None,
    ) -> None:
        """Register a provider.

        Args:
            config: Provider configuration
            provider_type: Optional provider type override

        Raises:
            ValueError: If provider is already registered
            ValidationError: If engine is not initialized
            ProviderError: If provider creation fails

        """
        self._ensure_initialized()

        provider_type = provider_type or config.provider_type
        if provider_type in self._providers:
            raise ValueError(f"Provider already registered: {provider_type}")

        try:
            provider = await self._factory.execute(
                provider_type=provider_type,
                config=config,
            )
            self._providers[provider_type] = provider
        except Exception as e:
            raise ProviderError(
                "Failed to create provider",
                details={"error": str(e), "provider_type": provider_type},
            )

    async def unregister_provider(self, provider_type: str) -> None:
        """Unregister a provider.

        Args:
            provider_type: Type of provider to unregister

        Raises:
            ValueError: If provider is not registered
            ValidationError: If engine is not initialized
            ProviderError: If provider cleanup fails

        """
        self._ensure_initialized()

        if provider_type not in self._providers:
            raise ValueError(f"Provider not registered: {provider_type}")

        provider = self._providers[provider_type]
        try:
            await provider.cleanup()
            del self._providers[provider_type]
        except Exception as e:
            logger.error(
                "Provider cleanup failed",
                extra={
                    "provider_type": provider_type,
                    "error": str(e),
                },
            )
            raise ProviderError(
                "Failed to cleanup provider",
                details={"error": str(e), "provider_type": provider_type},
            )

    def get_provider(self, provider_type: str) -> BaseProvider:
        """Get a registered provider.

        Args:
            provider_type: Type of provider to get

        Returns:
            Provider instance

        Raises:
            ValueError: If provider is not registered
            ValidationError: If engine is not initialized

        """
        self._ensure_initialized()

        if provider_type not in self._providers:
            raise ValueError(f"Provider not registered: {provider_type}")

        return self._providers[provider_type]

    def list_providers(self) -> list[BaseProvider]:
        """Get all registered providers.

        Returns:
            List of provider instances

        Raises:
            ValidationError: If engine is not initialized

        """
        self._ensure_initialized()
        return list(self._providers.values())
