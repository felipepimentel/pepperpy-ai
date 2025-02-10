"""Provider engine for managing language model providers.

This module provides the provider engine functionality for:
- Provider registration and discovery
- Provider lifecycle management
- Provider selection and routing
- Error handling and recovery
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

from pepperpy.core.errors import ProviderError, ValidationError
from pepperpy.monitoring import logger

from .base import VALID_PROVIDER_TYPES, BaseProvider, ProviderConfig

# Type variables for generic implementations
T = TypeVar("T")


class ProviderEngine:
    """Engine for managing language model providers.

    This class provides functionality for:
    - Provider registration and discovery
    - Provider lifecycle management
    - Provider selection and routing
    - Error handling and recovery
    """

    def __init__(self) -> None:
        """Initialize the provider engine."""
        self._providers: dict[str, BaseProvider] = {}
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if engine is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize the provider engine."""
        if self._initialized:
            raise ValidationError("Provider engine already initialized")
        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up provider engine resources."""
        if not self._initialized:
            raise ValidationError("Provider engine not initialized")

        # Clean up providers
        for provider in self._providers.values():
            try:
                await provider.cleanup()
            except Exception as e:
                logger.error(
                    "Provider cleanup failed",
                    provider_type=provider.config.provider_type,
                    error=str(e),
                )

        self._providers.clear()
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Ensure engine is initialized."""
        if not self._initialized:
            raise ValidationError("Provider engine not initialized")

    async def register_provider(
        self,
        provider: BaseProvider,
        provider_type: str | None = None,
    ) -> None:
        """Register a provider.

        Args:
            provider: Provider instance to register
            provider_type: Optional provider type override

        Raises:
            ValueError: If provider is already registered
            ValidationError: If engine is not initialized
        """
        self._ensure_initialized()

        provider_type = provider_type or provider.config.provider_type
        if provider_type in self._providers:
            raise ValueError(f"Provider already registered: {provider_type}")

        await provider.initialize()
        self._providers[provider_type] = provider

    async def unregister_provider(self, provider_type: str) -> None:
        """Unregister a provider.

        Args:
            provider_type: Type of provider to unregister

        Raises:
            ValueError: If provider is not registered
            ValidationError: If engine is not initialized
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
                provider_type=provider_type,
                error=str(e),
            )
            raise ProviderError(str(e), provider_type) from e

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
