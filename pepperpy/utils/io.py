"""IO utilities for the PepperPy framework.

This module provides utility functions for file and IO operations.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, cast

from pepperpy.core.errors import PepperPyError
from pepperpy.core.types import JSON, PathType


def ensure_directory(path: PathType) -> Path:
    """Ensure that a directory exists, creating it if necessary.

    Args:
        path: The directory path

    Returns:
        The path as a Path object

    Raises:
        PepperPyError: If the directory cannot be created
    """
    path_obj = Path(path)

    try:
        path_obj.mkdir(parents=True, exist_ok=True)
        return path_obj
    except Exception as e:
        raise PepperPyError(f"Failed to create directory {path}: {str(e)}")


def read_text(path: PathType, encoding: str = "utf-8") -> str:
    """Read text from a file.

    Args:
        path: The file path
        encoding: The file encoding

    Returns:
        The file contents as a string

    Raises:
        PepperPyError: If the file cannot be read
    """
    path_obj = Path(path)

    try:
        return path_obj.read_text(encoding=encoding)
    except Exception as e:
        raise PepperPyError(f"Failed to read file {path}: {str(e)}")


def write_text(path: PathType, content: str, encoding: str = "utf-8") -> None:
    """Write text to a file.

    Args:
        path: The file path
        content: The content to write
        encoding: The file encoding

    Raises:
        PepperPyError: If the file cannot be written
    """
    path_obj = Path(path)

    # Ensure the parent directory exists
    ensure_directory(path_obj.parent)

    try:
        path_obj.write_text(content, encoding=encoding)
    except Exception as e:
        raise PepperPyError(f"Failed to write file {path}: {str(e)}")


def read_json(path: PathType, encoding: str = "utf-8") -> JSON:
    """Read JSON from a file.

    Args:
        path: The file path
        encoding: The file encoding

    Returns:
        The parsed JSON data

    Raises:
        PepperPyError: If the file cannot be read or parsed
    """
    try:
        content = read_text(path, encoding=encoding)
        return cast(JSON, json.loads(content))
    except json.JSONDecodeError as e:
        raise PepperPyError(f"Failed to parse JSON from {path}: {str(e)}")


def write_json(
    path: PathType, data: JSON, indent: int = 2, encoding: str = "utf-8"
) -> None:
    """Write JSON to a file.

    Args:
        path: The file path
        data: The data to write
        indent: The indentation level
        encoding: The file encoding

    Raises:
        PepperPyError: If the file cannot be written
    """
    try:
        content = json.dumps(data, indent=indent, ensure_ascii=False)
        write_text(path, content, encoding=encoding)
    except Exception as e:
        raise PepperPyError(f"Failed to write JSON to {path}: {str(e)}")


def list_files(
    directory: PathType, pattern: str = "*", recursive: bool = False
) -> List[Path]:
    """List files in a directory.

    Args:
        directory: The directory path
        pattern: The glob pattern to match
        recursive: Whether to search recursively

    Returns:
        A list of matching file paths

    Raises:
        PepperPyError: If the directory cannot be read
    """
    path_obj = Path(directory)

    try:
        if recursive:
            return list(path_obj.glob(f"**/{pattern}"))
        else:
            return list(path_obj.glob(pattern))
    except Exception as e:
        raise PepperPyError(f"Failed to list files in {directory}: {str(e)}")


def copy_file(source: PathType, destination: PathType) -> None:
    """Copy a file.

    Args:
        source: The source file path
        destination: The destination file path

    Raises:
        PepperPyError: If the file cannot be copied
    """
    source_path = Path(source)
    dest_path = Path(destination)

    # Ensure the parent directory exists
    ensure_directory(dest_path.parent)

    try:
        shutil.copy2(source_path, dest_path)
    except Exception as e:
        raise PepperPyError(f"Failed to copy {source} to {destination}: {str(e)}")


def move_file(source: PathType, destination: PathType) -> None:
    """Move a file.

    Args:
        source: The source file path
        destination: The destination file path

    Raises:
        PepperPyError: If the file cannot be moved
    """
    source_path = Path(source)
    dest_path = Path(destination)

    # Ensure the parent directory exists
    ensure_directory(dest_path.parent)

    try:
        shutil.move(source_path, dest_path)
    except Exception as e:
        raise PepperPyError(f"Failed to move {source} to {destination}: {str(e)}")


def remove_file(path: PathType) -> None:
    """Remove a file.

    Args:
        path: The file path

    Raises:
        PepperPyError: If the file cannot be removed
    """
    path_obj = Path(path)

    try:
        if path_obj.exists():
            path_obj.unlink()
    except Exception as e:
        raise PepperPyError(f"Failed to remove {path}: {str(e)}")


def create_temp_file(
    content: Optional[str] = None, suffix: Optional[str] = None
) -> Path:
    """Create a temporary file.

    Args:
        content: Optional content to write to the file
        suffix: Optional file suffix

    Returns:
        The path to the temporary file

    Raises:
        PepperPyError: If the file cannot be created
    """
    try:
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)

        if content is not None:
            write_text(path, content)

        return Path(path)
    except Exception as e:
        raise PepperPyError(f"Failed to create temporary file: {str(e)}")


def create_temp_directory() -> Path:
    """Create a temporary directory.

    Returns:
        The path to the temporary directory

    Raises:
        PepperPyError: If the directory cannot be created
    """
    try:
        return Path(tempfile.mkdtemp())
    except Exception as e:
        raise PepperPyError(f"Failed to create temporary directory: {str(e)}")


__all__ = [
    "ensure_directory",
    "read_text",
    "write_text",
    "read_json",
    "write_json",
    "list_files",
    "copy_file",
    "move_file",
    "remove_file",
    "create_temp_file",
    "create_temp_directory",
]
