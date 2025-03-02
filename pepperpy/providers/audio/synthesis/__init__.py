"""Audio synthesis providers.

This module provides implementations of audio synthesis providers that
integrate with various text-to-speech services.
"""

from .base import (
    AudioConfig,
    AudioData,
    BaseSynthesisProvider,
    SynthesisError,
    SynthesisProvider,
)

__all__ = [
    "AudioConfig",
    "AudioData",
    "BaseSynthesisProvider",
    "SynthesisError",
    "SynthesisProvider",
]
