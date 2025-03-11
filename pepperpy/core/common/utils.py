"""Utility functions for the core module.

This module provides utility functions for the core module.
These functions are deprecated and will be removed in a future version.
Use pepperpy.utils instead.
"""

import warnings
from typing import Any, Dict, List, Union

# Type definitions
JSON = Union[Dict[str, Any], List[Any], str, int, float, bool, None]

# Show deprecation warning on import
warnings.warn(
    "The pepperpy.core.common.utils module is deprecated. Use pepperpy.utils instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export all the functions from utils.base
# These will be removed in a future version
