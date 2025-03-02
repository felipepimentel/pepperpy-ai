"""JSON utilities.

This module provides utilities for working with JSON data.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

from .formatters import JsonFormatter


class JsonUtils:
    """Utility functions for JSON manipulation.

    Note: This class is maintained for backward compatibility.
    New code should use JsonFormatter directly.
    """

    @staticmethod
    def load(path: Union[str, Path]) -> Dict[str, Any]:
        """Load JSON from file.

        Args:
            path: File path

        Returns:
            JSON data as dictionary
        """
        return JsonFormatter.load(path)

    @staticmethod
    def save(data: Dict[str, Any], path: Union[str, Path], indent: int = 2) -> None:
        """Save dictionary to JSON file.

        Args:
            data: Dictionary to save
            path: File path
            indent: JSON indentation
        """
        formatter = JsonFormatter(indent=indent)
        formatter.format_to_file(data, str(path))

    @staticmethod
    def parse(text: str) -> Dict[str, Any]:
        """Parse JSON string.

        Args:
            text: JSON string

        Returns:
            JSON data as dictionary
        """
        return JsonFormatter.parse(text)

    @staticmethod
    def stringify(data: Dict[str, Any], indent: Optional[int] = None) -> str:
        """Convert dictionary to JSON string.

        Args:
            data: Dictionary to convert
            indent: JSON indentation

        Returns:
            JSON string
        """
        formatter = JsonFormatter(indent=indent)
        return formatter.format(data)

    @staticmethod
    def merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two JSON dictionaries.

        Args:
            base: Base dictionary
            override: Dictionary to merge on top

        Returns:
            Merged dictionary
        """
        return JsonFormatter.merge(base, override)

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
        return JsonFormatter.get_value(data, path, default, separator)

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
        JsonFormatter.set_value(data, path, value, separator)


# Re-export JsonFormatter for direct use
__all__ = ["JsonUtils", "JsonFormatter"]
