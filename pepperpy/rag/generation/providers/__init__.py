"""Provider implementations for generation components.

This module provides concrete implementations of generation components using various
third-party libraries and services.
"""

from typing import Dict

from pepperpy.core.logging import get_logger
from pepperpy.rag.generation import Generator

logger = get_logger(__name__)

# Registry of generation providers
_generation_providers: Dict[str, Generator] = {}


def register_generation_provider(provider_id: str, provider: Generator) -> None:
    """Register a generation provider.

    Args:
        provider_id: Unique identifier for the provider
        provider: The provider to register
    """
    if provider_id in _generation_providers:
        logger.warning(f"Generation provider already registered with ID: {provider_id}")

    _generation_providers[provider_id] = provider
    logger.debug(f"Registered generation provider: {provider_id}")


def get_generation_provider(provider_id: str) -> Generator:
    """Get a generation provider by ID.

    Args:
        provider_id: The ID of the provider to get

    Returns:
        The provider if found

    Raises:
        ValueError: If the provider is not found
    """
    provider = _generation_providers.get(provider_id)
    if provider is None:
        raise ValueError(f"Generation provider not found: {provider_id}")

    return provider
