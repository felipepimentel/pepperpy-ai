"""Audio synthesis providers.

This module provides implementations of audio synthesis providers that
integrate with various text-to-speech services.
"""

from pepperpy.providers.audio.synthesis.base import (
    AudioConfig,
    AudioData,
    BaseSynthesisProvider,
    SynthesisError,
    SynthesisProvider,
    SynthesisProviderProtocol,
    get_synthesis_provider_class,
    get_synthesis_registry,
    list_synthesis_providers,
    register_synthesis_provider,
)

__all__ = [
    "AudioConfig",
    "AudioData",
    "BaseSynthesisProvider",
    "SynthesisError",
    "SynthesisProvider",
    "SynthesisProviderProtocol",
    "register_synthesis_provider",
    "get_synthesis_provider_class",
    "list_synthesis_providers",
    "get_synthesis_registry",
]
