"""Serialization utilities for PepperPy.

This module provides utilities for serializing and deserializing data in various formats:
- JSON: JavaScript Object Notation
- YAML: YAML Ain't Markup Language
- XML: Extensible Markup Language
- CSV: Comma-Separated Values

The module centralizes all serialization functionality to provide a consistent interface
for working with different data formats throughout the framework.
"""

import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
    TypeVar,
    Union,
    cast,
    overload,
)
from xml.dom import minidom
from xml.etree import ElementTree as ET

from pepperpy.core.common.utils.dates import DateUtils
from pepperpy.formats.json import JsonUtils
from pepperpy.formats.yaml import YamlUtils

T = TypeVar("T")
D = TypeVar("D", bound=Dict[str, Any])


class SerializationUtils:
    """Base class for serialization utilities."""

    @staticmethod
    def serialize_object(obj: Any) -> Any:
        """Serialize an object to a JSON-compatible format.

        Args:
            obj: Object to serialize

        Returns:
            JSON-compatible object
        """
        if isinstance(obj, datetime):
            return DateUtils.format_date(obj, DateUtils.DEFAULT_DATETIME_FORMAT)
        elif isinstance(obj, Decimal):
            return str(obj)
        elif hasattr(obj, "to_dict"):
            return obj.to_dict()
        elif hasattr(obj, "dict"):
            return obj.dict()
        return str(obj)


class XmlUtils:
    """Utility functions for XML manipulation."""

    @staticmethod
    def load(path: Union[str, Path]) -> ET.Element:
        """Load XML from file.

        Args:
            path: File path

        Returns:
            Parsed XML element
        """
        return ET.parse(path).getroot()

    @staticmethod
    def save(
        element: ET.Element,
        path: Union[str, Path],
        encoding: str = "utf-8",
        pretty: bool = True,
    ) -> None:
        """Save XML element to file.

        Args:
            element: XML element to save
            path: File path
            encoding: File encoding
            pretty: Whether to format output
        """
        tree = ET.ElementTree(element)
        if pretty:
            xml_str = ET.tostring(element, encoding=encoding)
            dom = minidom.parseString(xml_str)
            with open(path, "w", encoding=encoding) as f:
                f.write(dom.toprettyxml(indent="  "))
        else:
            tree.write(path, encoding=encoding)

    @staticmethod
    def dumps(element: ET.Element, encoding: str = "utf-8", pretty: bool = True) -> str:
        """Convert XML element to string.

        Args:
            element: XML element to convert
            encoding: String encoding
            pretty: Whether to format output

        Returns:
            XML string
        """
        if pretty:
            xml_str = ET.tostring(element, encoding=encoding)
            dom = minidom.parseString(xml_str)
            return dom.toprettyxml(indent="  ")
        return ET.tostring(element, encoding=encoding).decode(encoding)

    @staticmethod
    def loads(data: str) -> ET.Element:
        """Parse XML string.

        Args:
            data: XML string

        Returns:
            Parsed XML element
        """
        return ET.fromstring(data)

    @staticmethod
    def to_dict(element: ET.Element) -> Union[Dict[str, Any], str]:
        """Convert XML element to dictionary.

        Args:
            element: XML element to convert

        Returns:
            Dictionary representation or text content
        """
        result: Dict[str, Any] = {}

        # Add attributes
        for key, value in element.attrib.items():
            result[f"@{key}"] = value

        # Add children
        for child in element:
            child_dict = XmlUtils.to_dict(child)
            if child.tag in result:
                if isinstance(result[child.tag], list):
                    result[child.tag].append(child_dict)
                else:
                    result[child.tag] = [result[child.tag], child_dict]
            else:
                result[child.tag] = child_dict

        # Add text content
        if element.text and element.text.strip():
            if result:
                result["#text"] = element.text.strip()
            else:
                return element.text.strip()

        return result

    @staticmethod
    def from_dict(data: Dict[str, Any], root_tag: str) -> ET.Element:
        """Convert dictionary to XML element.

        Args:
            data: Dictionary to convert
            root_tag: Root element tag

        Returns:
            XML element
        """
        root = ET.Element(root_tag)

        def _add_dict(parent: ET.Element, d: Dict[str, Any]) -> None:
            for key, value in d.items():
                if key.startswith("@"):
                    parent.set(key[1:], str(value))
                elif key == "#text":
                    parent.text = str(value)
                else:
                    if isinstance(value, list):
                        for item in value:
                            child = ET.SubElement(parent, key)
                            if isinstance(item, dict):
                                _add_dict(child, item)
                            else:
                                child.text = str(item)
                    else:
                        child = ET.SubElement(parent, key)
                        if isinstance(value, dict):
                            _add_dict(child, value)
                        else:
                            child.text = str(value)

        _add_dict(root, data)
        return root

    @staticmethod
    def find(
        element: ET.Element, xpath: str, namespaces: Optional[Dict[str, str]] = None
    ) -> Optional[ET.Element]:
        """Find first element matching XPath.

        Args:
            element: XML element to search
            xpath: XPath expression
            namespaces: Namespace map

        Returns:
            Matching element or None
        """
        return element.find(xpath, namespaces)

    @staticmethod
    def find_all(
        element: ET.Element, xpath: str, namespaces: Optional[Dict[str, str]] = None
    ) -> List[ET.Element]:
        """Find all elements matching XPath.

        Args:
            element: XML element to search
            xpath: XPath expression
            namespaces: Namespace map

        Returns:
            List of matching elements
        """
        return element.findall(xpath, namespaces)

    @staticmethod
    def get_text(
        element: ET.Element,
        xpath: str,
        namespaces: Optional[Dict[str, str]] = None,
        default: str = "",
    ) -> str:
        """Get text content of element matching XPath.

        Args:
            element: XML element to search
            xpath: XPath expression
            namespaces: Namespace map
            default: Default value if not found

        Returns:
            Text content or default
        """
        found = element.find(xpath, namespaces)
        return found.text.strip() if found is not None and found.text else default

    @staticmethod
    def get_attr(
        element: ET.Element,
        xpath: str,
        attr: str,
        namespaces: Optional[Dict[str, str]] = None,
        default: str = "",
    ) -> str:
        """Get attribute value of element matching XPath.

        Args:
            element: XML element to search
            xpath: XPath expression
            attr: Attribute name
            namespaces: Namespace map
            default: Default value if not found

        Returns:
            Attribute value or default
        """
        found = element.find(xpath, namespaces)
        return found.get(attr, default) if found is not None else default


