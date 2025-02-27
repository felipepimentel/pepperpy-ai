"""Formatters functionality for PepperPy formats.

This module provides formatters for various data formats, with consistent
interfaces and error handling.
"""

import json
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Any, Optional

import yaml


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
        pass

    @abstractmethod
    def format_to_file(self, data: Any, file_path: str) -> None:
        """Format data and write to file.

        Args:
            data: Data to format
            file_path: Path to output file
        """
        pass


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
        self.kwargs = {"indent": indent, **kwargs}

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


class YamlFormatter(Formatter):
    """Formatter for YAML content."""

    def __init__(self, default_flow_style: bool = False, **kwargs: Any):
        """Initialize YAML formatter.

        Args:
            default_flow_style: YAML flow style setting
            **kwargs: Additional arguments passed to yaml.dump
        """
        self.kwargs = {"default_flow_style": default_flow_style, **kwargs}

    def format(self, data: Any) -> str:
        """Format data as YAML.

        Args:
            data: Data to format as YAML

        Returns:
            YAML string representation
        """
        return yaml.dump(data, **self.kwargs)

    def format_to_file(self, data: Any, file_path: str) -> None:
        """Format data as YAML and write to file.

        Args:
            data: Data to format as YAML
            file_path: Path to output file
        """
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, **self.kwargs)


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
