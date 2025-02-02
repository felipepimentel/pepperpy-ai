"""Provider base class and configuration.

This module defines the base Provider class that all providers must implement,
along with the configuration model used to initialize providers.

Example:
    >>> from pepperpy.providers import Provider, ProviderConfig
    >>> class MyProvider(Provider):
    ...     async def initialize(self) -> None:
    ...         # Provider-specific initialization
    ...         pass
    ...     async def complete(self, prompt: str) -> str:
    ...         # Provider-specific completion
    ...         return "Response"
"""

# Standard library imports
import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, AsyncIterator
from datetime import datetime
from typing import Any, ClassVar, Final

# Third-party imports
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Local imports
from pepperpy.common.errors import ProviderConfigError, ProviderError
from pepperpy.monitoring import logger


class ProviderConfig(BaseSettings):
    """Configuration for a provider.

    Attributes:
        provider_type: The type of provider.
        api_key: The API key for authentication.
        model: The model to use.
        max_retries: Maximum number of retries for failed requests.
        timeout: Timeout in seconds for requests.
        enabled_providers: List of enabled provider types.
        rate_limits: Rate limits per provider type.
    """

    provider_type: str = Field(
        description="Type of provider (e.g., 'openai', 'gemini')"
    )
    api_key: SecretStr = Field(description="API key for the provider")
    model: str = Field(description="Model to use (provider-specific)")
    max_retries: int = Field(
        3, description="Maximum number of retries for failed calls", ge=0
    )
    timeout: int = Field(30, description="Request timeout in seconds", ge=1)
    enabled_providers: list[str] = Field(
        default_factory=list, description="List of enabled provider types"
    )
    rate_limits: dict[str, int] = Field(
        default_factory=dict, description="Rate limits per provider type"
    )

    model_config = SettingsConfigDict(
        env_prefix="PEPPERPY_PROVIDER__",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        validate_assignment=True,
        extra="allow",
        env_nested_delimiter="__",
        json_schema_extra={"examples": []},
        secrets_dir=None,
    )


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
            ProviderConfigError: If required fields are missing.

        Example:
            >>> config = ProviderConfig(
            ...     provider_type="test",
            ...     api_key="your-api-key"
            ... )
            >>> provider = MyProvider(config=config)
        """
        if not config:
            raise ValueError("Config cannot be None")

        if not config.api_key or not config.api_key.get_secret_value():
            raise ProviderError(
                "API key is required",
                provider_type=config.provider_type,
                details={"field": "api_key"},
            )

        if not config.provider_type:
            raise ProviderError(
                "Provider type is required",
                provider_type=config.provider_type,
                details={"field": "provider_type"},
            )

        self.config = config
        self._initialized = False
        self._lock = asyncio.Lock()

        logger.debug(
            "Provider instance created",
            extra={
                "provider_type": config.provider_type,
                "model": config.model,
                "timeout": config.timeout,
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
