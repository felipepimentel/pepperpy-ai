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

from pepperpy.multimodal.audio.providers.synthesis.base import (
    AudioConfig,
    AudioData,
    BaseSynthesisProvider,
    SynthesisError,
    SynthesisProvider,
    SynthesisProviderProtocol,
    get_synthesis_provider_class,
    get_synthesis_registry,
    list_synthesis_providers,
    register_synthesis_provider,
)

__version__ = "0.1.0"
__all__ = [
    "AudioConfig",
    "AudioData",
    "BaseSynthesisProvider",
    "SynthesisError",
    "SynthesisProvider",
    "SynthesisProviderProtocol",
    "get_synthesis_provider_class",
    "get_synthesis_registry",
    "list_synthesis_providers",
    "register_synthesis_provider",
]
