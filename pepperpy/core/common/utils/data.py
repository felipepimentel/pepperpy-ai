"""Data manipulation utilities.

Implements helper functions for data manipulation and conversion.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, TypeVar

T = TypeVar("T")


class DataUtils:
    """Utility functions for data manipulation."""

    @staticmethod
    def to_dict(obj: Any) -> Dict[str, Any]:
        """Convert object to dictionary.

        Args:
            obj: Object to convert

        Returns:
            Dictionary representation

        """
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        if hasattr(obj, "dict"):
            return obj.dict()
        if isinstance(obj, dict):
            return obj
        raise ValueError(f"Cannot convert {type(obj)} to dict")

    @staticmethod
    def from_dict(data: Dict[str, Any], cls: type[T]) -> T:
        """Create object from dictionary.

        Args:
            data: Dictionary data
            cls: Target class

        Returns:
            Instance of target class

        """
        if hasattr(cls, "from_dict"):
            return cls.from_dict(data)
        if hasattr(cls, "parse_obj"):
            return cls.parse_obj(data)
        return cls(**data)

    @staticmethod
    def to_json(obj: Any) -> str:
        """Convert object to JSON string.

        Args:
            obj: Object to convert

        Returns:
            JSON string

        """

        def default(o: Any) -> Any:
            if isinstance(o, datetime):
                return o.isoformat()
            return str(o)

        return json.dumps(DataUtils.to_dict(obj), default=default)

    @staticmethod
    def from_json(data: str, cls: type[T]) -> T:
        """Create object from JSON string.

        Args:
            data: JSON string
            cls: Target class

        Returns:
            Instance of target class

        """
        return DataUtils.from_dict(json.loads(data), cls)

    @staticmethod
    def merge_dicts(*dicts: Dict[str, Any], overwrite: bool = True) -> Dict[str, Any]:
        """Merge multiple dictionaries.

        Args:
            *dicts: Dictionaries to merge
            overwrite: Whether to overwrite existing keys

        Returns:
            Merged dictionary

        """
        result = {}
        for d in dicts:
            if overwrite:
                result.update(d)
            else:
                result.update({k: v for k, v in d.items() if k not in result})
        return result

    @staticmethod
    def flatten_dict(
        d: Dict[str, Any], parent_key: str = "", sep: str = ".",
    ) -> Dict[str, Any]:
        """Flatten nested dictionary.

        Args:
            d: Dictionary to flatten
            parent_key: Parent key for nested items
            sep: Separator for nested keys

        Returns:
            Flattened dictionary

        """
        items: List[tuple[str, Any]] = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(DataUtils.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
