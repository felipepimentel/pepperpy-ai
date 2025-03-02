"""Registry for audio synthesis providers.

This module provides a registry for audio synthesis providers.
"""

from typing import Dict, List, Type

from pepperpy.core.logging import get_logger
from pepperpy.multimodal.audio.providers.synthesis.base.base import SynthesisProvider

logger = get_logger(__name__)

# Registry of synthesis providers
_SYNTHESIS_REGISTRY: Dict[str, Type[SynthesisProvider]] = {}


def register_synthesis_provider(
    name: str, provider_class: Type[SynthesisProvider]
) -> None:
    """Register a synthesis provider class.

    Args:
        name: Name of the synthesis provider
        provider_class: Provider class to register
    """
    _SYNTHESIS_REGISTRY[name] = provider_class
    logger.debug(f"Registered synthesis provider: {name}")


def get_synthesis_provider_class(name: str) -> Type[SynthesisProvider]:
    """Get a synthesis provider class by name.

    Args:
        name: Name of the synthesis provider

    Returns:
        The synthesis provider class

    Raises:
        ValueError: If the synthesis provider is not found
    """
    if name not in _SYNTHESIS_REGISTRY:
        raise ValueError(f"Synthesis provider '{name}' not found in registry")
    return _SYNTHESIS_REGISTRY[name]


def list_synthesis_providers() -> List[str]:
    """List all registered synthesis providers.

    Returns:
        List of synthesis provider names
    """
    return list(_SYNTHESIS_REGISTRY.keys())


def get_synthesis_registry() -> Dict[str, Type[SynthesisProvider]]:
    """Get the synthesis provider registry.

    Returns:
        Copy of the synthesis provider registry
    """
    return _SYNTHESIS_REGISTRY.copy()
