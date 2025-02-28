"""Monitoring module for PepperPy (DEPRECATED).

This module is deprecated and will be removed in a future version.
Please use the 'pepperpy.observability' module instead.

The functionality previously provided by this module has been moved:
- monitoring/metrics.py → observability/metrics/
"""

import warnings
from typing import Any, Dict, List, Optional, Union

# Import from the new observability module
from ..observability import metrics
from ..observability.monitoring import runtime, system

# Show deprecation warning
warnings.warn(
    "The 'pepperpy.monitoring' module is deprecated and will be removed in a future version. "
    "Please use 'pepperpy.observability' module instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export for backward compatibility
from .metrics import MetricsManager

__all__ = [
    "MetricsManager",
    "metrics",
    "runtime",
    "system",
]
