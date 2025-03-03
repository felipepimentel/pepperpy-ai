"""Audio transcription providers

This module implements integrations with transcription providers,
offering:

- Audio Transcription (STT)
  - Speech to text
  - Speaker identification
  - Language detection
  - Automatic punctuation

- Optical Recognition (OCR)
  - Scanned documents
  - Text images
  - Forms and tables
  - Multiple languages

- Video Analysis
  - Caption extraction
  - Scene recognition

Supported providers:
- OpenAI Whisper
- Google Speech-to-Text
- Amazon Transcribe
- Microsoft Azure Speech
- Other providers as needed
"""

from typing import Dict, List, Optional, Union

from pepperpy.multimodal.audio.providers.transcription.base import (
    TranscriptionError,
    TranscriptionProvider,
    TranscriptionProviderProtocol,
    TranscriptionResult,
    TranscriptionSegment,
    get_transcription_provider_class,
    get_transcription_registry,
    list_transcription_providers,
    register_transcription_provider,
)

__version__ = "0.1.0"
__all__ = [
    "TranscriptionError",
    "TranscriptionProvider",
    "TranscriptionProviderProtocol",
    "TranscriptionResult",
    "TranscriptionSegment",
    "get_transcription_provider_class",
    "get_transcription_registry",
    "list_transcription_providers",
    "register_transcription_provider",
]
