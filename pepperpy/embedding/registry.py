"""Registry for embedding providers."""

from typing import Dict, List, Type

from pepperpy.embedding.base import BaseEmbedding

# Registry of embedding providers
_EMBEDDING_REGISTRY: Dict[str, Type[BaseEmbedding]] = {}


def register_embedding(name: str, embedding_class: Type[BaseEmbedding]) -> None:
    """Register an embedding provider class.

    Args:
        name: Name of the embedding provider
        embedding_class: Embedding provider class
    """
    _EMBEDDING_REGISTRY[name] = embedding_class


def get_embedding_class(name: str) -> Type[BaseEmbedding]:
    """Get an embedding provider class by name.

    Args:
        name: Name of the embedding provider

    Returns:
        Type[BaseEmbedding]: Embedding provider class

    Raises:
        ValueError: If embedding provider is not found
    """
    if name not in _EMBEDDING_REGISTRY:
        raise ValueError(f"Embedding provider '{name}' not found in registry")
    return _EMBEDDING_REGISTRY[name]


def list_embeddings() -> List[str]:
    """List all registered embedding providers.

    Returns:
        List[str]: List of embedding provider names
    """
    return list(_EMBEDDING_REGISTRY.keys())


def get_embedding_registry() -> Dict[str, Type[BaseEmbedding]]:
    """Get the embedding provider registry.

    Returns:
        Dict[str, Type[BaseEmbedding]]: Copy of the embedding provider registry
    """
    return _EMBEDDING_REGISTRY.copy()
