"""Provider factory for creating provider instances.

This module provides factory functions for creating provider instances based on
configuration and provider type.
"""

from typing import Any, Dict, Optional, Type

from pepperpy.core.errors import ConfigurationError
from pepperpy.monitoring import bind_logger
from pepperpy.providers.base import VALID_PROVIDER_TYPES, BaseProvider
from pepperpy.providers.services.openai import OpenAIProvider
from pepperpy.providers.services.openrouter import OpenRouterProvider

# Configure logger
logger = bind_logger(module="providers.factory")

# Provider class mapping
PROVIDER_CLASSES: Dict[str, Type[BaseProvider]] = {
    "services.openai": OpenAIProvider,
    "services.openrouter": OpenRouterProvider,
}


def create_provider(
    provider_type: str,
    config: Dict[str, Any],
) -> BaseProvider:
    """Create a provider instance.

    Args:
        provider_type: Type of provider to create
        config: Provider configuration

    Returns:
        BaseProvider: Provider instance

    Raises:
        ConfigurationError: If provider type is unknown

    """
    if provider_type not in VALID_PROVIDER_TYPES:
        raise ConfigurationError(f"Unknown provider type: {provider_type}")

    provider_class = PROVIDER_CLASSES.get(provider_type)
    if not provider_class:
        raise ConfigurationError(
            f"Provider implementation not found for type: {provider_type}"
        )

    logger.info(f"Creating provider instance for type: {provider_type}")
    return provider_class(config)


def create_provider_factory(
    default_provider: str = "services.openrouter",
    default_config: Optional[Dict[str, Any]] = None,
) -> BaseProvider:
    """Create a provider factory with default configuration.

    Args:
        default_provider: Default provider type to use
        default_config: Default provider configuration

    Returns:
        BaseProvider: Provider instance

    Raises:
        ConfigurationError: If provider type is unknown

    """
    if default_config is None:
        default_config = {}

    return create_provider(default_provider, default_config)
