"""Shared utilities for the Pepperpy framework.

This module provides a comprehensive set of utility functions for:
- Unique identifier generation
- File and path operations
- Data validation and conversion
- String manipulation
- Time and date handling
- Environment management
- Serialization and deserialization
- Version management
- Resource management
"""

import asyncio
import contextlib
import hashlib
import json
import os
import time
import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel

T = TypeVar("T")


# Identifier utilities
def generate_id(prefix: str = "") -> str:
    """Generate a unique identifier.

    Args:
        prefix: Optional prefix for the ID

    Returns:
        Unique identifier string
    """
    id_str = str(uuid.uuid4())
    return f"{prefix}{id_str}" if prefix else id_str


def hash_content(content: str | bytes) -> str:
    """Generate a hash of content.

    Args:
        content: Content to hash (string or bytes)

    Returns:
        SHA-256 hash of content
    """
    if isinstance(content, str):
        content = content.encode()
    return hashlib.sha256(content).hexdigest()


# File utilities
def load_json_file(path: Path) -> dict[str, Any]:
    """Load and parse a JSON file.

    Args:
        path: Path to JSON file

    Returns:
        Parsed JSON content

    Raises:
        FileNotFoundError: If file does not exist
        json.JSONDecodeError: If file is not valid JSON
        ValueError: If file does not contain a dictionary
    """
    with open(path) as f:
        data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("JSON file must contain a dictionary")
        return dict(data)


def save_json_file(data: dict[str, Any], path: Path) -> None:
    """Save data to a JSON file.

    Args:
        data: Data to save
        path: Path to save to

    Raises:
        OSError: If file cannot be written
    """
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_yaml_file(path: Path) -> dict[str, Any]:
    """Load and parse a YAML file.

    Args:
        path: Path to YAML file

    Returns:
        Parsed YAML content

    Raises:
        FileNotFoundError: If file does not exist
        yaml.YAMLError: If file is not valid YAML
        ValueError: If file does not contain a dictionary
    """
    with open(path) as f:
        data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError("YAML file must contain a dictionary")
        return dict(data)


def save_yaml_file(data: dict[str, Any], path: Path) -> None:
    """Save data to a YAML file.

    Args:
        data: Data to save
        path: Path to save to

    Raises:
        OSError: If file cannot be written
    """
    with open(path, "w") as f:
        yaml.safe_dump(data, f, indent=2)


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists.

    Args:
        path: Directory path to ensure

    Raises:
        OSError: If directory cannot be created
    """
    path.mkdir(parents=True, exist_ok=True)


async def ensure_directory_async(path: Path) -> None:
    """Ensure a directory exists asynchronously.

    Args:
        path: Directory path to ensure

    Raises:
        OSError: If directory cannot be created
    """
    await asyncio.to_thread(path.mkdir, parents=True, exist_ok=True)


# Time utilities
def get_timestamp() -> str:
    """Get current timestamp in ISO format with timezone.

    Returns:
        ISO formatted timestamp string with timezone
    """
    return datetime.now(UTC).isoformat()


def parse_timestamp(timestamp: str) -> datetime:
    """Parse an ISO format timestamp.

    Args:
        timestamp: ISO formatted timestamp string

    Returns:
        Parsed datetime object

    Raises:
        ValueError: If timestamp is invalid
    """
    return datetime.fromisoformat(timestamp)


def get_elapsed_time(start_time: float) -> float:
    """Get elapsed time in seconds.

    Args:
        start_time: Start time in seconds

    Returns:
        Elapsed time in seconds
    """
    return time.time() - start_time


# Environment utilities
def get_env_var(name: str, default: str | None = None) -> str | None:
    """Get environment variable value.

    Args:
        name: Environment variable name
        default: Optional default value

    Returns:
        Environment variable value or default
    """
    return os.environ.get(name, default)


def get_env_bool(name: str, default: bool = False) -> bool:
    """Get boolean environment variable value.

    Args:
        name: Environment variable name
        default: Default value if not set

    Returns:
        Boolean value of environment variable
    """
    value = os.environ.get(name)
    if value is None:
        return default
    return parse_bool(value)


def get_env_int(name: str, default: int = 0) -> int:
    """Get integer environment variable value.

    Args:
        name: Environment variable name
        default: Default value if not set

    Returns:
        Integer value of environment variable
    """
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


# Type conversion utilities
def parse_bool(value: Any) -> bool:
    """Parse a boolean value from various types.

    Args:
        value: Value to parse

    Returns:
        Parsed boolean value
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    if isinstance(value, int | float):
        return bool(value)
    return False


def parse_int(value: Any, default: int = 0) -> int:
    """Parse an integer value from various types.

    Args:
        value: Value to parse
        default: Default value if parsing fails

    Returns:
        Parsed integer value
    """
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    if isinstance(value, float):
        return int(value)
    return default


# String utilities
def truncate_string(text: str, max_length: int = 100) -> str:
    """Truncate a string to maximum length.

    Args:
        text: String to truncate
        max_length: Maximum length

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def format_error(error: Exception) -> str:
    """Format an exception for display.

    Args:
        error: Exception to format

    Returns:
        Formatted error string
    """
    return f"{error.__class__.__name__}: {error!s}"


def format_size(size: int) -> str:
    """Format size in bytes to human readable string.

    Args:
        size: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0
    size_float = float(size)

    while size_float >= 1024 and unit_index < len(units) - 1:
        size_float /= 1024
        unit_index += 1

    return f"{size_float:.1f} {units[unit_index]}"


# Resource management utilities
@contextlib.contextmanager
def resource_timer() -> Iterator[float]:
    """Context manager for timing operations.

    Yields:
        Start time in seconds
    """
    start_time = time.time()
    try:
        yield start_time
    finally:
        _ = time.time() - start_time  # Calculate elapsed time but don't store it


@contextlib.asynccontextmanager
async def async_resource_timer() -> AsyncIterator[float]:
    """Async context manager for timing operations.

    Yields:
        Start time in seconds
    """
    start_time = time.time()
    try:
        yield start_time
    finally:
        _ = time.time() - start_time  # Calculate elapsed time but don't store it


def to_dict(obj: Any) -> dict[str, Any]:
    """Convert an object to a dictionary.

    Args:
        obj: Object to convert

    Returns:
        Dictionary representation of object
    """
    if isinstance(obj, dict):
        return dict(obj)
    if isinstance(obj, BaseModel):
        return dict(obj.model_dump())
    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)
    return {"value": str(obj)}


def merge_dicts(dict1: dict[str, Any], dict2: dict[str, Any]) -> dict[str, Any]:
    """Merge two dictionaries recursively.

    Args:
        dict1: First dictionary
        dict2: Second dictionary

    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def normalize_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize dictionary keys and values.

    Args:
        data: Dictionary to normalize

    Returns:
        Normalized dictionary
    """
    result: dict[str, Any] = {}
    for key, value in data.items():
        normalized_key = str(key).lower().strip()
        if isinstance(value, dict):
            result[normalized_key] = normalize_dict(value)
        else:
            result[normalized_key] = value
    return result


def extract_metadata(data: dict[str, Any]) -> dict[str, Any]:
    """Extract metadata from dictionary.

    Args:
        data: Dictionary containing metadata

    Returns:
        Extracted metadata dictionary
    """
    metadata: dict[str, Any] = {}
    for key, value in data.items():
        if key.startswith("_"):
            metadata[key[1:]] = value
    return metadata
