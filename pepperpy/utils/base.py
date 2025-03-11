"""Base utility functions for PepperPy.

This module provides basic utility functions used throughout the PepperPy framework.
These are core utilities that are not specific to any particular domain or module.
"""

import functools
import hashlib
import json
import mimetypes
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, cast

# Type definitions
T = TypeVar("T")
PathType = Union[str, Path]
JSON = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


def generate_id(prefix: str = "", length: int = 16) -> str:
    """Generate a random ID.

    Args:
        prefix: Optional prefix for the ID
        length: Length of the random part of the ID

    Returns:
        A random ID
    """
    import uuid

    random_part = uuid.uuid4().hex[:length]
    return f"{prefix}{random_part}"


def generate_timestamp() -> str:
    """Generate a timestamp string in ISO 8601 format.

    Returns:
        A timestamp string
    """
    return datetime.utcnow().isoformat()


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


def load_json(path: PathType) -> JSON:
    """Load JSON data from a file.

    Args:
        path: The path to the JSON file

    Returns:
        The loaded JSON data

    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    path_obj = Path(path)
    with path_obj.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: JSON, path: PathType, indent: int = 2) -> None:
    """Save JSON data to a file.

    Args:
        data: The JSON data to save
        path: The path to the JSON file
        indent: The indentation level for the JSON file

    Raises:
        TypeError: If the data is not JSON serializable
    """
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with path_obj.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def slugify(s: str, separator: str = "-") -> str:
    """Convert a string to a slug.

    Args:
        s: The string to convert
        separator: The separator to use between words

    Returns:
        The slugified string
    """
    # Remove special characters and replace spaces with separator
    slug = re.sub(r"[^\w\s]", "", s.lower())
    slug = re.sub(r"\s+", separator, slug)
    return slug


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
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
    func: Optional[Callable] = None,
    *,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[type, ...] = (Exception,),
) -> Any:
    """Retry a function multiple times.

    Can be used as a decorator with default arguments:
        @retry
        def my_function():
            ...

    Or with custom arguments:
        @retry(max_attempts=5, delay=0.5)
        def my_function():
            ...

    Or as a function:
        result = retry(my_function, max_attempts=5, delay=0.5)

    Args:
        func: The function to retry
        max_attempts: The maximum number of attempts
        delay: The initial delay between attempts in seconds
        backoff: The backoff factor for subsequent attempts
        exceptions: The exceptions to catch and retry on

    Returns:
        The result of the function

    Raises:
        The last exception raised by the function if all attempts fail
    """

    def decorator(func_to_decorate: Callable) -> Callable:
        @functools.wraps(func_to_decorate)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempts = 0
            current_delay = delay
            while True:
                try:
                    return func_to_decorate(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        raise e
                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper

    if func is None:
        return decorator
    return decorator(func)


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
    """Get the file extension from a path.

    Args:
        path: The file path

    Returns:
        The file extension (without the dot)
    """
    return os.path.splitext(str(path))[1].lstrip(".")


def get_file_mime_type(path: PathType) -> str:
    """Get the MIME type of a file.

    Args:
        path: The file path

    Returns:
        The MIME type of the file
    """
    mime_type, _ = mimetypes.guess_type(str(path))
    return mime_type or "application/octet-stream"


def get_file_size(path: PathType) -> int:
    """Get the size of a file in bytes.

    Args:
        path: The file path

    Returns:
        The size of the file in bytes
    """
    return os.path.getsize(str(path))


def dict_to_object(data: Dict[str, Any], cls: type) -> T:
    """Convert a dictionary to an object of the specified class.

    Args:
        data: The dictionary to convert
        cls: The class to convert to

    Returns:
        An instance of the specified class
    """
    return cast(T, cls(**data))


def object_to_dict(obj: Any) -> Dict[str, Any]:
    """Convert an object to a dictionary.

    Args:
        obj: The object to convert

    Returns:
        A dictionary representation of the object
    """
    if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
        return obj.to_dict()
    return {
        key: value for key, value in obj.__dict__.items() if not key.startswith("_")
    }
