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
    ContentGenerator,
    SpeechGenerator,
    TextGenerator,
)
from .optimizers import (
    ContentOptimizer,
    QualityOptimizer,
    SizeOptimizer,
)

__all__ = [
    # Base classes
    "AudioConfig",
    "AudioData",
    "SynthesisError",
    "SynthesisProcessor",
    "SynthesisProvider",
    # Generator classes
    "ContentGenerator",
    "SpeechGenerator",
    "TextGenerator",
    # Optimizer classes
    "ContentOptimizer",
    "QualityOptimizer",
    "SizeOptimizer",
    # Submodules
    "processors",
]
