"""Core provider interfaces and base classes.

This module defines the base provider interfaces and classes used throughout
the Pepperpy framework. It includes:
- Base provider interface
- Provider configuration
- Provider management
- Error handling
"""

import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any, Dict, Optional, TypeVar, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from pepperpy.core.errors import ConfigurationError
from pepperpy.core.logging import get_logger
from pepperpy.core.messages import ProviderMessage, ProviderResponse

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

    pass


class ProviderNotFoundError(ProviderError):
    """Error raised when provider is not found."""

    pass


class BaseProvider(ABC):
    """Base provider interface.

    All providers must implement this interface to ensure consistent
    behavior across the framework.
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
    async def process_message(
        self,
        message: ProviderMessage,
    ) -> Union[ProviderResponse, AsyncGenerator[ProviderResponse, None]]:
        """Process a provider message.

        Args:
            message: Provider message to process

        Returns:
            Provider response or async generator of responses

        Raises:
            ProviderError: If message processing fails
            ConfigurationError: If provider is not initialized
        """
        pass

    @property
    def is_initialized(self) -> bool:
        """Whether the provider is initialized."""
        return self._initialized


class ProviderManager:
    """Provider management system.

    This class handles provider registration, creation, and lifecycle
    management.
    """

    def __init__(self) -> None:
        """Initialize provider manager."""
        self._providers: Dict[str, BaseProvider] = {}
        self._lock = asyncio.Lock()

    async def get_provider(
        self, type: str, config: Optional[Dict[str, Any]] = None
    ) -> BaseProvider:
        """Get or create a provider instance.

        Args:
            type: Provider type identifier
            config: Optional provider configuration

        Returns:
            Provider instance

        Raises:
            ProviderNotFoundError: If provider type is not found
            ConfigurationError: If provider configuration is invalid
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
                if isinstance(e, (ProviderNotFoundError, ConfigurationError)):
                    raise
                raise ConfigurationError(f"Failed to get provider: {e}")

    async def _create_provider(self, config: ProviderConfig) -> BaseProvider:
        """Create a new provider instance.

        Args:
            config: Provider configuration

        Returns:
            Provider instance

        Raises:
            ProviderNotFoundError: If provider type is not found
            ConfigurationError: If provider configuration is invalid
        """
        # TODO: Implement provider creation logic
        raise NotImplementedError("Provider creation not implemented")
