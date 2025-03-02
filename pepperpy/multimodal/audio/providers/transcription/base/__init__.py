"""Base module for audio transcription providers.

This module provides the base classes and interfaces for audio transcription providers.
"""

from pepperpy.multimodal.audio.providers.transcription.base.base import (
    TranscriptionError,
    TranscriptionProvider,
    TranscriptionResult,
    TranscriptionSegment,
)
from pepperpy.multimodal.audio.providers.transcription.base.registry import (
    get_transcription_provider_class,
    get_transcription_registry,
    list_transcription_providers,
    register_transcription_provider,
)
from pepperpy.multimodal.audio.providers.transcription.base.types import (
    TranscriptionProvider as TranscriptionProviderProtocol,
)

__all__ = [
    "TranscriptionProvider",
    "TranscriptionError",
    "TranscriptionResult",
    "TranscriptionSegment",
    "TranscriptionProviderProtocol",
    "register_transcription_provider",
    "get_transcription_provider_class",
    "list_transcription_providers",
    "get_transcription_registry",
]
