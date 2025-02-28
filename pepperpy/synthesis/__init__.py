"""Multimodal content synthesis module.

This module implements functionality for synthesizing different types of content,
including:

- Text Synthesis
  - Text generation
  - Summaries
  - Paraphrases
  - Translations

- Voice Synthesis
  - Text-to-Speech
  - Voice cloning
  - Prosody and emotion
  - Multiple languages

- Image Synthesis
  - Text-to-Image
  - Editing and manipulation
  - Styles and filters
  - Composition

- Video Synthesis
  - Animations
  - Avatars
  - Effects
  - Rendering

This module is different from processing in multimodal/
as it focuses on:
- Generating new content
- Applying creative transformations
- Producing high-quality outputs
- Customizing results

The module provides:
- Unified interfaces
- Modular pipeline
- Specific optimizations
- Quality control
"""

from typing import Dict, List, Optional, Union

from .generators import AudioGenerator, ImageGenerator, TextGenerator
from .migration import MigrationHelper
from .optimizers import AudioOptimizer, ImageOptimizer, TextOptimizer
from .processors import AudioProcessor, ImageProcessor, TextProcessor

__version__ = "0.1.0"
__all__ = [
    # Processors
    "AudioProcessor",
    "ImageProcessor",
    "TextProcessor",
    # Generators
    "AudioGenerator",
    "ImageGenerator",
    "TextGenerator",
    # Optimizers
    "AudioOptimizer",
    "ImageOptimizer",
    "TextOptimizer",
    # Migration
    "MigrationHelper",
]
