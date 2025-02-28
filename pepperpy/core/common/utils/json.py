"""JSON utilities.

This module provides utilities for working with JSON data.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union


class JsonUtils:
    """Utility functions for JSON manipulation."""

    @staticmethod
    def load(path: Union[str, Path]) -> Dict[str, Any]:
        """Load JSON from file.

        Args:
            path: File path

        Returns:
            JSON data as dictionary
        """
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save(data: Dict[str, Any], path: Union[str, Path], indent: int = 2) -> None:
        """Save dictionary to JSON file.

        Args:
            data: Dictionary to save
            path: File path
            indent: JSON indentation
        """
        path = Path(path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

    @staticmethod
    def parse(text: str) -> Dict[str, Any]:
        """Parse JSON string.

        Args:
            text: JSON string

        Returns:
            JSON data as dictionary
        """
        return json.loads(text)

    @staticmethod
    def stringify(data: Dict[str, Any], indent: Optional[int] = None) -> str:
        """Convert dictionary to JSON string.

        Args:
            data: Dictionary to convert
            indent: JSON indentation

        Returns:
            JSON string
        """
        return json.dumps(data, indent=indent, ensure_ascii=False)

    @staticmethod
    def merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two JSON dictionaries.

        Args:
            base: Base dictionary
            override: Dictionary to merge on top

        Returns:
            Merged dictionary
        """
        result = base.copy()
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = JsonUtils.merge(result[key], value)
            else:
                result[key] = value
        return result

    @staticmethod
    def get_value(
        data: Dict[str, Any], path: str, default: Any = None, separator: str = "."
    ) -> Any:
        """Get value from nested JSON using path.

        Args:
            data: JSON dictionary
            path: Path to value (e.g. "user.address.city")
            default: Default value if not found
            separator: Path separator

        Returns:
            Value at path or default
        """
        current = data
        for key in path.split(separator):
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        return current

    @staticmethod
    def set_value(
        data: Dict[str, Any], path: str, value: Any, separator: str = "."
    ) -> None:
        """Set value in nested JSON using path.

        Args:
            data: JSON dictionary
            path: Path to value (e.g. "user.address.city")
            value: Value to set
            separator: Path separator
        """
        keys = path.split(separator)
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value
