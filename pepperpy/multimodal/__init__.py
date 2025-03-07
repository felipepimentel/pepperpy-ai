"""Multimodal processing system for PepperPy.

This module provides a unified framework for processing multimodal content:
- Audio processing (speech recognition, synthesis, analysis)
- Vision processing (image analysis, object detection)
- Content synthesis (text-to-speech, image generation)
- Multimodal fusion (combining information from multiple modalities)
- Multimodal conversion (converting between different modalities)

The module is organized into submodules for each modality:
- audio: Audio processing capabilities
- vision: Vision processing capabilities
- synthesis: Content synthesis capabilities
- fusion: Multimodal fusion capabilities
- converters: Multimodal conversion capabilities
"""

# Import submodules
from . import audio, converters, synthesis, vision

# Import converters
from .converters import (
    ImageToTextConverter,
    TextToImageConverter,
    convert_between_modalities,
    get_converter,
    register_converter,
)

# Import base types
from .types import (
    BaseModalityConverter,
    Modality,
    ModalityConverter,
    ModalityData,
)

__all__ = [
    # Base types
    "Modality",
    "ModalityData",
    "ModalityConverter",
    "BaseModalityConverter",
    # Converter functions
    "convert_between_modalities",
    "get_converter",
    "register_converter",
    # Converters
    "TextToImageConverter",
    "ImageToTextConverter",
    # Submodules
    "audio",
    "synthesis",
    "vision",
    "converters",
]
