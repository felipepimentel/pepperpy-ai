"""PepperPy Utilities.

This module provides utility functions and classes for the PepperPy framework,
including file operations, string manipulation, validation, and logging.
"""

import os
from pathlib import Path
from typing import Union

from pepperpy.errors import PepperpyError
from pepperpy.types import PathLike
from pepperpy.utils.public import (
    # Type definitions
    JSON,
    PathType,
    # Logging utilities
    configure_logging,
    # Object utilities
    dict_to_object,
    # General utilities
    generate_id,
    generate_timestamp,
    get_file_extension,
    get_file_mime_type,
    get_file_size,
    get_logger,
    hash_string,
    # Validation utilities
    is_valid_email,
    is_valid_url,
    # File utilities
    load_json,
    object_to_dict,
    retry,
    save_json,
    set_log_level,
    slugify,
    truncate_string,
)


def normalize_path(path: PathLike) -> Path:
    """Normalize a path.

    Args:
        path: Path to normalize

    Returns:
        Normalized path

    Raises:
        PepperpyError: If path is invalid
    """
    try:
        if isinstance(path, str):
            path = Path(path)
        elif isinstance(path, os.PathLike):
            path = Path(path)
        return path.resolve()
    except Exception as e:
        raise PepperpyError(f"Invalid path: {e}")


def read_file_content(path: PathLike, encoding: str = "utf-8") -> str:
    """Read file content.

    Args:
        path: Path to file
        encoding: File encoding

    Returns:
        File content

    Raises:
        PepperpyError: If file cannot be read
    """
    try:
        path = normalize_path(path)
        with open(path, "r", encoding=encoding) as f:
            return f.read()
    except Exception as e:
        raise PepperpyError(f"Error reading file: {e}")


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
    "normalize_path",
    "read_file_content",
]
