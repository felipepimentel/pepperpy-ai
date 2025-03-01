"""Factory for creating embedding components."""

from typing import Any, Dict, Optional

from pepperpy.embedding.base import BaseEmbedding, EmbeddingError
from pepperpy.embedding.registry import get_embedding_class


def create_embedding(
    provider: str, config: Optional[Dict[str, Any]] = None, **kwargs
) -> BaseEmbedding:
    """Create an embedding provider instance.

    Args:
        provider: Name of the embedding provider to create
        config: Optional configuration dictionary
        **kwargs: Additional provider-specific parameters

    Returns:
        BaseEmbedding: Embedding provider instance

    Raises:
        EmbeddingError: If provider creation fails
    """
    try:
        # Get provider class from registry
        provider_class = get_embedding_class(provider)

        # Merge config and kwargs
        provider_config = {}
        if config:
            provider_config.update(config)
        provider_config.update(kwargs)

        # Create provider instance
        return provider_class(**provider_config)
    except Exception as e:
        raise EmbeddingError(f"Failed to create embedding provider '{provider}': {e}")
