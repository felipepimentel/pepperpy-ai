"""Parsers functionality for PepperPy formats.

This module provides parsers for various data formats, with consistent
interfaces and error handling.
"""

import json
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Any

import yaml


class Parser(ABC):
    """Base class for data format parsers."""

    @abstractmethod
    def parse(self, content: str) -> Any:
        """Parse content from string.

        Args:
            content: String content to parse

        Returns:
            Parsed content in appropriate format

        """

    @abstractmethod
    def parse_file(self, file_path: str) -> Any:
        """Parse content from file.

        Args:
            file_path: Path to file to parse

        Returns:
            Parsed content in appropriate format

        """


class TextParser(Parser):
    """Parser for plain text content."""

    def parse(self, content: str) -> str:
        """Parse text content.

        Args:
            content: Text content to parse

        Returns:
            Processed text content

        """
        return content.strip()

    def parse_file(self, file_path: str) -> str:
        """Parse text from file.

        Args:
            file_path: Path to text file

        Returns:
            Processed text content

        """
        with open(file_path, encoding="utf-8") as f:
            return self.parse(f.read())


class JsonParser(Parser):
    """Parser for JSON content."""

    def __init__(self, **kwargs: Any):
        """Initialize JSON parser.

        Args:
            **kwargs: Additional arguments passed to json.loads/json.load

        """
        self.kwargs = kwargs

    def parse(self, content: str) -> Any:
        """Parse JSON content.

        Args:
            content: JSON content to parse

        Returns:
            Parsed JSON data

        """
        return json.loads(content, **self.kwargs)

    def parse_file(self, file_path: str) -> Any:
        """Parse JSON from file.

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed JSON data

        """
        with open(file_path, encoding="utf-8") as f:
            return json.load(f, **self.kwargs)


class YamlParser(Parser):
    """Parser for YAML content."""

    def __init__(self, **kwargs: Any):
        """Initialize YAML parser.

        Args:
            **kwargs: Additional arguments passed to yaml.safe_load

        """
        self.kwargs = kwargs

    def parse(self, content: str) -> Any:
        """Parse YAML content.

        Args:
            content: YAML content to parse

        Returns:
            Parsed YAML data

        """
        return yaml.safe_load(content, **self.kwargs)

    def parse_file(self, file_path: str) -> Any:
        """Parse YAML from file.

        Args:
            file_path: Path to YAML file

        Returns:
            Parsed YAML data

        """
        with open(file_path, encoding="utf-8") as f:
            return yaml.safe_load(f, **self.kwargs)


class XmlParser(Parser):
    """Parser for XML content."""

    def __init__(self, **kwargs: Any):
        """Initialize XML parser.

        Args:
            **kwargs: Additional arguments passed to ElementTree.parse

        """
        self.kwargs = kwargs

    def parse(self, content: str) -> ET.Element:
        """Parse XML content.

        Args:
            content: XML content to parse

        Returns:
            Parsed XML element tree

        """
        return ET.fromstring(content, **self.kwargs)

    def parse_file(self, file_path: str) -> ET.ElementTree:
        """Parse XML from file.

        Args:
            file_path: Path to XML file

        Returns:
            Parsed XML element tree

        """
        return ET.parse(file_path, **self.kwargs)
