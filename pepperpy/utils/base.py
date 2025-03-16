"""Base utility functions for PepperPy.

This module provides basic utility functions used throughout the PepperPy framework.
These are core utilities that are not specific to any particular domain or module.
"""

# Re-export all components from pepperpy.infra.utils
from pepperpy.infra.utils import (
    JSON,
    PathType,
    dict_to_object,
    generate_id,
    generate_timestamp,
    get_file_extension,
    get_file_mime_type,
    get_file_size,
    hash_string,
    is_valid_email,
    is_valid_url,
    load_json,
    object_to_dict,
    retry,
    save_json,
    slugify,
    truncate_string,
)

# Export all public functions and types
__all__ = [
    # Type definitions
    "PathType",
    "JSON",
    # ID and hash functions
    "generate_id",
    "generate_timestamp",
    "hash_string",
    # File operations
    "load_json",
    "save_json",
    "get_file_extension",
    "get_file_mime_type",
    "get_file_size",
    # String manipulation
    "slugify",
    "truncate_string",
    # Validation
    "is_valid_email",
    "is_valid_url",
    # Retry functionality
    "retry",
    # Object conversion
    "dict_to_object",
    "object_to_dict",
]