class CsvUtils:
    """Utility functions for CSV manipulation."""

    @overload
    @staticmethod
    def load(
        path: Union[str, Path],
        delimiter: str = ",",
        quotechar: str = '"',
        has_header: bool = True,
    ) -> List[Dict[str, str]]: ...

    @overload
    @staticmethod
    def load(
        path: Union[str, Path],
        delimiter: str = ",",
        quotechar: str = '"',
        has_header: bool = False,
    ) -> List[List[str]]: ...

    @staticmethod
    def load(
        path: Union[str, Path],
        delimiter: str = ",",
        quotechar: str = '"',
        has_header: bool = True,
    ) -> Union[List[Dict[str, str]], List[List[str]]]:
        """Load CSV from file.

        Args:
            path: File path
            delimiter: Field delimiter
            quotechar: Quote character
            has_header: Whether file has header row

        Returns:
            List of dictionaries (with header) or list of lists (without header)
        """
        with open(path, "r", encoding="utf-8", newline="") as f:
            if has_header:
                reader = csv.DictReader(f, delimiter=delimiter, quotechar=quotechar)
                return list(reader)
            else:
                reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)
                return list(reader)

    @staticmethod
    def save(
        data: Union[List[Dict[str, Any]], List[List[Any]]],
        path: Union[str, Path],
        delimiter: str = ",",
        quotechar: str = '"',
        header: Optional[List[str]] = None,
    ) -> None:
        """Save data to CSV file.

        Args:
            data: Data to save (list of dictionaries or list of lists)
            path: File path
            delimiter: Field delimiter
            quotechar: Quote character
            header: Header row (required for list of lists)
        """
        with open(path, "w", encoding="utf-8", newline="") as f:
            if data and isinstance(data[0], dict):
                dict_data = cast(List[Dict[str, Any]], data)
                fieldnames = header or list(dict_data[0].keys())
                writer = csv.DictWriter(
                    f,
                    fieldnames=fieldnames,
                    delimiter=delimiter,
                    quotechar=quotechar,
                    quoting=csv.QUOTE_MINIMAL,
                )
                writer.writeheader()
                writer.writerows(dict_data)
            else:
                list_data = cast(List[List[Any]], data)
                writer = csv.writer(
                    f,
                    delimiter=delimiter,
                    quotechar=quotechar,
                    quoting=csv.QUOTE_MINIMAL,
                )
                if header:
                    writer.writerow(header)
                writer.writerows(list_data)

    @staticmethod
    def dumps(
        data: Union[List[Dict[str, Any]], List[List[Any]]],
        delimiter: str = ",",
        quotechar: str = '"',
        header: Optional[List[str]] = None,
    ) -> str:
        """Convert data to CSV string.

        Args:
            data: Data to convert (list of dictionaries or list of lists)
            delimiter: Field delimiter
            quotechar: Quote character
            header: Header row (required for list of lists)

        Returns:
            CSV string
        """
        import io

        output = io.StringIO()
        if data and isinstance(data[0], dict):
            dict_data = cast(List[Dict[str, Any]], data)
            fieldnames = header or list(dict_data[0].keys())
            writer = csv.DictWriter(
                output,
                fieldnames=fieldnames,
                delimiter=delimiter,
                quotechar=quotechar,
                quoting=csv.QUOTE_MINIMAL,
            )
            writer.writeheader()
            writer.writerows(dict_data)
        else:
            list_data = cast(List[List[Any]], data)
            writer = csv.writer(
                output,
                delimiter=delimiter,
                quotechar=quotechar,
                quoting=csv.QUOTE_MINIMAL,
            )
            if header:
                writer.writerow(header)
            writer.writerows(list_data)
        return output.getvalue()

    @overload
    @staticmethod
    def loads(
        data: str, delimiter: str = ",", quotechar: str = '"', has_header: bool = True
    ) -> List[Dict[str, str]]: ...

    @overload
    @staticmethod
    def loads(
        data: str, delimiter: str = ",", quotechar: str = '"', has_header: bool = False
    ) -> List[List[str]]: ...

    @staticmethod
    def loads(
        data: str, delimiter: str = ",", quotechar: str = '"', has_header: bool = True
    ) -> Union[List[Dict[str, str]], List[List[str]]]:
        """Parse CSV string.

        Args:
            data: CSV string
            delimiter: Field delimiter
            quotechar: Quote character
            has_header: Whether data has header row

        Returns:
            List of dictionaries (with header) or list of lists (without header)
        """
        import io

        f = io.StringIO(data)
        if has_header:
            reader = csv.DictReader(f, delimiter=delimiter, quotechar=quotechar)
            return list(reader)
        else:
            reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)
            return list(reader)

    @staticmethod
    def to_json(
        data: Union[List[Dict[str, Any]], List[List[Any]]],
        header: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Convert CSV data to JSON format.

        Args:
            data: CSV data (list of dictionaries or list of lists)
            header: Header row (required for list of lists)

        Returns:
            JSON data (list of dictionaries)
        """
        if data and isinstance(data[0], dict):
            return cast(List[Dict[str, Any]], data)
        else:
            list_data = cast(List[List[Any]], data)
            if not header:
                raise ValueError("Header is required for list of lists")
            return [dict(zip(header, row)) for row in list_data]

    @staticmethod
    def from_json(data: List[Dict[str, Any]]) -> tuple[List[str], List[List[Any]]]:
        """Convert JSON data to CSV format.

        Args:
            data: JSON data (list of dictionaries)

        Returns:
            Tuple of (header, rows)
        """
        if not data:
            return [], []
        header = list(data[0].keys())
        rows = [[row.get(key, "") for key in header] for row in data]
        return header, rows


# Export all types
__all__ = [
    "SerializationUtils",
    "JsonUtils",
    "YamlUtils",
    "XmlUtils",
    "CsvUtils",
]
