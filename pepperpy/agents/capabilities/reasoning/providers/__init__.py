"""Reasoning capability providers.

This module provides providers for reasoning capabilities.
"""

from pepperpy.agents.capabilities.reasoning.providers.base import BaseReasoningProvider
from pepperpy.agents.capabilities.reasoning.providers.registry import (
    get_reasoning_provider_class,
    register_reasoning_provider_class,
)
from pepperpy.agents.capabilities.reasoning.providers.types import (
    ReasoningResult,
    ReasoningStep,
    ReasoningType,
)

__all__ = [
    "BaseReasoningProvider",
    "ReasoningResult",
    "ReasoningStep",
    "ReasoningType",
    "get_reasoning_provider_class",
    "register_reasoning_provider_class",
]

from typing import Dict, Optional

from pepperpy.agents.capabilities.base import CapabilityProvider, CapabilityRegistry
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

# Registry of reasoning providers
_reasoning_providers: Dict[str, CapabilityProvider] = {}


def register_reasoning_provider(provider_id: str, provider: CapabilityProvider) -> None:
    """Register a reasoning provider.

    Args:
        provider_id: Unique identifier for the provider
        provider: The provider to register
    """
    if provider_id in _reasoning_providers:
        logger.warning(
            f"Reasoning provider {provider_id} already registered, overwriting"
        )

    _reasoning_providers[provider_id] = provider

    # Also register with the global registry
    CapabilityRegistry().register_provider(provider_id, provider)

    logger.debug(f"Registered reasoning provider: {provider_id}")


def get_reasoning_provider(provider_id: str) -> Optional[CapabilityProvider]:
    """Get a reasoning provider by ID.

    Args:
        provider_id: Unique identifier for the provider

    Returns:
        The provider if found, None otherwise
    """
    return _reasoning_providers.get(provider_id)
