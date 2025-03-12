"""Public API for PepperPy utilities.

This module exports the public API for the PepperPy utility functions.
It includes various utility functions used throughout the framework.
"""

from pepperpy.utils.base import (
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
from pepperpy.utils.caching import (
    AsyncCacheInvalidator,
    CacheInvalidationRule,
    CacheInvalidator,
    CachePolicy,
    DefaultCachePolicy,
    DynamicTTLCachePolicy,
    InvalidationStrategy,
    SizeLimitedCachePolicy,
    async_cached,
    cached,
    get_async_cache_invalidator,
    get_cache_invalidator,
)
from pepperpy.utils.logging import configure_logging, get_logger, set_log_level

__all__ = [
    # Type definitions
    "JSON",
    "PathType",
    # General utilities
    "generate_id",
    "generate_timestamp",
    "hash_string",
    "slugify",
    "truncate_string",
    "retry",
    # Validation utilities
    "is_valid_email",
    "is_valid_url",
    # File utilities
    "load_json",
    "save_json",
    "get_file_extension",
    "get_file_mime_type",
    "get_file_size",
    # Object utilities
    "dict_to_object",
    "object_to_dict",
    # Logging utilities
    "configure_logging",
    "get_logger",
    "set_log_level",
    # Caching utilities
    "cached",
    "async_cached",
    "CacheInvalidationRule",
    "CacheInvalidator",
    "AsyncCacheInvalidator",
    "CachePolicy",
    "DefaultCachePolicy",
    "SizeLimitedCachePolicy",
    "DynamicTTLCachePolicy",
    "InvalidationStrategy",
    "get_cache_invalidator",
    "get_async_cache_invalidator",
]
