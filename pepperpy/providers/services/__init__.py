"""Service providers for the Pepperpy library.

This module contains the implementation of various service providers
that can be used with Pepperpy, such as OpenAI, Anthropic, etc.

This module also provides common functionality for provider implementations,
reducing code duplication and standardizing error handling.
"""

from typing import Final, cast

from pepperpy.common.errors import ProviderError
from pepperpy.monitoring import logger

from ..base import BaseProvider, ProviderConfig
from ..domain import ProviderInitError
from ..engine import ProviderEngine
from ..provider import Provider
from .anthropic import AnthropicConfig, AnthropicProvider
from .gemini import GeminiConfig, GeminiProvider
from .openai import OpenAIConfig, OpenAIProvider
from .openrouter import OpenRouterProvider
from .stackspot import StackSpotProvider

# Provider types
OPENAI: Final[str] = "openai"
ANTHROPIC: Final[str] = "anthropic"
OPENROUTER: Final[str] = "openrouter"
GEMINI: Final[str] = "gemini"
STACKSPOT: Final[str] = "stackspot"

REQUIRED_PROVIDERS: Final[list[str]] = [OPENAI]
OPTIONAL_PROVIDERS: Final[list[str]] = [
    ANTHROPIC,
    GEMINI,
    OPENROUTER,
    STACKSPOT,
]

# Track registered providers
REGISTERED_PROVIDERS: dict[str, type[Provider]] = {}


def register_providers() -> dict[str, type[Provider]]:
    """Register all available providers."""
    registered: dict[str, type[Provider]] = {}

    # Register required providers
    try:
        from .openai import OpenAIProvider

        provider_class = cast(type[Provider], OpenAIProvider)
        ProviderEngine.register_provider(OPENAI, provider_class)
        registered[OPENAI] = provider_class
    except ImportError as e:
        raise ProviderInitError(f"Required provider 'openai' not available: {e}") from e

    # Register optional providers
    try:
        from .gemini import GeminiProvider

        provider_class = cast(type[Provider], GeminiProvider)
        ProviderEngine.register_provider(GEMINI, provider_class)
        registered[GEMINI] = provider_class
    except ImportError as e:
        logger.warning(
            "Optional provider not available",
            extra={"provider": GEMINI, "error": str(e)},
        )

    try:
        from pepperpy.providers.services.openrouter import OpenRouterProvider

        provider_class = cast(type[Provider], OpenRouterProvider)
        ProviderEngine.register_provider(OPENROUTER, provider_class)
        registered[OPENROUTER] = provider_class
    except ImportError as e:
        logger.warning(
            "Failed to import OpenRouter provider",
            extra={"error": str(e)},
        )

    try:
        from .stackspot import StackSpotProvider

        provider_class = cast(type[Provider], StackSpotProvider)
        ProviderEngine.register_provider(STACKSPOT, provider_class)
        registered[STACKSPOT] = provider_class
    except ImportError as e:
        logger.warning(
            "Optional provider not available",
            extra={"provider": STACKSPOT, "error": str(e)},
        )

    return registered


# Register providers on module import
REGISTERED_PROVIDERS.update(register_providers())


__all__ = [
    "GEMINI",
    "OPENAI",
    "OPENROUTER",
    "OPTIONAL_PROVIDERS",
    "REGISTERED_PROVIDERS",
    "REQUIRED_PROVIDERS",
    "STACKSPOT",
    "AnthropicConfig",
    "AnthropicProvider",
    "BaseProvider",
    "GeminiConfig",
    "GeminiProvider",
    "OpenAIConfig",
    "OpenAIProvider",
    "OpenRouterProvider",
    "ProviderConfig",
    "ProviderError",
    "StackSpotProvider",
    "register_providers",
]
