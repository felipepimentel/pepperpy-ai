"""Unified provider system.

This module provides a unified provider system for the Pepperpy framework.
It includes base classes and registry for managing providers.
"""

from abc import ABC, abstractmethod
from typing import Any, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from pepperpy.core.errors import PepperpyError
from pepperpy.core.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Type variable for provider configuration
T = TypeVar("T", bound=BaseModel)


class ProviderError(PepperpyError):
    """Base class for provider errors."""

    pass


class ProviderNotFoundError(ProviderError):
    """Error raised when a provider is not found."""

    pass


class ProviderConfig(BaseModel):
    """Base configuration for providers."""

    name: str = Field(description="Provider name")
    version: str = Field(default="1.0.0", description="Provider version")
    description: str = Field(default="", description="Provider description")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Provider parameters"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Provider metadata"
    )


class BaseProvider(ABC):
    """Base class for all providers."""

    config_class: type[ProviderConfig] = ProviderConfig

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration
        """
        self.id = uuid4()
        self.config = config
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize provider.

        This method should be implemented by subclasses to handle
        provider-specific initialization.
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method should be implemented by subclasses to handle
        provider-specific cleanup.
        """
        pass

    @property
    def initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized


class UnifiedProviderRegistry:
    """Registry for managing providers."""

    def __init__(self) -> None:
        """Initialize registry."""
        self._providers: dict[UUID, BaseProvider] = {}
        self._provider_types: dict[str, type[BaseProvider]] = {}

    def register_provider(self, name: str, provider_class: type[BaseProvider]) -> None:
        """Register a provider type.

        Args:
            name: Provider name
            provider_class: Provider class to register

        Raises:
            ProviderError: If provider is already registered
        """
        if name in self._provider_types:
            raise ProviderError(f"Provider {name} is already registered")
        self._provider_types[name] = provider_class
        logger.info(f"Registered provider {name}")

    def unregister_provider(self, name: str) -> None:
        """Unregister a provider type.

        Args:
            name: Provider name to unregister

        Raises:
            ProviderNotFoundError: If provider is not found
        """
        if name not in self._provider_types:
            raise ProviderNotFoundError(f"Provider {name} not found")
        del self._provider_types[name]
        logger.info(f"Unregistered provider {name}")

    async def create_provider(
        self, name: str, config: dict[str, Any] | None = None
    ) -> BaseProvider:
        """Create a provider instance.

        Args:
            name: Provider name
            config: Optional provider configuration

        Returns:
            Provider instance

        Raises:
            ProviderNotFoundError: If provider is not found
            ProviderError: If provider creation fails
        """
        if name not in self._provider_types:
            raise ProviderNotFoundError(f"Provider {name} not found")

        try:
            provider_class = self._provider_types[name]
            provider_config = provider_class.config_class(
                name=name, parameters=config or {}
            )
            provider = provider_class(provider_config)
            await provider.initialize()
            self._providers[provider.id] = provider
            logger.info(f"Created provider {name}")
            return provider
        except Exception as e:
            raise ProviderError(f"Failed to create provider {name}: {e}")

    async def get_provider(self, id: UUID) -> BaseProvider:
        """Get a provider instance.

        Args:
            id: Provider ID

        Returns:
            Provider instance

        Raises:
            ProviderNotFoundError: If provider is not found
        """
        if id not in self._providers:
            raise ProviderNotFoundError(f"Provider {id} not found")
        return self._providers[id]

    async def cleanup(self) -> None:
        """Clean up all providers."""
        for provider in self._providers.values():
            try:
                await provider.cleanup()
            except Exception as e:
                logger.error(f"Failed to clean up provider {provider.id}: {e}")
        self._providers.clear()
        logger.info("Cleaned up all providers")


# Global registry instance
_registry = UnifiedProviderRegistry()


def get_registry() -> UnifiedProviderRegistry:
    """Get the global provider registry.

    Returns:
        Global provider registry instance
    """
    return _registry


__all__ = [
    "BaseProvider",
    "ProviderConfig",
    "ProviderError",
    "ProviderNotFoundError",
    "UnifiedProviderRegistry",
    "get_registry",
]
