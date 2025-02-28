"""YAML utilities.

This module provides utilities for working with YAML data.
"""

from pathlib import Path
from typing import Any, Dict, Union

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class YamlUtils:
    """Utility functions for YAML manipulation."""

    @staticmethod
    def _ensure_yaml_available():
        """Ensure PyYAML is available.

        Raises:
            ImportError: If PyYAML is not installed
        """
        if not YAML_AVAILABLE:
            raise ImportError(
                "PyYAML is required for YAML operations. "
                "Install it with: pip install pyyaml"
            )

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
        YamlUtils._ensure_yaml_available()
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @staticmethod
    def save(
        data: Dict[str, Any], path: Union[str, Path], default_flow_style: bool = False
    ) -> None:
        """Save dictionary to YAML file.

        Args:
            data: Dictionary to save
            path: File path
            default_flow_style: YAML flow style

        Raises:
            ImportError: If PyYAML is not installed
        """
        YamlUtils._ensure_yaml_available()
        path = Path(path)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=default_flow_style)

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
        YamlUtils._ensure_yaml_available()
        return yaml.safe_load(text)

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
        YamlUtils._ensure_yaml_available()
        return yaml.dump(data, default_flow_style=default_flow_style)

    @staticmethod
    def merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two YAML dictionaries.

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
                result[key] = YamlUtils.merge(result[key], value)
            else:
                result[key] = value
        return result
