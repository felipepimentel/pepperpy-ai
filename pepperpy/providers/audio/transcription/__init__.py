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

from .base import (
    TranscriptionError,
    TranscriptionProvider,
    TranscriptionResult,
    TranscriptionSegment,
)

__version__ = "0.1.0"
__all__ = [
    "TranscriptionProvider",
    "TranscriptionError",
    "TranscriptionResult",
    "TranscriptionSegment",
]
