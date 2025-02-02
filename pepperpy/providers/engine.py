"""Engine for managing and creating providers.

This module implements the singleton pattern to ensure consistent provider
management across the application. It maintains a registry of provider types
and handles provider instantiation.

Example:
    >>> from pepperpy.providers import ProviderEngine
    >>> engine = ProviderEngine()
    >>> providers = engine.list_providers()
    >>> assert "openai" in providers
"""

from typing import Any, ClassVar, Final, cast

from pepperpy.monitoring import logger

from .domain import ProviderConfigError, ProviderError, ProviderNotFoundError
from .provider import Provider, ProviderConfig

DEFAULT_TIMEOUT: Final[float] = 30.0


class ProviderEngine:
    """Engine for managing and creating providers.

    This class implements the singleton pattern to ensure consistent
    provider management across the application. It maintains a registry
    of provider types and handles provider instantiation.

    Attributes:
        _instance: Singleton instance of the engine
        _providers: Registry of provider types and their classes

    Example:
        >>> engine = ProviderEngine()
        >>> providers = engine.list_providers()
        >>> assert "openai" in providers
    """

    _instance: ClassVar["ProviderEngine | None"] = None
    _providers: ClassVar[dict[str, type[Provider]]] = {}

    def __new__(cls) -> "ProviderEngine":
        """Singleton pattern implementation.

        Returns:
            The singleton instance of ProviderEngine

        Example:
            >>> engine1 = ProviderEngine()
            >>> engine2 = ProviderEngine()
            >>> assert engine1 is engine2
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register_provider(
        cls, provider_type: str, provider_class: type[Provider]
    ) -> None:
        """Register a provider class.

        Args:
            provider_type: Type identifier for the provider
            provider_class: Provider class to register

        Raises:
            ValueError: If provider_type is empty or provider_class is None
            ProviderError: If provider_type is already registered

        Example:
            >>> ProviderEngine.register_provider("openai", OpenAIProvider)
        """
        if not provider_type:
            raise ValueError("Provider type cannot be empty")

        if provider_class is None:
            raise ValueError("Provider class cannot be None")

        if provider_type in cls._providers:
            raise ProviderError(
                f"Provider '{provider_type}' is already registered",
                provider_type=provider_type,
            )

        cls._providers[provider_type] = provider_class
        logger.info(
            "Registered provider '%s' (class: %s)",
            provider_type,
            provider_class.__name__,
        )

    @classmethod
    def create_provider(
        cls,
        provider_type: str,
        api_key: str | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        **config_kwargs: Any,
    ) -> Provider:
        """Create a provider instance.

        Args:
            provider_type: Type of provider to create
            api_key: API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed calls
            **config_kwargs: Additional configuration parameters

        Returns:
            Provider instance

        Raises:
            ProviderNotFoundError: If provider type is not registered
            ProviderConfigError: If configuration is invalid
            ValueError: If provider_type is empty

        Example:
            >>> provider = ProviderEngine.create_provider(
            ...     "openai",
            ...     api_key="your-api-key",
            ...     timeout=30
            ... )
        """
        if not provider_type:
            raise ValueError("Provider type cannot be empty")

        if provider_type not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ProviderNotFoundError(
                f"Provider '{provider_type}' not found. "
                f"Available providers: {available}",
                provider_type=provider_type,
            )

        config_data = {
            "provider_type": provider_type,
            "timeout": timeout,
            "max_retries": max_retries,
            **config_kwargs,
        }

        if api_key is not None:
            config_data["api_key"] = api_key

        try:
            config = ProviderConfig(**config_data)
        except Exception as e:
            raise ProviderConfigError(
                f"Invalid configuration for provider '{provider_type}': {e!s}",
                provider_type=provider_type,
                details={"error": str(e), "config": config_data},
            ) from e

        provider_class = cls._providers[provider_type]
        provider = provider_class(config)

        logger.debug(
            "Created provider instance '%s' (class: %s)",
            provider_type,
            provider_class.__name__,
        )

        return provider

    @classmethod
    def list_providers(cls) -> list[str]:
        """List available provider types.

        Returns:
            List of registered provider types

        Example:
            >>> ProviderEngine.register_provider("openai", OpenAIProvider)
            >>> providers = ProviderEngine.list_providers()
            >>> assert "openai" in providers
            >>> assert isinstance(providers, list)
        """
        return sorted(cls._providers.keys())


def create_provider(
    provider_type: str,
    api_key: str | None = None,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = 3,
    **config_kwargs: Any,
) -> Provider:
    """Create a provider instance.

    This is a convenience function that delegates to ProviderEngine.
    See ProviderEngine.create_provider for full documentation.

    Example:
        >>> provider = create_provider(
        ...     "openai",
        ...     api_key="your-api-key",
        ...     timeout=30
        ... )
    """
    return ProviderEngine().create_provider(
        provider_type,
        api_key,
        timeout=timeout,
        max_retries=max_retries,
        **config_kwargs,
    )


def list_providers() -> list[str]:
    """List available provider types.

    This is a convenience function that delegates to ProviderEngine.
    See ProviderEngine.list_providers for full documentation.

    Example:
        >>> providers = list_providers()
        >>> assert isinstance(providers, list)
    """
    return ProviderEngine.list_providers()
