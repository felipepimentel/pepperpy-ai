"""Formatters functionality for PepperPy formats.

This module provides formatters for various data formats, with consistent
interfaces and error handling.
"""

import json
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class Formatter(ABC):
    """Base class for data format formatters."""

    @abstractmethod
    def format(self, data: Any) -> str:
        """Format data to string.

        Args:
            data: Data to format

        Returns:
            Formatted string representation

        """

    @abstractmethod
    def format_to_file(self, data: Any, file_path: str) -> None:
        """Format data and write to file.

        Args:
            data: Data to format
            file_path: Path to output file

        """


class TextFormatter(Formatter):
    """Formatter for plain text content."""

    def format(self, data: Any) -> str:
        """Format data as text.

        Args:
            data: Data to format as text

        Returns:
            Text representation

        """
        return str(data)

    def format_to_file(self, data: Any, file_path: str) -> None:
        """Format data as text and write to file.

        Args:
            data: Data to format as text
            file_path: Path to output file

        """
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.format(data))


class JsonFormatter(Formatter):
    """Formatter for JSON content."""

    def __init__(self, indent: Optional[int] = 2, **kwargs: Any):
        """Initialize JSON formatter.

        Args:
            indent: Number of spaces for indentation
            **kwargs: Additional arguments passed to json.dumps/json.dump

        """
        self.kwargs = {"indent": indent, "ensure_ascii": False, **kwargs}

    def format(self, data: Any) -> str:
        """Format data as JSON.

        Args:
            data: Data to format as JSON

        Returns:
            JSON string representation

        """
        return json.dumps(data, **self.kwargs)

    def format_to_file(self, data: Any, file_path: str) -> None:
        """Format data as JSON and write to file.

        Args:
            data: Data to format as JSON
            file_path: Path to output file

        """
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, **self.kwargs)

    @staticmethod
    def load(path: Union[str, Path]) -> Dict[str, Any]:
        """Load JSON from file.

        Args:
            path: File path

        Returns:
            JSON data as dictionary

        """
        path = Path(path)
        with open(path, encoding="utf-8") as f:
            return json.load(f)

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
                result[key] = JsonFormatter.merge(result[key], value)
            else:
                result[key] = value
        return result

    @staticmethod
    def get_value(
        data: Dict[str, Any], path: str, default: Any = None, separator: str = ".",
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
        data: Dict[str, Any], path: str, value: Any, separator: str = ".",
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


class YamlFormatter(Formatter):
    """Formatter for YAML content."""

    def __init__(self, default_flow_style: bool = False, **kwargs: Any):
        """Initialize YAML formatter.

        Args:
            default_flow_style: YAML flow style setting
            **kwargs: Additional arguments passed to yaml.dump

        """
        self.kwargs = {"default_flow_style": default_flow_style, **kwargs}
        self._ensure_yaml_available()

    @staticmethod
    def _ensure_yaml_available():
        """Ensure PyYAML is available.

        Raises:
            ImportError: If PyYAML is not installed

        """
        if not YAML_AVAILABLE:
            raise ImportError(
                "PyYAML is required for YAML operations. "
                "Install it with: pip install pyyaml",
            )

    def format(self, data: Any) -> str:
        """Format data as YAML.

        Args:
            data: Data to format as YAML

        Returns:
            YAML string representation

        """
        self._ensure_yaml_available()
        return yaml.dump(data, **self.kwargs)

    def format_to_file(self, data: Any, file_path: str) -> None:
        """Format data as YAML and write to file.

        Args:
            data: Data to format as YAML
            file_path: Path to output file

        """
        self._ensure_yaml_available()
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, **self.kwargs)

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
        YamlFormatter._ensure_yaml_available()
        path = Path(path)
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

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
        YamlFormatter._ensure_yaml_available()
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
        YamlFormatter._ensure_yaml_available()
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
                result[key] = YamlFormatter.merge(result[key], value)
            else:
                result[key] = value
        return result


class XmlFormatter(Formatter):
    """Formatter for XML content."""

    def __init__(self, encoding: str = "unicode", **kwargs: Any):
        """Initialize XML formatter.

        Args:
            encoding: Output encoding
            **kwargs: Additional arguments passed to ElementTree.write

        """
        self.encoding = encoding
        self.kwargs = kwargs

    def format(self, data: ET.Element) -> str:
        """Format XML element to string.

        Args:
            data: XML element to format

        Returns:
            XML string representation

        """
        return ET.tostring(data, encoding=self.encoding, **self.kwargs).decode("utf-8")

    def format_to_file(self, data: ET.Element, file_path: str) -> None:
        """Format XML element and write to file.

        Args:
            data: XML element to format
            file_path: Path to output file

        """
        tree = ET.ElementTree(data)
        tree.write(file_path, encoding=self.encoding, **self.kwargs)
