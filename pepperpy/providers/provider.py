"""Base provider interface and configuration for Pepperpy.

This module defines the base provider interface that all providers must implement,
as well as the standard configuration structure.
"""

# Standard library imports
import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any, Final

# Third-party imports
from pydantic import BaseModel, Field, SecretStr, field_validator

# Local imports
from pepperpy.common.errors import ProviderError
from pepperpy.monitoring import logger

VALID_PROVIDER_TYPES: Final[set[str]] = {
    "openai",
    "anthropic",
    "stackspot",
    "gemini",
}


class ProviderConfig(BaseModel):
    """Configuration for a provider."""

    provider_type: str = Field(description="The type of provider")
    api_key: SecretStr | None = Field(
        default=None, description="The API key for the provider"
    )
    model: str = Field(description="The model to use")
    max_retries: int = Field(
        default=3, ge=0, description="Maximum number of retries for failed requests"
    )
    timeout: int = Field(default=30, gt=0, description="Request timeout in seconds")
    extra_config: dict[str, Any] = Field(default_factory=dict)

    @field_validator("provider_type")
    def validate_provider_type(self, v: str) -> str:
        """Validate provider type.

        Args:
            v: Provider type to validate.

        Returns:
            Validated provider type.

        Raises:
            ValueError: If provider type is invalid.
        """
        if v not in VALID_PROVIDER_TYPES:
            raise ValueError(f"Invalid provider type: {v}")
        return v

    @field_validator("api_key")
    def validate_api_key(self, v: SecretStr | None) -> SecretStr | None:
        """Validate API key.

        Args:
            v: API key to validate.

        Returns:
            Validated API key.

        Raises:
            ValueError: If API key is invalid.
        """
        if v is None:
            return None
        if not v.get_secret_value():
            raise ValueError("API key cannot be empty")
        return v


class BaseProvider(ABC):
    """Base class for all providers.

    All providers must inherit from this class and implement its abstract methods
    to ensure consistent behavior across different implementations.
    """

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the provider.

        Args:
            config: Provider configuration
        """
        self.config = config

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider.

        This method should handle any setup required before the provider
        can be used, such as validating credentials or establishing connections.
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method should handle proper cleanup of any resources used
        by the provider, such as closing connections.
        """
        pass

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        """Complete a prompt using this provider.

        Args:
            prompt: The prompt to complete
            temperature: Sampling temperature
            stream: Whether to stream the response

        Returns:
            Either a string response or an async generator for streaming
        """
        pass


class Provider(ABC):
    """Base provider class.

    All providers must inherit from this class and implement the required methods.
    """

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the provider with configuration.

        Args:
            config: Provider configuration.

        Raises:
            ValueError: If config is None.
            ProviderError: If required fields are missing.

        Example:
            >>> config = ProviderConfig(
            ...     provider_type="test",
            ...     api_key="your-api-key"
            ... )
            >>> provider = MyProvider(config=config)
        """
        if not config:
            raise ValueError("Config cannot be None")

        if not config.provider_type:
            raise ValueError("Provider type cannot be empty")

        if not config.api_key:
            raise ProviderError(
                "API key is required",
                provider_type=config.provider_type,
                details={"field": "api_key"},
            )

        self.config = config
        self._initialized = False
        self._lock = asyncio.Lock()

        logger.debug(
            "Provider instance created",
            extra={
                "provider_type": self.config.provider_type,
                "model": self.config.model,
            },
        )

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider.

        This method should be called before any other methods.
        It should handle any setup required by the provider.

        Raises:
            ProviderError: If initialization fails

        Example:
            >>> await provider.initialize()
        """
        self._initialized = True

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> str | AsyncGenerator[str, None]:
        """Complete a prompt using the provider's model.

        Args:
            prompt: The prompt to complete
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text or async generator of text chunks if streaming

        Raises:
            ProviderError: If the API call fails or rate limit is exceeded
            RuntimeError: If provider is not initialized

        Example:
            >>> response = await provider.complete(
            ...     "Tell me a joke",
            ...     temperature=0.3
            ... )
        """
        ...

    @abstractmethod
    async def embed(self, text: str, **kwargs: Any) -> list[float]:
        """Generate embeddings for text using the provider's model.

        Args:
            text: Text to embed
            **kwargs: Additional provider-specific parameters

        Returns:
            List of embedding values as floats

        Raises:
            ProviderError: If the API call fails
            RuntimeError: If provider is not initialized

        Example:
            >>> embeddings = await provider.embed("Hello world")
            >>> print(f"Embedding dimension: {len(embeddings)}")
        """
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up provider resources.

        Override this method to handle any cleanup needed.
        By default, this method does nothing.

        Example:
            >>> await provider.cleanup()
        """
        ...

    def _check_initialized(self) -> None:
        """Check if provider is initialized.

        Raises:
            RuntimeError: If provider is not initialized

        Example:
            >>> provider._check_initialized()  # Raises if not initialized
        """
        if not self._initialized:
            raise RuntimeError(
                "Provider not initialized. "
                "Call initialize() or use async with context manager."
            )

    async def __aenter__(self) -> "Provider":
        """Async context manager entry.

        Returns:
            The initialized provider instance

        Raises:
            ProviderError: If initialization fails

        Example:
            >>> async with provider:
            ...     response = await provider.complete("Hello!")
        """
        await self.initialize()
        return self

    async def __aexit__(
        self, exc_type: type | None, exc_val: Exception | None, exc_tb: Any | None
    ) -> None:
        """Async context manager exit.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        await self.cleanup()
