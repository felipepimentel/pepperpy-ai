"""PepperPy Utilities.

This module provides utility functions and classes for the PepperPy framework,
including file operations, string manipulation, validation, and logging.
"""

import os
from pathlib import Path

from pepperpy.core.errors import PepperPyError
from pepperpy.infra.logging import configure_logging, get_logger, set_log_level
from pepperpy.types import PathLike


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
        raise PepperPyError(f"Invalid path: {e}")


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
        raise PepperPyError(f"Error reading file: {e}")


__all__ = [
    # Logging utilities
    "configure_logging",
    "get_logger",
    "set_log_level",
    # Path utilities
    "normalize_path",
    "read_file_content",
]
