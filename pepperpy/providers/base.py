"""Base provider interfaces and abstractions.

This module defines the core provider interfaces and abstractions used throughout
the Pepperpy framework. It includes:
- Base provider interface
- Provider configuration
- Provider registration
- Error handling
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, Type, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from pepperpy.core.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Type variables
T = TypeVar("T")
ProviderType = TypeVar("ProviderType", bound="BaseProvider")


class ProviderConfig(BaseModel):
    """Provider configuration model.

    Attributes:
        id: Unique provider identifier
        type: Provider type identifier
        config: Provider-specific configuration
    """

    id: UUID = Field(default_factory=uuid4)
    type: str
    config: Dict[str, Any] = Field(default_factory=dict)


class ProviderError(Exception):
    """Base class for provider-related errors."""

    def __init__(
        self,
        message: str,
        provider_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize provider error.

        Args:
            message: Error message
            provider_type: Optional provider type identifier
            details: Optional error details
        """
        super().__init__(message)
        self.provider_type = provider_type
        self.details = details or {}


class BaseProvider(ABC, Generic[T]):
    """Base provider interface.

    All providers must implement this interface to ensure consistent
    behavior across the framework.

    Type Args:
        T: The type of data this provider handles
    """

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration
        """
        self.id = config.id
        self.type = config.type
        self.config = config.config
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider.

        This method should be called before using the provider.

        Raises:
            ConfigurationError: If initialization fails
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up provider resources."""
        pass

    @abstractmethod
    async def validate(self) -> None:
        """Validate provider configuration and state.

        Raises:
            ConfigurationError: If validation fails
        """
        pass

    @property
    def is_initialized(self) -> bool:
        """Whether the provider is initialized."""
        return self._initialized


class ProviderRegistry:
    """Provider registration and management.

    This class handles provider registration and lifecycle management.
    """

    def __init__(self) -> None:
        """Initialize provider registry."""
        self._providers: Dict[str, Type[BaseProvider[Any]]] = {}
        self._instances: Dict[str, BaseProvider[Any]] = {}
        self._lock = asyncio.Lock()

    def register_provider(
        self, provider_type: str, provider_class: Type[BaseProvider[T]]
    ) -> None:
        """Register a provider type.

        Args:
            provider_type: Provider type identifier
            provider_class: Provider class to register

        Raises:
            ProviderError: If provider type is already registered
        """
        if provider_type in self._providers:
            raise ProviderError(
                f"Provider type already registered: {provider_type}",
                provider_type=provider_type,
            )

        self._providers[provider_type] = provider_class
        logger.info(
            "Registered provider",
            extra={"type": provider_type, "class": provider_class.__name__},
        )

    async def get_provider(
        self, provider_type: str, config: Optional[Dict[str, Any]] = None
    ) -> BaseProvider[T]:
        """Get or create a provider instance.

        Args:
            provider_type: Provider type identifier
            config: Optional provider configuration

        Returns:
            Provider instance

        Raises:
            ProviderError: If provider type not found or creation fails
        """
        async with self._lock:
            # Return existing instance if available
            if provider_type in self._instances:
                return self._instances[provider_type]

            # Get provider class
            provider_class = self._providers.get(provider_type)
            if not provider_class:
                raise ProviderError(
                    f"Provider type not found: {provider_type}",
                    provider_type=provider_type,
                )

            try:
                # Create and initialize provider
                provider_config = ProviderConfig(
                    type=provider_type, config=config or {}
                )
                provider = provider_class(provider_config)
                await provider.initialize()
                await provider.validate()

                # Store instance
                self._instances[provider_type] = provider
                return provider

            except Exception as e:
                raise ProviderError(
                    f"Failed to create provider: {e}",
                    provider_type=provider_type,
                    details={"error": str(e)},
                )

    async def cleanup(self) -> None:
        """Clean up all provider instances."""
        async with self._lock:
            for provider in self._instances.values():
                try:
                    await provider.cleanup()
                except Exception as e:
                    logger.error(
                        "Failed to cleanup provider",
                        extra={
                            "type": provider.type,
                            "error": str(e),
                        },
                    )
            self._instances.clear()
