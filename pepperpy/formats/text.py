"""Text format handlers for the unified format handling system.

This module provides format handlers for text-based formats:
- PlainTextFormat: Plain text format
- MarkdownFormat: Markdown format
- JSONFormat: JSON format
- YAMLFormat: YAML format
- XMLFormat: XML format
"""

import json
import xml.dom.minidom
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Union

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from .base import FormatError, FormatHandler


class PlainTextFormat(FormatHandler[str]):
    """Handler for plain text format."""

    @property
    def mime_type(self) -> str:
        """Get the MIME type for this format.

        Returns:
            MIME type string

        """
        return "text/plain"

    @property
    def file_extensions(self) -> list[str]:
        """Get the file extensions for this format.

        Returns:
            List of file extensions (without dot)

        """
        return ["txt", "text"]

    def serialize(self, data: str) -> bytes:
        """Serialize string to bytes.

        Args:
            data: String to serialize

        Returns:
            Serialized data as bytes

        Raises:
            FormatError: If serialization fails

        """
        try:
            return data.encode("utf-8")
        except Exception as e:
            raise FormatError(f"Failed to serialize text: {e!s}") from e

    def deserialize(self, data: bytes) -> str:
        """Deserialize bytes to string.

        Args:
            data: Bytes to deserialize

        Returns:
            Deserialized string

        Raises:
            FormatError: If deserialization fails

        """
        try:
            return data.decode("utf-8")
        except Exception as e:
            raise FormatError(f"Failed to deserialize text: {e!s}") from e


class MarkdownFormat(FormatHandler[str]):
    """Handler for Markdown format."""

    @property
    def mime_type(self) -> str:
        """Get the MIME type for this format.

        Returns:
            MIME type string

        """
        return "text/markdown"

    @property
    def file_extensions(self) -> list[str]:
        """Get the file extensions for this format.

        Returns:
            List of file extensions (without dot)

        """
        return ["md", "markdown"]

    def serialize(self, data: str) -> bytes:
        """Serialize Markdown to bytes.

        Args:
            data: Markdown string to serialize

        Returns:
            Serialized data as bytes

        Raises:
            FormatError: If serialization fails

        """
        try:
            return data.encode("utf-8")
        except Exception as e:
            raise FormatError(f"Failed to serialize Markdown: {e!s}") from e

    def deserialize(self, data: bytes) -> str:
        """Deserialize bytes to Markdown.

        Args:
            data: Bytes to deserialize

        Returns:
            Deserialized Markdown string

        Raises:
            FormatError: If deserialization fails

        """
        try:
            return data.decode("utf-8")
        except Exception as e:
            raise FormatError(f"Failed to deserialize Markdown: {e!s}") from e


class JSONFormat(FormatHandler[Union[Dict[str, Any], List[Any]]]):
    """Handler for JSON format."""

    @property
    def mime_type(self) -> str:
        """Get the MIME type for this format.

        Returns:
            MIME type string

        """
        return "application/json"

    @property
    def file_extensions(self) -> list[str]:
        """Get the file extensions for this format.

        Returns:
            List of file extensions (without dot)

        """
        return ["json"]

    def serialize(self, data: Union[Dict[str, Any], List[Any]]) -> bytes:
        """Serialize JSON to bytes.

        Args:
            data: JSON data to serialize

        Returns:
            Serialized data as bytes

        Raises:
            FormatError: If serialization fails

        """
        try:
            return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        except Exception as e:
            raise FormatError(f"Failed to serialize JSON: {e!s}") from e

    def deserialize(self, data: bytes) -> Union[Dict[str, Any], List[Any]]:
        """Deserialize bytes to JSON.

        Args:
            data: Bytes to deserialize

        Returns:
            Deserialized JSON data

        Raises:
            FormatError: If deserialization fails

        """
        try:
            return json.loads(data.decode("utf-8"))
        except Exception as e:
            raise FormatError(f"Failed to deserialize JSON: {e!s}") from e


class YAMLFormat(FormatHandler[Union[Dict[str, Any], List[Any]]]):
    """Handler for YAML format."""

    @property
    def mime_type(self) -> str:
        """Get the MIME type for this format.

        Returns:
            MIME type string

        """
        return "application/yaml"

    @property
    def file_extensions(self) -> list[str]:
        """Get the file extensions for this format.

        Returns:
            List of file extensions (without dot)

        """
        return ["yaml", "yml"]

    def serialize(self, data: Union[Dict[str, Any], List[Any]]) -> bytes:
        """Serialize YAML to bytes.

        Args:
            data: YAML data to serialize

        Returns:
            Serialized data as bytes

        Raises:
            FormatError: If serialization fails

        """
        if not YAML_AVAILABLE:
            raise FormatError("YAML support requires PyYAML package")

        try:
            return yaml.dump(data, default_flow_style=False).encode("utf-8")
        except Exception as e:
            raise FormatError(f"Failed to serialize YAML: {e!s}") from e

    def deserialize(self, data: bytes) -> Union[Dict[str, Any], List[Any]]:
        """Deserialize bytes to YAML.

        Args:
            data: Bytes to deserialize

        Returns:
            Deserialized YAML data

        Raises:
            FormatError: If deserialization fails

        """
        if not YAML_AVAILABLE:
            raise FormatError("YAML support requires PyYAML package")

        try:
            return yaml.safe_load(data.decode("utf-8"))
        except Exception as e:
            raise FormatError(f"Failed to deserialize YAML: {e!s}") from e


class XMLFormat(FormatHandler[ET.Element]):
    """Handler for XML format."""

    @property
    def mime_type(self) -> str:
        """Get the MIME type for this format.

        Returns:
            MIME type string

        """
        return "application/xml"

    @property
    def file_extensions(self) -> list[str]:
        """Get the file extensions for this format.

        Returns:
            List of file extensions (without dot)

        """
        return ["xml"]

    def serialize(self, data: ET.Element) -> bytes:
        """Serialize XML to bytes.

        Args:
            data: XML element to serialize

        Returns:
            Serialized data as bytes

        Raises:
            FormatError: If serialization fails

        """
        try:
            xml_str = ET.tostring(data, encoding="utf-8")
            # Pretty print
            dom = xml.dom.minidom.parseString(xml_str)
            pretty_xml = dom.toprettyxml(indent="  ")
            return pretty_xml.encode("utf-8")
        except Exception as e:
            raise FormatError(f"Failed to serialize XML: {e!s}") from e

    def deserialize(self, data: bytes) -> ET.Element:
        """Deserialize bytes to XML.

        Args:
            data: Bytes to deserialize

        Returns:
            Deserialized XML element

        Raises:
            FormatError: If deserialization fails

        """
        try:
            return ET.fromstring(data.decode("utf-8"))
        except Exception as e:
            raise FormatError(f"Failed to deserialize XML: {e!s}") from e
