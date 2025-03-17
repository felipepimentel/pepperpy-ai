"""Base utilities for PepperPy.

This module provides basic utility functions and classes used throughout the PepperPy framework.
"""

import hashlib
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, Union, cast

from pepperpy.types import JSONDict, PathLike

# Type definitions
PathType = Union[str, os.PathLike, Path]
JSON = Union[Dict[str, Any], List[Any], str, int, float, bool, None]
T = TypeVar("T")


def generate_id() -> str:
    """Generate a unique identifier.

    Returns:
        A unique identifier
    """
    return str(uuid.uuid4())


def generate_timestamp() -> int:
    """Generate a timestamp.

    Returns:
        Current timestamp in milliseconds
    """
    return int(time.time() * 1000)


def hash_string(s: str, algorithm: str = "sha256") -> str:
    """Hash a string using the specified algorithm.

    Args:
        s: String to hash
        algorithm: Hashing algorithm to use

    Returns:
        Hashed string
    """
    h = hashlib.new(algorithm)
    h.update(s.encode("utf-8"))
    return h.hexdigest()


def slugify(text: str) -> str:
    """Convert text to a slug.

    Args:
        text: Text to convert

    Returns:
        Slugified text
    """
    # Convert to lowercase
    text = text.lower()
    # Replace spaces with hyphens
    text = re.sub(r"\s+", "-", text)
    # Remove non-alphanumeric characters (except hyphens)
    text = re.sub(r"[^a-z0-9\-]", "", text)
    # Remove multiple hyphens
    text = re.sub(r"\-+", "-", text)
    # Remove leading and trailing hyphens
    text = text.strip("-")
    return text


def truncate_string(s: str, max_length: int, suffix: str = "...") -> str:
    """Truncate a string to the specified length.

    Args:
        s: String to truncate
        max_length: Maximum length of the string
        suffix: Suffix to add to truncated string

    Returns:
        Truncated string
    """
    if len(s) <= max_length:
        return s
    return s[: max_length - len(suffix)] + suffix


def is_valid_email(email: str) -> bool:
    """Check if a string is a valid email address.

    Args:
        email: Email address to check

    Returns:
        True if the email is valid, False otherwise
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL.

    Args:
        url: URL to check

    Returns:
        True if the URL is valid, False otherwise
    """
    pattern = r"^(https?|ftp)://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, url))


def get_file_extension(path: PathLike) -> str:
    """Get the extension of a file.

    Args:
        path: Path to the file

    Returns:
        Extension of the file
    """
    if isinstance(path, str):
        return os.path.splitext(path)[1].lower()
    return os.path.splitext(str(path))[1].lower()


def get_file_size(path: PathLike) -> int:
    """Get the size of a file.

    Args:
        path: Path to the file

    Returns:
        Size of the file in bytes
    """
    if isinstance(path, str):
        return os.path.getsize(path)
    return os.path.getsize(str(path))


def get_file_mime_type(path: PathLike) -> str:
    """Get the MIME type of a file.

    Args:
        path: Path to the file

    Returns:
        MIME type of the file
    """
    import mimetypes

    mimetypes.init()
    if isinstance(path, str):
        return mimetypes.guess_type(path)[0] or "application/octet-stream"
    return mimetypes.guess_type(str(path))[0] or "application/octet-stream"


def load_json(path: PathLike) -> JSONDict:
    """Load JSON from a file.

    Args:
        path: Path to the JSON file

    Returns:
        Loaded JSON
    """
    import json

    if isinstance(path, str):
        with open(path, "r", encoding="utf-8") as f:
            return cast(JSONDict, json.load(f))
    with open(str(path), "r", encoding="utf-8") as f:
        return cast(JSONDict, json.load(f))


def save_json(path: PathLike, data: JSONDict, indent: int = 2) -> None:
    """Save JSON to a file.

    Args:
        path: Path to the JSON file
        data: JSON data to save
        indent: Indentation level
    """
    import json

    if isinstance(path, str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent)
    else:
        with open(str(path), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent)


def object_to_dict(obj: Any) -> Dict[str, Any]:
    """Convert an object to a dictionary.

    Args:
        obj: Object to convert

    Returns:
        Dictionary representation of the object
    """
    if isinstance(obj, dict):
        return obj
    return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}


def dict_to_object(d: Dict[str, Any], cls: type) -> Any:
    """Convert a dictionary to an object.

    Args:
        d: Dictionary to convert
        cls: Class to instantiate

    Returns:
        Object representation of the dictionary
    """
    if not isinstance(d, dict):
        return d
    obj = cls()
    for k, v in d.items():
        setattr(obj, k, v)
    return obj


def retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Optional[List[type]] = None,
) -> Any:
    """Retry a function a certain number of times.

    Args:
        max_retries: Maximum number of retries
        delay: Initial delay between retries in seconds
        backoff: Backoff factor
        exceptions: Exceptions to catch and retry

    Returns:
        Decorator function
    """
    if exceptions is None:
        exceptions = [Exception]

    def decorator(func: Any) -> Any:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            retries = 0
            current_delay = delay
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except tuple(exceptions) as e:
                    retries += 1
                    if retries > max_retries:
                        raise e
                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper

    return decorator
