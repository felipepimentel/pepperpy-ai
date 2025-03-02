"""Provider implementations for retrieval components.

This module provides concrete implementations of retrieval components using various
third-party libraries and services.
"""

from typing import Dict

from pepperpy.core.logging import get_logger
from pepperpy.rag.retrieval import Retriever

logger = get_logger(__name__)

# Registry of retrieval providers
_retrieval_providers: Dict[str, Retriever] = {}


def register_retrieval_provider(provider_id: str, provider: Retriever) -> None:
    """Register a retrieval provider.

    Args:
        provider_id: Unique identifier for the provider
        provider: The provider to register
    """
    if provider_id in _retrieval_providers:
        logger.warning(f"Retrieval provider already registered with ID: {provider_id}")

    _retrieval_providers[provider_id] = provider
    logger.debug(f"Registered retrieval provider: {provider_id}")


def get_retrieval_provider(provider_id: str) -> Retriever:
    """Get a retrieval provider by ID.

    Args:
        provider_id: The ID of the provider to get

    Returns:
        The provider if found

    Raises:
        ValueError: If the provider is not found
    """
    provider = _retrieval_providers.get(provider_id)
    if provider is None:
        raise ValueError(f"Retrieval provider not found: {provider_id}")

    return provider
