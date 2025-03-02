"""Registry for indexing providers.

This module provides a registry for indexing providers.
"""

from typing import TYPE_CHECKING, Dict, List

from pepperpy.core.logging import get_logger

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from pepperpy.rag.indexing.providers.base.base import IndexingProvider

logger = get_logger(__name__)

# Registry of indexing providers
_indexing_providers: Dict[str, "IndexingProvider"] = {}


def register_indexing_provider(provider_id: str, provider: "IndexingProvider") -> None:
    """Register an indexing provider.

    Args:
        provider_id: Unique identifier for the provider
        provider: The provider to register
    """
    if provider_id in _indexing_providers:
        logger.warning(f"Indexing provider already registered with ID: {provider_id}")

    _indexing_providers[provider_id] = provider
    logger.debug(f"Registered indexing provider: {provider_id}")


def get_indexing_provider(provider_id: str) -> "IndexingProvider":
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


def list_indexing_providers() -> List[str]:
    """List all registered indexing providers.

    Returns:
        A list of provider IDs
    """
    return list(_indexing_providers.keys())
