"""Provider implementations for indexing components.

This module provides concrete implementations of indexing components using various
third-party libraries and services.
"""

from typing import Dict

from pepperpy.core.logging import get_logger
from pepperpy.rag.indexing import DocumentIndexer

logger = get_logger(__name__)

# Registry of indexing providers
_indexing_providers: Dict[str, DocumentIndexer] = {}


def register_indexing_provider(provider_id: str, provider: DocumentIndexer) -> None:
    """Register an indexing provider.

    Args:
        provider_id: Unique identifier for the provider
        provider: The provider to register
    """
    if provider_id in _indexing_providers:
        logger.warning(f"Indexing provider already registered with ID: {provider_id}")

    _indexing_providers[provider_id] = provider
    logger.debug(f"Registered indexing provider: {provider_id}")


def get_indexing_provider(provider_id: str) -> DocumentIndexer:
    """Get an indexing provider by ID.

    Args:
        provider_id: The ID of the provider to get

    Returns:
        The provider if found

    Raises:
        ValueError: If the provider is not found
    """
    provider = _indexing_providers.get(provider_id)
    if provider is None:
        raise ValueError(f"Indexing provider not found: {provider_id}")

    return provider
