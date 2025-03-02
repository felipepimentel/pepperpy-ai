"""Registry for generation providers.

This module provides a registry for generation providers.
"""

from typing import TYPE_CHECKING, Dict, List

from pepperpy.core.logging import get_logger

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from pepperpy.rag.generation.providers.base.base import GenerationProvider

logger = get_logger(__name__)

# Registry of generation providers
_generation_providers: Dict[str, "GenerationProvider"] = {}


def register_generation_provider(
    provider_id: str, provider: "GenerationProvider"
) -> None:
    """Register a generation provider.

    Args:
        provider_id: Unique identifier for the provider
        provider: The provider to register
    """
    if provider_id in _generation_providers:
        logger.warning(f"Generation provider already registered with ID: {provider_id}")

    _generation_providers[provider_id] = provider
    logger.debug(f"Registered generation provider: {provider_id}")


def get_generation_provider(provider_id: str) -> "GenerationProvider":
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


def list_generation_providers() -> List[str]:
    """List all registered generation providers.

    Returns:
        A list of provider IDs
    """
    return list(_generation_providers.keys())
