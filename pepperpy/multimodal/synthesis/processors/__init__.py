"""Content synthesis processors.

This module implements specialized processors for content synthesis,
including:

- Text Processing
  - Tokenization
  - Normalization
  - Formatting
  - Styling

- Image Processing
  - Resizing
  - Filters
  - Composition
  - Optimization

- Effects Processing
  - Filters
  - Transformations
  - Enhancements

The module provides:
- Standardized interfaces
- Flexible configuration
- Modular pipeline
- Extensibility
"""

from typing import Dict, List, Optional, Union

from .effects import AudioEffectsProcessor
from .image import ImageProcessor
from .text import TextProcessor

__version__ = "0.1.0"
__all__ = [
    "AudioEffectsProcessor",
    "ImageProcessor",
    "TextProcessor",
]
