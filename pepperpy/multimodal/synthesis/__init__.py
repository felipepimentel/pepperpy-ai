"""Multimodal content synthesis module.

This module provides functionality for generating multimodal content:
- Text-to-speech synthesis
- Content generation and optimization
- Audio processing and effects
"""

# Import submodules
from . import processors
from .base import (
    AudioConfig,
    AudioData,
    SynthesisError,
    SynthesisProcessor,
    SynthesisProvider,
)
from .generators import (
    AudioGenerator,
    ImageGenerator,
    TextGenerator,
)
from .optimizers import (
    AudioOptimizer,
    ImageOptimizer,
    TextOptimizer,
)

__all__ = [
    # Base classes
    "AudioConfig",
    "AudioData",
    "SynthesisError",
    "SynthesisProcessor",
    "SynthesisProvider",
    # Generator classes
    "AudioGenerator",
    "ImageGenerator",
    "TextGenerator",
    # Optimizer classes
    "AudioOptimizer",
    "ImageOptimizer",
    "TextOptimizer",
    # Submodules
    "processors",
]
