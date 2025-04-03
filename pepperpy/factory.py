"""Factory module for creating PepperPy components and plugins.

This module provides convenient factory functions for creating instances
of plugins and components in the PepperPy framework.
"""

from typing import Any, TypeVar, cast

from pepperpy.core.config_manager import get_default_provider
from pepperpy.core.errors import ProviderError
from pepperpy.core.logging import get_logger
from pepperpy.plugins.plugin import PepperpyPlugin
from pepperpy.plugins.registry import get_plugin

logger = get_logger(__name__)

T = TypeVar("T", bound=PepperpyPlugin)


def create_plugin(
    plugin_type: str,
    provider_type: str | None = None,
    **config: Any,
) -> T:
    """Create a plugin instance.

    Args:
        plugin_type: Type of plugin (e.g., "llm", "tts", "rag")
        provider_type: Provider type, will use default if not provided
        **config: Additional configuration for the plugin

    Returns:
        Initialized plugin instance

    Raises:
        ProviderError: If provider cannot be created or no default is available
    """
    try:
        # If provider_type not specified, get default from config
        if not provider_type:
            provider_type = get_default_provider(plugin_type)
            if not provider_type:
                raise ProviderError(f"No default provider found for {plugin_type}")
            logger.debug(f"Using default provider {provider_type} for {plugin_type}")

        # Get provider instance from registry
        provider = get_plugin(plugin_type, provider_type, **config)

        if not provider:
            raise ProviderError(f"No provider found for {plugin_type}/{provider_type}")

        return cast(T, provider)
    except Exception as e:
        raise ProviderError(f"Failed to create plugin {plugin_type}: {e}") from e


# Convenience factory functions for different plugin types
def create_llm(**config: Any) -> T:
    """Create an LLM provider.

    Args:
        **config: Provider configuration

    Returns:
        LLM provider instance
    """
    return create_plugin("llm", **config)


def create_embeddings(**config: Any) -> T:
    """Create an embeddings provider.

    Args:
        **config: Provider configuration

    Returns:
        Embeddings provider instance
    """
    return create_plugin("embeddings", **config)


def create_storage(**config: Any) -> T:
    """Create a storage provider.

    Args:
        **config: Provider configuration

    Returns:
        Storage provider instance
    """
    return create_plugin("storage", **config)


def create_rag(**config: Any) -> T:
    """Create a RAG provider.

    Args:
        **config: Provider configuration

    Returns:
        RAG provider instance
    """
    return create_plugin("rag", **config)


def create_tts(**config: Any) -> T:
    """Create a TTS provider.

    Args:
        **config: Provider configuration

    Returns:
        TTS provider instance
    """
    return create_plugin("tts", **config)


def create_content(**config: Any) -> T:
    """Create a content provider.

    Args:
        **config: Provider configuration

    Returns:
        Content provider instance
    """
    return create_plugin("content", **config)


def create_workflow(**config: Any) -> T:
    """Create a workflow provider.

    Args:
        **config: Provider configuration

    Returns:
        Workflow provider instance
    """
    return create_plugin("workflow", **config)


def create_agent(**config: Any) -> T:
    """Create an agent provider.

    Args:
        **config: Provider configuration

    Returns:
        Agent provider instance
    """
    return create_plugin("agent", **config)


def get_plugin_class(plugin_type: str, provider_type: str) -> type[PepperpyPlugin]:
    """Get the plugin class for a specific provider type.

    Args:
        plugin_type: Type of plugin
        provider_type: Type of provider

    Returns:
        Plugin class

    Raises:
        ProviderError: If provider class cannot be found
    """
    try:
        # Get provider instance from registry
        provider = get_plugin(plugin_type, provider_type)

        if not provider:
            raise ProviderError(f"No provider found for {plugin_type}/{provider_type}")

        return cast(type[PepperpyPlugin], provider.__class__)
    except Exception as e:
        raise ProviderError(
            f"Failed to get provider class for {plugin_type}/{provider_type}: {e}"
        ) from e
