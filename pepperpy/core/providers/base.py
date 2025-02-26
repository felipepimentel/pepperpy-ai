"""Base provider interfaces and classes."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ProviderError(Exception):
    """Base exception for provider-related errors."""

    pass


class ConfigurationError(ProviderError):
    """Exception raised for provider configuration errors."""

    pass


class ProviderConfig(BaseModel):
    """Base configuration for providers."""

    name: str
    enabled: bool = True
    options: dict[str, Any] = {}


class Provider(ABC):
    """Base class for all providers."""

    def __init__(self, config: ProviderConfig):
        """Initialize provider with configuration.

        Args:
            config: Provider configuration
        """
        self.config = config
        self.initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider.

        This method should be called before using the provider.
        """
        self.initialized = True

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the provider.

        This method should be called when the provider is no longer needed.
        """
        self.initialized = False

    def _check_initialized(self) -> None:
        """Check if provider is initialized.

        Raises:
            ProviderError: If provider is not initialized
        """
        if not self.initialized:
            raise ProviderError("Provider not initialized")
