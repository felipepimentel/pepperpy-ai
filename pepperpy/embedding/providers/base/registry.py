"""Registry for embedding providers.

This module provides a registry for embedding providers.
"""

from typing import Dict, Type

from pepperpy.embedding.providers.base.base import BaseEmbeddingProvider

# Registry of embedding provider classes
_EMBEDDING_PROVIDER_REGISTRY: Dict[str, Type[BaseEmbeddingProvider]] = {}


def register_embedding_provider_class(
    name: str, provider_class: Type[BaseEmbeddingProvider],
) -> None:
    """Register an embedding provider class.

    Args:
        name: Name of the provider
        provider_class: Provider class to register

    """
    _EMBEDDING_PROVIDER_REGISTRY[name] = provider_class


def get_embedding_provider_class(name: str) -> Type[BaseEmbeddingProvider]:
    """Get an embedding provider class by name.

    Args:
        name: Name of the provider

    Returns:
        Type[BaseEmbeddingProvider]: Provider class

    Raises:
        ValueError: If provider is not found

    """
    if name not in _EMBEDDING_PROVIDER_REGISTRY:
        raise ValueError(f"Embedding provider '{name}' not found")
    return _EMBEDDING_PROVIDER_REGISTRY[name]


def list_embedding_providers() -> list[str]:
    """List all registered embedding providers.

    Returns:
        list[str]: List of provider names

    """
    return list(_EMBEDDING_PROVIDER_REGISTRY.keys())
