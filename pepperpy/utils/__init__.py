"""Utility functions for PepperPy.

This module provides utility functions used across the PepperPy framework,
including type validation, text manipulation, retry logic, and more.

Example:
    >>> from pepperpy.utils import validate_type, truncate_text
    >>> value = validate_type("test", str)  # No error
    >>> text = truncate_text("Long text...", max_length=10)  # "Long tex..."
"""

from pepperpy.utils.base import (
    convert_to_dict,
    flatten_dict,
    get_class_attributes,
    get_metadata_value,
    import_string,
    merge_configs,
    retry,
    safe_import,
    truncate_text,
    unflatten_dict,
    validate_type,
)

__all__ = [
    "convert_to_dict",
    "flatten_dict",
    "get_class_attributes",
    "get_metadata_value",
    "import_string",
    "merge_configs",
    "retry",
    "safe_import",
    "truncate_text",
    "unflatten_dict",
    "validate_type",
]
