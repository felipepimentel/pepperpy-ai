"""Base provider interface for the Pepperpy framework.

This module defines the core interfaces and base classes that all providers
must implement, ensuring consistent behavior across different implementations.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any, TypeVar

from pydantic import BaseModel, Field, SecretStr

from pepperpy.core.types import Message, Response
from pepperpy.monitoring import logger
from pepperpy.monitoring.logger import ContextLogger
from pepperpy.providers.domain import (
    ProviderError,
    ProviderInitError,
)

T = TypeVar("T", covariant=True)


class ProviderConfig(BaseModel):
    """Base configuration for providers."""

    provider_type: str = Field(..., description="Type of provider")
    api_key: SecretStr = Field(..., description="API key for authentication")
    model: str = Field(..., description="Model to use")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    max_tokens: int = Field(default=2048, description="Maximum tokens per request")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    extra_config: dict[str, Any] = Field(
        default_factory=dict, description="Additional configuration"
    )


class BaseProvider(ABC):
    """Base class for all providers.

    All providers must inherit from this class and implement its abstract methods
    to ensure consistent behavior across different implementations.

    Attributes:
        config (ProviderConfig): Provider configuration
        name (str): Provider name (class name)
        _initialized (bool): Whether the provider is initialized
        _logger (ContextLogger): Logger instance with context support
    """

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize provider with configuration.

        Args:
            config: Provider configuration
        """
        self.config = config
        self.name = self.__class__.__name__
        self._initialized = False
        self._logger: ContextLogger = logger

    def _ensure_initialized(self) -> None:
        """Ensure the provider is initialized.

        Raises:
            ProviderInitError: If the provider is not initialized
        """
        if not self._initialized:
            raise ProviderInitError(
                "Provider not initialized",
                provider_type=self.config.provider_type,
            )

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize provider resources.

        This method should handle any setup required before the provider
        can be used, such as validating credentials or establishing connections.

        Raises:
            ProviderInitError: If initialization fails due to provider state
            ProviderConfigError: If configuration is invalid
            ProviderAPIError: If API connection fails
        """
        self._initialized = True

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method should handle proper cleanup of any resources used
        by the provider, such as closing connections.

        Raises:
            ProviderError: If cleanup fails
        """
        self._initialized = False

    @abstractmethod
    async def generate(self, messages: list[Message], **kwargs: Any) -> Response:
        """Generate a response from the provider.

        Args:
            messages: List of messages to generate from
            **kwargs: Additional arguments to pass to the provider

        Returns:
            Generated response

        Raises:
            ProviderInitError: If the provider is not initialized
            ProviderAPIError: If the API request fails
            ProviderError: If generation fails for other reasons
        """
        self._ensure_initialized()
        raise NotImplementedError

    @abstractmethod
    def stream(self, messages: list[Message], **kwargs: Any) -> AsyncIterator[Response]:
        """Stream responses from the provider.

        Args:
            messages: List of messages to generate from
            **kwargs: Additional arguments to pass to the provider

        Returns:
            AsyncIterator[Response]: Stream of responses

        Raises:
            ProviderInitError: If the provider is not initialized
            ProviderAPIError: If the API request fails
            ProviderError: If streaming fails for other reasons
        """
        self._ensure_initialized()
        raise NotImplementedError

    async def _handle_api_error(
        self, error: Exception, context: dict[str, Any]
    ) -> None:
        """Handle API errors in a standardized way.

        Args:
            error: The original error
            context: Additional context about the error

        Raises:
            ProviderError: With appropriate error details
        """
        self._logger.error(
            "API error occurred",
            extra={"error": str(error), "provider": self.name, **context},
        )
        raise ProviderError(
            message=str(error), provider_type=self.name, details=context
        ) from error

    def _check_initialized(self) -> None:
        """Check if provider is initialized.

        Raises:
            RuntimeError: If provider is not initialized
        """
        if not self._initialized:
            raise RuntimeError(
                f"Provider {self.name} not initialized. Call initialize() first."
            )

    async def __aenter__(self) -> "BaseProvider":
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.cleanup()
