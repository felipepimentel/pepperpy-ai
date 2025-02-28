"""Content synthesis processors.

This module implements specialized processors for content synthesis,
including:

- Text Processing
  - Tokenization
  - Normalization
  - Formatting
  - Styling

- Audio Processing
  - Normalization
  - Filtering
  - Effects
  - Mixing

- Image Processing
  - Resizing
  - Filters
  - Composition
  - Optimization

The module provides:
- Standardized interfaces
- Flexible configuration
- Modular pipeline
- Extensibility
"""

from typing import Dict, List, Optional, Union

from .audio import AudioProcessor
from .image import ImageProcessor
from .text import TextProcessor

__version__ = "0.1.0"
__all__ = [
    "AudioProcessor",
    "ImageProcessor",
    "TextProcessor",
]
