"""Audio Providers Module

This module provides integration with various audio processing services,
including speech recognition, text-to-speech, and audio analysis.

It supports multiple provider implementations for:
- Speech transcription
- Voice synthesis
- Audio analysis
- Sound processing
"""

from .synthesis import SynthesisError, SynthesisProvider
from .transcription import TranscriptionError, TranscriptionProvider

__all__ = [
    "SynthesisProvider",
    "SynthesisError",
    "TranscriptionProvider",
    "TranscriptionError",
]
