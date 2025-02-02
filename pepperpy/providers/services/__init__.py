"""Service providers for the Pepperpy library.

This module contains the implementation of various service providers
that can be used with Pepperpy, such as OpenAI, Anthropic, etc.

This module also provides common functionality for provider implementations,
reducing code duplication and standardizing error handling.
"""

from typing import Final

from pepperpy.common.errors import ProviderError
from pepperpy.monitoring import logger

from ..domain import ProviderInitError
from ..engine import ProviderEngine
from ..provider import Provider

# Provider types
OPENAI: Final[str] = "openai"
ANTHROPIC: Final[str] = "anthropic"
OPENROUTER: Final[str] = "openrouter"
GEMINI: Final[str] = "gemini"
STACKSPOT: Final[str] = "stackspot"

REQUIRED_PROVIDERS: Final[list[str]] = [OPENAI]
OPTIONAL_PROVIDERS: Final[list[str]] = [
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

        ProviderEngine.register_provider(OPENAI, OpenAIProvider)
        registered[OPENAI] = OpenAIProvider
    except ImportError as e:
        raise ProviderInitError(f"Required provider 'openai' not available: {e}") from e

    # Register optional providers
    try:
        from .gemini import GeminiProvider

        ProviderEngine.register_provider(GEMINI, GeminiProvider)
        registered[GEMINI] = GeminiProvider
    except ImportError as e:
        logger.warning("Optional provider not available", provider=GEMINI, error=str(e))

    try:
        from .openrouter import OpenRouterProvider

        ProviderEngine.register_provider(OPENROUTER, OpenRouterProvider)
        registered[OPENROUTER] = OpenRouterProvider
    except ImportError as e:
        logger.warning(
            "Optional provider not available", provider=OPENROUTER, error=str(e)
        )

    try:
        from .stackspot import StackSpotProvider

        ProviderEngine.register_provider(STACKSPOT, StackSpotProvider)
        registered[STACKSPOT] = StackSpotProvider
    except ImportError as e:
        logger.warning(
            "Optional provider not available", provider=STACKSPOT, error=str(e)
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
    "register_providers",
]
