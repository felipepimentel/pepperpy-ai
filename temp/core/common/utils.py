"""Common utilities for PepperPy.

This module provides utility functions used throughout the PepperPy framework,
including file operations, string manipulation, and other common tasks.
"""

import hashlib
import json
import mimetypes
import os
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Tuple, Union

# Define types locally to avoid circular imports
JSON = Dict[str, Any]
PathType = Union[str, Path]


def generate_id() -> str:
    """Generate a unique ID.

    Returns:
        A unique ID string
    """
    return str(uuid.uuid4())


def generate_timestamp() -> str:
    """Generate a timestamp in ISO format.

    Returns:
        A timestamp string in ISO format
    """
    return datetime.now().isoformat()


def hash_string(s: str, algorithm: str = "sha256") -> str:
    """Hash a string using the specified algorithm.

    Args:
        s: The string to hash
        algorithm: The hashing algorithm to use

    Returns:
        The hashed string
    """
    h = hashlib.new(algorithm)
    h.update(s.encode("utf-8"))
    return h.hexdigest()


def load_json(path: Union[str, Path]) -> JSON:
    """Load JSON data from a file.

    Args:
        path: The path to the JSON file

    Returns:
        The loaded JSON data

    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: JSON, path: Union[str, Path], indent: int = 2) -> None:
    """Save JSON data to a file.

    Args:
        data: The JSON data to save
        path: The path to save the JSON file to
        indent: The indentation level for the JSON file
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def slugify(s: str) -> str:
    """Convert a string to a slug.

    Args:
        s: The string to convert

    Returns:
        The slugified string
    """
    # Convert to lowercase
    s = s.lower()
    # Replace spaces with hyphens
    s = re.sub(r"\s+", "-", s)
    # Remove non-alphanumeric characters (except hyphens)
    s = re.sub(r"[^a-z0-9-]", "", s)
    # Remove consecutive hyphens
    s = re.sub(r"-+", "-", s)
    # Remove leading and trailing hyphens
    s = s.strip("-")
    return s


def truncate_string(s: str, max_length: int, suffix: str = "...") -> str:
    """Truncate a string to a maximum length.

    Args:
        s: The string to truncate
        max_length: The maximum length of the string
        suffix: The suffix to add to the truncated string

    Returns:
        The truncated string
    """
    if len(s) <= max_length:
        return s
    return s[: max_length - len(suffix)] + suffix


def retry(
    func: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple = (Exception,),
) -> Any:
    """Retry a function call with exponential backoff.

    Args:
        func: The function to call
        max_retries: The maximum number of retries
        delay: The initial delay between retries
        backoff: The backoff factor
        exceptions: The exceptions to catch

    Returns:
        The result of the function call

    Raises:
        The last exception raised by the function
    """
    retries = 0
    current_delay = delay

    while True:
        try:
            return func()
        except exceptions as e:
            retries += 1
            if retries > max_retries:
                raise e
            time.sleep(current_delay)
            current_delay *= backoff


def is_valid_email(email: str) -> bool:
    """Check if a string is a valid email address.

    Args:
        email: The string to check

    Returns:
        True if the string is a valid email address, False otherwise
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL.

    Args:
        url: The string to check

    Returns:
        True if the string is a valid URL, False otherwise
    """
    pattern = r"^(https?|ftp)://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, url))


def get_file_extension(path: PathType) -> str:
    """Get the extension of a file.

    Args:
        path: The path to the file

    Returns:
        The extension of the file
    """
    return os.path.splitext(str(path))[1].lower()


def get_file_mime_type(path: PathType) -> str:
    """Get the MIME type of a file.

    Args:
        path: The path to the file

    Returns:
        The MIME type of the file
    """
    mime_type, _ = mimetypes.guess_type(str(path))
    return mime_type or "application/octet-stream"


def get_file_size(path: PathType) -> int:
    """Get the size of a file in bytes.

    Args:
        path: The path to the file

    Returns:
        The size of the file in bytes
    """
    return os.path.getsize(str(path))
