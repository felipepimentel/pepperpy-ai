"""Base module for audio synthesis providers.

This module provides the base classes and interfaces for audio synthesis providers.
"""

from pepperpy.multimodal.audio.providers.synthesis.base.base import (
    AudioConfig,
    AudioData,
    BaseSynthesisProvider,
    SynthesisError,
    SynthesisProvider,
)
from pepperpy.multimodal.audio.providers.synthesis.base.registry import (
    get_synthesis_provider_class,
    get_synthesis_registry,
    list_synthesis_providers,
    register_synthesis_provider,
)
from pepperpy.multimodal.audio.providers.synthesis.base.types import (
    SynthesisProvider as SynthesisProviderProtocol,
)

__all__ = [
    "AudioConfig",
    "AudioData",
    "BaseSynthesisProvider",
    "SynthesisError",
    "SynthesisProvider",
    "SynthesisProviderProtocol",
    "get_synthesis_provider_class",
    "get_synthesis_registry",
    "list_synthesis_providers",
    "register_synthesis_provider",
]
