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


class TextProcessor:
    """Processor for text data.

    This class provides methods for processing text data, including:
    - Loading text from files
    - Saving text to files
    - Converting between formats
    - Basic text processing operations
    """

    def __init__(self) -> None:
        """Initialize the text processor."""
        self.formats = {
            "plain": PlainTextFormat(),
            "markdown": MarkdownFormat(),
            "json": JSONFormat(),
            "yaml": YAMLFormat(),
            "xml": XMLFormat(),
        }

    def load_file(self, file_path: str) -> Any:
        """Load text from a file.

        Args:
            file_path: Path to the text file

        Returns:
            Loaded text data (type depends on format)

        Raises:
            FormatError: If the file format is not supported or loading fails
        """
        extension = file_path.split(".")[-1].lower()
        if extension not in self.get_supported_extensions():
            raise FormatError(f"Unsupported text format: {extension}")

        format_handler = self._get_format_for_extension(extension)
        with open(file_path, "rb") as f:
            data = f.read()

        return format_handler.deserialize(data)

    def save_file(self, data: Any, file_path: str) -> None:
        """Save text to a file.

        Args:
            data: Text data to save (type depends on format)
            file_path: Path to save the text file

        Raises:
            FormatError: If the file format is not supported or saving fails
        """
        extension = file_path.split(".")[-1].lower()
        if extension not in self.get_supported_extensions():
            raise FormatError(f"Unsupported text format: {extension}")

        format_handler = self._get_format_for_extension(extension)
        data_bytes = format_handler.serialize(data)

        with open(file_path, "wb") as f:
            f.write(data_bytes)

    def convert_format(self, data: Any, source_format: str, target_format: str) -> Any:
        """Convert text from one format to another.

        Args:
            data: Text data to convert
            source_format: Source format extension (e.g., 'json', 'yaml')
            target_format: Target format extension (e.g., 'json', 'yaml')

        Returns:
            Converted text data

        Raises:
            FormatError: If the source or target format is not supported
        """
        if source_format not in self.get_supported_extensions():
            raise FormatError(f"Unsupported source format: {source_format}")
        if target_format not in self.get_supported_extensions():
            raise FormatError(f"Unsupported target format: {target_format}")

        source_handler = self._get_format_for_extension(source_format)
        target_handler = self._get_format_for_extension(target_format)

        # For simple text formats, we can just convert directly
        if isinstance(source_handler, (PlainTextFormat, MarkdownFormat)) and isinstance(
            target_handler, (PlainTextFormat, MarkdownFormat)
        ):
            return data

        # For structured formats, we need to serialize and deserialize
        if isinstance(source_handler, (JSONFormat, YAMLFormat)) and isinstance(
            target_handler, (JSONFormat, YAMLFormat)
        ):
            return data  # Both are already structured data

        # XML requires special handling
        if isinstance(source_handler, XMLFormat) and isinstance(
            target_handler, (JSONFormat, YAMLFormat)
        ):
            # Convert XML to dict (simplified)
            raise FormatError(
                "XML to JSON/YAML conversion requires additional libraries"
            )

        if isinstance(source_handler, (JSONFormat, YAMLFormat)) and isinstance(
            target_handler, XMLFormat
        ):
            # Convert dict to XML (simplified)
            raise FormatError(
                "JSON/YAML to XML conversion requires additional libraries"
            )

        # Default fallback: serialize to bytes and deserialize
        serialized = source_handler.serialize(data)
        if isinstance(source_handler, (PlainTextFormat, MarkdownFormat)) and isinstance(
            target_handler, (JSONFormat, YAMLFormat)
        ):
            # Text to structured - try to parse as JSON first
            try:
                return json.loads(serialized.decode("utf-8"))
            except:
                raise FormatError(
                    "Cannot convert plain text to structured format automatically"
                )

        return target_handler.deserialize(serialized)

    def get_supported_formats(self) -> Dict[str, FormatHandler]:
        """Get all supported text formats.

        Returns:
            Dictionary of format handlers
        """
        return self.formats

    def get_supported_extensions(self) -> list[str]:
        """Get all supported file extensions.

        Returns:
            List of supported file extensions
        """
        extensions = []
        for format_handler in self.formats.values():
            extensions.extend(format_handler.file_extensions)
        return extensions

    def _get_format_for_extension(self, extension: str) -> FormatHandler:
        """Get the format handler for a file extension.

        Args:
            extension: File extension

        Returns:
            Format handler

        Raises:
            FormatError: If no handler is found for the extension
        """
        for format_name, format_handler in self.formats.items():
            if extension in format_handler.file_extensions:
                return format_handler

        raise FormatError(f"No handler found for extension: {extension}")
