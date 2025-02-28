"""Content module for PepperPy (DEPRECATED).

This module is deprecated and will be removed in version 1.0.0 (scheduled for Q3 2023).
Please use the 'pepperpy.synthesis' module instead.

The functionality previously provided by this module has been moved:
- content/synthesis/processors → synthesis/processors
- content/synthesis/generators → synthesis/generators
- content/synthesis/optimizers → synthesis/optimizers

For migration assistance, use the MigrationHelper:
    from pepperpy.synthesis import MigrationHelper
"""

import warnings
from typing import Any, Dict, List, Optional, Union

# Import from the new synthesis module
from ..synthesis import (
    AudioGenerator,
    AudioOptimizer,
    AudioProcessor,
    ImageGenerator,
    ImageOptimizer,
    ImageProcessor,
    MigrationHelper,
    TextGenerator,
    TextOptimizer,
    TextProcessor,
)

# Show deprecation warning
warnings.warn(
    "The 'pepperpy.content' module is deprecated and will be removed in version 1.0.0 (Q3 2023). "
    "Please use 'pepperpy.synthesis' module instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export for backward compatibility
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
