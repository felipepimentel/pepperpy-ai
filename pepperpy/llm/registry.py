"""LLM provider registry for PepperPy.

This module provides a registry for LLM providers in the PepperPy framework.
It uses the core registry system to manage LLM provider classes and instances.

Example:
    ```python
    from pepperpy.llm.registry import register_provider, get_provider
    from pepperpy.llm.providers.openai import OpenAIProvider

    # Register a provider
    register_provider("openai", OpenAIProvider)

    # Create a provider instance
    provider = get_provider("openai", api_key="your-api-key")

    # Use the provider
    response = await provider.generate("Hello, world!")
    ```
"""

from typing import Any, Dict, List, Optional, Type

from pepperpy.core.errors import NotFoundError, PepperPyError
from pepperpy.core.registry import ProviderRegistry
from pepperpy.utils.logging import get_logger

logger = get_logger(__name__)

# Avoid circular imports
# We'll use typing.TYPE_CHECKING and string literals for type hints
LLMProvider = Any  # Placeholder for actual type
LLMResult = Any  # Placeholder for actual type

# LLM provider registry
llm_provider_registry = ProviderRegistry[LLMProvider](
    registry_name="llm_provider_registry", registry_type="llm_provider"
)


def register_provider(name: str, provider_class: Type[LLMProvider]) -> None:
    """Register an LLM provider class.

    Args:
        name: The name of the provider
        provider_class: The provider class to register

    Raises:
        RegistryError: If a provider with the same name is already registered
    """
    llm_provider_registry.register_provider("llm", name, provider_class)


def get_provider(
    name: str, create_if_missing: bool = True, **kwargs: Any
) -> LLMProvider:
    """Get an LLM provider instance.

    Args:
        name: The name of the provider
        create_if_missing: Whether to create the provider if it doesn't exist
        **kwargs: Provider-specific configuration

    Returns:
        An LLM provider instance

    Raises:
        NotFoundError: If the provider is not found
    """
    try:
        if create_if_missing:
            return llm_provider_registry.create_provider("llm", name, **kwargs)
        # Use get_provider_class and instantiate manually since get_provider doesn't exist
        provider_class = llm_provider_registry.get_provider_class("llm", name)
        return provider_class(**kwargs)
    except Exception as e:
        logger.error(f"Error getting LLM provider: {e}")
        if isinstance(e, PepperPyError):
            raise
        raise NotFoundError(f"Failed to get LLM provider: {e}") from e


def list_providers() -> List[str]:
    """List all registered LLM provider types.

    Returns:
        A list of registered LLM provider names
    """
    providers = llm_provider_registry.list_providers("llm")
    return providers.get("llm", [])


async def generate(
    prompt: str,
    provider_name: str = "openai",
    options: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> LLMResult:
    """Generate text using an LLM provider.

    Args:
        prompt: The prompt to generate text from
        provider_name: The name of the provider to use
        options: Optional generation options
        **kwargs: Additional arguments to pass to the provider

    Returns:
        The generated text result

    Raises:
        PepperPyError: If there is an error generating text
    """
    try:
        provider = get_provider(provider_name, **kwargs)
        options = options or {}
        result = await provider.generate(prompt, **options)
        return result
    except Exception as e:
        logger.error(f"Error generating text: {e}")
        if isinstance(e, PepperPyError):
            raise
        raise PepperPyError(f"Failed to generate text: {e}") from e


__all__ = [
    "generate",
    "get_provider",
    "list_providers",
    "register_provider",
]
