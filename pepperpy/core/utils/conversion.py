"""Utility functions for converting between different data types."""

from typing import Any, Dict, List, Optional, Tuple, Union


def convert_to_dict(obj: Any) -> Dict[str, Any]:
    """Convert an object to a dictionary.

    Args:
        obj: The object to convert.

    Returns:
        A dictionary representation of the object.
    """
    if isinstance(obj, dict):
        return obj
    elif hasattr(obj, "__dict__"):
        return obj.__dict__
    elif hasattr(obj, "_asdict"):
        return obj._asdict()
    else:
        raise TypeError(f"Cannot convert {type(obj)} to dictionary")


def flatten_dict(
    d: Dict[str, Any],
    parent_key: str = "",
    sep: str = ".",
    ignore_keys: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Flatten a nested dictionary.

    Args:
        d: The dictionary to flatten.
        parent_key: The parent key to use for flattening.
        sep: The separator to use between keys.
        ignore_keys: A list of keys to ignore during flattening.

    Returns:
        A flattened dictionary.

    Example:
        >>> d = {"a": 1, "b": {"c": 2, "d": {"e": 3}}}
        >>> flatten_dict(d)
        {'a': 1, 'b.c': 2, 'b.d.e': 3}
    """
    items: List[Tuple[str, Any]] = []
    ignore_keys = ignore_keys or []

    for k, v in d.items():
        if k in ignore_keys:
            items.append((k, v))
            continue

        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            items.extend(
                flatten_dict(
                    v, new_key, sep=sep, ignore_keys=ignore_keys
                ).items()
            )
        else:
            items.append((new_key, v))

    return dict(items)


def unflatten_dict(
    d: Dict[str, Any], sep: str = ".", ignore_keys: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Unflatten a flattened dictionary.

    Args:
        d: The dictionary to unflatten.
        sep: The separator used between keys.
        ignore_keys: A list of keys to ignore during unflattening.

    Returns:
        An unflattened dictionary.

    Example:
        >>> d = {'a': 1, 'b.c': 2, 'b.d.e': 3}
        >>> unflatten_dict(d)
        {'a': 1, 'b': {'c': 2, 'd': {'e': 3}}}
    """
    result: Dict[str, Any] = {}
    ignore_keys = ignore_keys or []

    for key, value in d.items():
        if key in ignore_keys:
            result[key] = value
            continue

        parts = key.split(sep)
        target = result

        for part in parts[:-1]:
            target = target.setdefault(part, {})

        target[parts[-1]] = value

    return result 