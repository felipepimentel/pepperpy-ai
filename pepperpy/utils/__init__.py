"""Utility functions and helpers for PepperPy.

This module provides common utility functions and helpers used across
the PepperPy framework, including type validation, data conversion,
and common operations.

Example:
    >>> from pepperpy.utils import validate_type
    >>> validate_type("test", str)
    >>> validate_type(123, (int, float))
"""

from pepperpy.utils.base import (
    convert_to_dict,
    merge_configs,
    safe_import,
    validate_type,
)

__all__ = [
    "validate_type",
    "convert_to_dict",
    "merge_configs",
    "safe_import",
]
