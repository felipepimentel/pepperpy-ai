"""
PepperPy TTS Module.

Module for text-to-speech operations.
"""

from pepperpy.tts.base import (
    BaseTTSProvider,
    TTSConfigError,
    TTSError,
    TTSProvider,
    TTSProviderError,
    TTSVoiceError,
)

__all__ = [
    # Base classes
    "BaseTTSProvider",
    "TTSProvider",
    # Errors
    "TTSError",
    "TTSProviderError",
    "TTSConfigError",
    "TTSVoiceError",
]
