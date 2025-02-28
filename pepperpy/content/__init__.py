"""Content module for PepperPy (DEPRECATED).

This module is deprecated and will be removed in a future version.
Please use the 'pepperpy.synthesis' module instead.

The functionality previously provided by this module has been moved:
- content/synthesis/processors → synthesis/processors
"""

import warnings
from typing import Any, Dict, List, Optional, Union

# Import from the new synthesis module
from ..synthesis import processors

# Show deprecation warning
warnings.warn(
    "The 'pepperpy.content' module is deprecated and will be removed in a future version. "
    "Please use 'pepperpy.synthesis' module instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["processors"] 