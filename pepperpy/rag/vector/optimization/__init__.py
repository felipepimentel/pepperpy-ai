"""Vector optimization module for RAG (DEPRECATED)

This module is deprecated, use pepperpy.rag.optimizations instead.
This module will be removed in version 1.0.0.
"""

import warnings
from typing import Any, Dict

# Configuration type for backward compatibility
VectorOptimizer = Dict[str, Any]

# Show deprecation warning
warnings.warn(
    "The 'pepperpy.rag.vector.optimization' module is deprecated and will be removed in version 1.0.0. "
    "Please use 'pepperpy.rag.optimizations' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["VectorOptimizer"]
