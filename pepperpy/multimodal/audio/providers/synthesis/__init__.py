"""Audio and content synthesis providers

This module implements integrations with content synthesis providers,
including:

- Voice Synthesis (TTS)
  - Natural voices
  - Voice cloning
  - Emotions and intonation
  - Multiple languages

- Image Generation
  - Realistic images
  - Digital art
  - Editing and manipulation
  - Styles and filters

- Video Synthesis
  - Animations
  - Digital avatars

Supported providers:
- Stability AI
- Midjourney
- ElevenLabs
- Other providers as needed
"""

from typing import Dict, List, Optional, Union

from .base import (
    AudioConfig,
    AudioData,
    BaseSynthesisProvider,
    SynthesisError,
    SynthesisProvider,
)

__version__ = "0.1.0"
__all__ = [
    "SynthesisProvider",
    "BaseSynthesisProvider",
    "SynthesisError",
    "AudioConfig",
    "AudioData",
]
