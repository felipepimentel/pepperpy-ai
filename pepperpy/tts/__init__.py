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
from pepperpy.tts.providers import AzureTTSProvider

__all__ = [
    # Base classes
    "BaseTTSProvider",
    "TTSProvider",
    # Errors
    "TTSError",
    "TTSProviderError",
    "TTSConfigError",
    "TTSVoiceError",
    # Providers
    "AzureTTSProvider",
]
