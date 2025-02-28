"""Multimodal processing system for PepperPy.

This module provides a unified framework for processing multimodal content:
- Audio processing (speech recognition, synthesis, analysis)
- Vision processing (image analysis, object detection)
- Content synthesis (text-to-speech, image generation)
- Multimodal fusion (combining information from multiple modalities)

The module is organized into submodules for each modality:
- audio: Audio processing capabilities
- vision: Vision processing capabilities
- synthesis: Content synthesis capabilities
- fusion: Multimodal fusion capabilities
"""

# Import submodules
from . import audio, synthesis, vision
from .base import (
    ContentType,
    DataFormat,
    FileHandler,
    MultimodalComponent,
    MultimodalError,
    MultimodalMetadata,
    MultimodalProcessor,
    MultimodalProvider,
)
from .fusion import (
    ContextFuser,
    FeatureFuser,
    FusedFeatures,
    MultimodalContext,
    MultimodalFusion,
)

__all__ = [
    # Base classes
    "ContentType",
    "DataFormat",
    "FileHandler",
    "MultimodalComponent",
    "MultimodalError",
    "MultimodalMetadata",
    "MultimodalProcessor",
    "MultimodalProvider",
    # Fusion classes
    "ContextFuser",
    "FeatureFuser",
    "FusedFeatures",
    "MultimodalContext",
    "MultimodalFusion",
    # Submodules
    "audio",
    "synthesis",
    "vision",
]
