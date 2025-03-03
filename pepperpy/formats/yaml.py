"""YAML utilities.

This module provides utilities for working with YAML data.
"""

from pathlib import Path
from typing import Any, Dict, Union

from .formatters import YamlFormatter


class YamlUtils:
    """Utility functions for YAML manipulation.

    Note: This class is maintained for backward compatibility.
    New code should use YamlFormatter directly.
    """

    @staticmethod
    def _ensure_yaml_available():
        """Ensure PyYAML is available.

        Raises:
            ImportError: If PyYAML is not installed

        """
        YamlFormatter._ensure_yaml_available()

    @staticmethod
    def load(path: Union[str, Path]) -> Dict[str, Any]:
        """Load YAML from file.

        Args:
            path: File path

        Returns:
            YAML data as dictionary

        Raises:
            ImportError: If PyYAML is not installed

        """
        return YamlFormatter.load(path)

    @staticmethod
    def save(
        data: Dict[str, Any], path: Union[str, Path], default_flow_style: bool = False,
    ) -> None:
        """Save dictionary to YAML file.

        Args:
            data: Dictionary to save
            path: File path
            default_flow_style: YAML flow style

        Raises:
            ImportError: If PyYAML is not installed

        """
        formatter = YamlFormatter(default_flow_style=default_flow_style)
        formatter.format_to_file(data, str(path))

    @staticmethod
    def parse(text: str) -> Dict[str, Any]:
        """Parse YAML string.

        Args:
            text: YAML string

        Returns:
            YAML data as dictionary

        Raises:
            ImportError: If PyYAML is not installed

        """
        return YamlFormatter.parse(text)

    @staticmethod
    def stringify(data: Dict[str, Any], default_flow_style: bool = False) -> str:
        """Convert dictionary to YAML string.

        Args:
            data: Dictionary to convert
            default_flow_style: YAML flow style

        Returns:
            YAML string

        Raises:
            ImportError: If PyYAML is not installed

        """
        return YamlFormatter.stringify(data, default_flow_style)

    @staticmethod
    def merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two YAML dictionaries.

        Args:
            base: Base dictionary
            override: Dictionary to merge on top

        Returns:
            Merged dictionary

        """
        return YamlFormatter.merge(base, override)


# Re-export YamlFormatter for direct use
__all__ = ["YamlFormatter", "YamlUtils"]
