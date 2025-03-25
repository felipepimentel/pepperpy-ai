"""Utility functions for handling metadata."""

from typing import Any, Dict, Optional, Type, TypeVar

T = TypeVar("T")


def get_metadata_value(
    obj: Any,
    key: str,
    default: Optional[T] = None,
    expected_type: Optional[Type[T]] = None,
) -> Optional[T]:
    """Get a metadata value from an object.

    Args:
        obj: The object to get metadata from.
        key: The metadata key.
        default: The default value to return if the key is not found.
        expected_type: The expected type of the value.

    Returns:
        The metadata value, or the default value if not found.

    Raises:
        TypeError: If the value is not of the expected type.
    """
    if hasattr(obj, "__metadata__"):
        metadata = getattr(obj, "__metadata__")
        if isinstance(metadata, dict) and key in metadata:
            value = metadata[key]
            if expected_type and not isinstance(value, expected_type):
                raise TypeError(f"Expected {expected_type.__name__}, got {type(value).__name__}")
            return value
    return default 