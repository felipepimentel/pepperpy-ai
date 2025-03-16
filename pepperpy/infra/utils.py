"""Core utility functions for PepperPy.

This module provides foundational utility functions used throughout the PepperPy framework.
These are infrastructure-level utilities that are not specific to any particular domain.

Functions include:
- ID generation and hashing
- File operations
- String manipulation and validation
- JSON handling
- Object conversion
"""

import functools
import hashlib
import json
import mimetypes
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, cast

# Type definitions
T = TypeVar("T")
U = TypeVar("U")  # Add a new TypeVar for dict_to_object
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
    if algorithm == "sha256":
        return hashlib.sha256(s.encode()).hexdigest()
    elif algorithm == "md5":
        return hashlib.md5(s.encode()).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(s.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported hashing algorithm: {algorithm}")


def load_json(path: PathType) -> JSON:
    """Load a JSON file.

    Args:
        path: Path to the JSON file

    Returns:
        The loaded JSON data

    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    path_obj = Path(path)
    with path_obj.open("r", encoding="utf-8") as f:
        return cast(JSON, json.load(f))


def save_json(data: JSON, path: PathType, indent: int = 2) -> None:
    """Save data to a JSON file.

    Args:
        data: The data to save
        path: Path to the JSON file
        indent: Indentation level for the JSON file

    Raises:
        TypeError: If the data is not JSON serializable
        PermissionError: If the file cannot be written
    """
    path_obj = Path(path)
    # Create parent directories if they don't exist
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with path_obj.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent)


def slugify(s: str, separator: str = "-") -> str:
    """Convert a string to a slug.

    Args:
        s: The string to convert
        separator: The separator to use

    Returns:
        The slugified string
    """
    # Convert to lowercase
    s = s.lower()
    # Replace spaces with separator
    s = re.sub(r"\s+", separator, s)
    # Remove non-alphanumeric characters (except for the separator)
    s = re.sub(f"[^a-z0-9{separator}]", "", s)
    # Remove duplicate separators
    s = re.sub(f"{separator}+", separator, s)
    # Remove leading and trailing separators
    s = s.strip(separator)
    return s


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate a string to a maximum length.

    Args:
        s: The string to truncate
        max_length: The maximum length of the string
        suffix: The suffix to add if the string is truncated

    Returns:
        The truncated string
    """
    if len(s) <= max_length:
        return s
    else:
        return s[: max_length - len(suffix)] + suffix


def retry(
    func: Optional[Callable] = None,
    *,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[type[BaseException], ...] = (Exception,),
) -> Any:
    """Retry a function in case of exceptions.

    This can be used as a decorator with or without arguments.

    Examples:
        @retry
        def my_function():
            # This will be retried 3 times by default

        @retry(max_attempts=5, delay=2.0)
        def another_function():
            # This will be retried 5 times with a 2 second delay

        # Or you can use it directly:
        result = retry(my_function, max_attempts=2)

    Args:
        func: The function to retry
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts in seconds
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch

    Returns:
        The result of the function call
    """
    if func is None:
        return functools.partial(
            retry,
            max_attempts=max_attempts,
            delay=delay,
            backoff=backoff,
            exceptions=exceptions,
        )

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        attempts = 0
        while True:
            try:
                return func(*args, **kwargs)
            except exceptions:
                attempts += 1
                if attempts >= max_attempts:
                    raise
                current_delay = delay * (backoff ** (attempts - 1))
                time.sleep(current_delay)

    return wrapper


def is_valid_email(email: str) -> bool:
    """Check if a string is a valid email address.

    Args:
        email: The email address to check

    Returns:
        True if the email is valid, False otherwise
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL.

    Args:
        url: The URL to check

    Returns:
        True if the URL is valid, False otherwise
    """
    pattern = r"^(https?|ftp)://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, url))


def get_file_extension(path: PathType) -> str:
    """Get the extension of a file.

    Args:
        path: Path to the file

    Returns:
        The file extension (without the dot)
    """
    path_obj = Path(path)
    return path_obj.suffix.lstrip(".")


def get_file_mime_type(path: PathType) -> str:
    """Get the MIME type of a file.

    Args:
        path: Path to the file

    Returns:
        The MIME type of the file
    """
    path_obj = Path(path)
    mime_type, _ = mimetypes.guess_type(path_obj)
    return mime_type or "application/octet-stream"


def get_file_size(path: PathType) -> int:
    """Get the size of a file in bytes.

    Args:
        path: Path to the file

    Returns:
        The size of the file in bytes

    Raises:
        FileNotFoundError: If the file does not exist
    """
    path_obj = Path(path)
    return path_obj.stat().st_size


def dict_to_object(data: Dict[str, Any], cls: type) -> Any:
    """Convert a dictionary to an object of the specified class.

    Args:
        data: The dictionary to convert
        cls: The class to convert to

    Returns:
        An instance of the specified class
    """
    if hasattr(cls, "from_dict"):
        return cls.from_dict(data)
    else:
        obj = cls()
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        return obj


def object_to_dict(obj: Any) -> Dict[str, Any]:
    """Convert an object to a dictionary.

    Args:
        obj: The object to convert

    Returns:
        A dictionary representation of the object
    """
    if hasattr(obj, "to_dict"):
        return cast(Dict[str, Any], obj.to_dict())
    elif hasattr(obj, "__dict__"):
        return cast(Dict[str, Any], obj.__dict__)
    else:
        return {key: getattr(obj, key) for key in dir(obj) if not key.startswith("_")}


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
