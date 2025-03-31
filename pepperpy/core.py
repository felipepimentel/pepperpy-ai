"""Core interfaces and base classes for PepperPy.

DEPRECATED: This module is deprecated and will be removed in a future version.
Please use the pepperpy.core package instead.

Example:
    Instead of:
    >>> from pepperpy.core import BaseProvider, ConfigError
    
    Use:
    >>> from pepperpy.core import BaseProvider, ConfigError
    # Or import from the specific module:
    >>> from pepperpy.core.utils import BaseProvider, ConfigError
"""

import warnings

warnings.warn(
    "The pepperpy.core module is deprecated and will be removed in a future version. "
    "Please use the pepperpy.core package instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Redirect imports to new structure
from pepperpy.core.utils import (
    BaseProvider,
    ConfigError,
    PepperpyError,
    ProviderError,
    ValidationError,
)

# Re-export everything to maintain backwards compatibility
__all__ = [
    "BaseProvider",
    "ConfigError",
    "PepperpyError",
    "ProviderError",
    "ValidationError",
]
