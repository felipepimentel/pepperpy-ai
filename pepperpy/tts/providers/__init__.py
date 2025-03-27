"""
TTS Provider implementations.

This package contains implementations of various TTS providers.
"""

from pepperpy.tts.base import TTSFactory

# Uncomment these imports when the required dependencies are installed
# For this example, we'll keep them commented to avoid dependency issues
# from pepperpy.tts.providers.elevenlabs import ElevenLabsProvider
# from pepperpy.tts.providers.murf import MurfProvider
# from pepperpy.tts.providers.playht import PlayHTProvider
# Register available providers
# TTSFactory.register_provider("elevenlabs", ElevenLabsProvider)
# TTSFactory.register_provider("murf", MurfProvider)
# TTSFactory.register_provider("playht", PlayHTProvider)
from pepperpy.tts.providers.azure import AzureProvider

__all__ = [
    # "ElevenLabsProvider",
    # "MurfProvider",
    # "PlayHTProvider",
    "AzureProvider",
]
