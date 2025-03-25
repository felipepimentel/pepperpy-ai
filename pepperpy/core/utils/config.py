"""Utility functions for configuration management."""

from typing import Any, Dict, Type, TypeVar

T = TypeVar("T")


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two configuration dictionaries.

    Args:
        base: The base configuration dictionary.
        override: The override configuration dictionary.

    Returns:
        The merged configuration dictionary.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    return result


def unflatten_dict(flat_dict: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """Convert a flattened dictionary into a nested dictionary.

    Args:
        flat_dict: The flattened dictionary.
        separator: The separator used in the keys.

    Returns:
        The nested dictionary.
    """
    result: Dict[str, Any] = {}
    for key, value in flat_dict.items():
        parts = key.split(separator)
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return result


def flatten_dict(nested_dict: Dict[str, Any], separator: str = ".", prefix: str = "") -> Dict[str, Any]:
    """Convert a nested dictionary into a flattened dictionary.

    Args:
        nested_dict: The nested dictionary.
        separator: The separator to use in the keys.
        prefix: The prefix to use for the keys.

    Returns:
        The flattened dictionary.
    """
    result: Dict[str, Any] = {}
    for key, value in nested_dict.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key
        if isinstance(value, dict):
            result.update(flatten_dict(value, separator, new_key))
        else:
            result[new_key] = value
    return result


def validate_type(value: Any, expected_type: Type[T]) -> T:
    """Validate that a value is of the expected type.

    Args:
        value: The value to validate.
        expected_type: The expected type.

    Returns:
        The validated value.

    Raises:
        TypeError: If the value is not of the expected type.
    """
    if not isinstance(value, expected_type):
        raise TypeError(f"Expected {expected_type.__name__}, got {type(value).__name__}")
    return value 