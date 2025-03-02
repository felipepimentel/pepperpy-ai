"""Audio processing providers.

This module provides implementations for audio processing capabilities:
- Speech synthesis (text-to-speech)
- Speech recognition (speech-to-text)
- Audio analysis and processing
"""

from .synthesis import (
    AudioConfig,
    AudioData,
    BaseSynthesisProvider,
    SynthesisError,
    SynthesisProvider,
)

__all__ = [
    # Synthesis
    "AudioConfig",
    "AudioData",
    "BaseSynthesisProvider",
    "SynthesisError",
    "SynthesisProvider",
]
