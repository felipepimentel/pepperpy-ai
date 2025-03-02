"""Registry for audio transcription providers.

This module provides a registry for audio transcription providers.
"""

from typing import Dict, List, Type

from pepperpy.core.logging import get_logger
from pepperpy.multimodal.audio.providers.transcription.base.base import (
    TranscriptionProvider,
)

logger = get_logger(__name__)

# Registry of transcription providers
_TRANSCRIPTION_REGISTRY: Dict[str, Type[TranscriptionProvider]] = {}


def register_transcription_provider(
    name: str, provider_class: Type[TranscriptionProvider]
) -> None:
    """Register a transcription provider class.

    Args:
        name: Name of the transcription provider
        provider_class: Provider class to register
    """
    _TRANSCRIPTION_REGISTRY[name] = provider_class
    logger.debug(f"Registered transcription provider: {name}")


def get_transcription_provider_class(name: str) -> Type[TranscriptionProvider]:
    """Get a transcription provider class by name.

    Args:
        name: Name of the transcription provider

    Returns:
        The transcription provider class

    Raises:
        ValueError: If the transcription provider is not found
    """
    if name not in _TRANSCRIPTION_REGISTRY:
        raise ValueError(f"Transcription provider '{name}' not found in registry")
    return _TRANSCRIPTION_REGISTRY[name]


def list_transcription_providers() -> List[str]:
    """List all registered transcription providers.

    Returns:
        List of transcription provider names
    """
    return list(_TRANSCRIPTION_REGISTRY.keys())


def get_transcription_registry() -> Dict[str, Type[TranscriptionProvider]]:
    """Get the transcription provider registry.

    Returns:
        Copy of the transcription provider registry
    """
    return _TRANSCRIPTION_REGISTRY.copy()
