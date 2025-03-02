"""Google Cloud Speech-to-Text provider for audio transcription.

This module provides integration with Google Cloud Speech-to-Text for audio transcription.
"""

from pepperpy.multimodal.audio.providers.transcription.base import (
    register_transcription_provider,
)
from pepperpy.multimodal.audio.providers.transcription.google.google_provider import (
    GoogleTranscriptionProvider,
)

# Register the provider
register_transcription_provider("google", GoogleTranscriptionProvider)

__all__ = ["GoogleTranscriptionProvider"]
