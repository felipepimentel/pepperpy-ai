"""
TTS Provider implementations.

This package contains implementations of various TTS providers.
"""

from pepperpy.tts.base import TTSFactory
from pepperpy.tts.providers.elevenlabs import ElevenLabsProvider
from pepperpy.tts.providers.murf import MurfProvider
from pepperpy.tts.providers.playht import PlayHTProvider

# Register available providers
TTSFactory.register_provider("elevenlabs", ElevenLabsProvider)
TTSFactory.register_provider("murf", MurfProvider)
TTSFactory.register_provider("playht", PlayHTProvider)

__all__ = [
    "ElevenLabsProvider",
    "MurfProvider",
    "PlayHTProvider",
]
