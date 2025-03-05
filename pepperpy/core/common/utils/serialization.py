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
    Callable,
    Dict,
    List,
    Optional,
    Type,
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
        if isinstance(obj, Decimal):
            return str(obj)
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        if hasattr(obj, "dict"):
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
                elif isinstance(value, list):
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
        element: ET.Element,
        xpath: str,
        namespaces: Optional[Dict[str, str]] = None,
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
        element: ET.Element,
        xpath: str,
        namespaces: Optional[Dict[str, str]] = None,
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
        with open(path, encoding="utf-8", newline="") as f:
            if has_header:
                reader = csv.DictReader(f, delimiter=delimiter, quotechar=quotechar)
                return list(reader)
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
        data: str,
        delimiter: str = ",",
        quotechar: str = '"',
        has_header: bool = True,
    ) -> List[Dict[str, str]]: ...

    @overload
    @staticmethod
    def loads(
        data: str,
        delimiter: str = ",",
        quotechar: str = '"',
        has_header: bool = False,
    ) -> List[List[str]]: ...

    @staticmethod
    def loads(
        data: str,
        delimiter: str = ",",
        quotechar: str = '"',
        has_header: bool = True,
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
    "CsvUtils",
    "JsonUtils",
    "SerializationUtils",
    "XmlUtils",
    "YamlUtils",
]


def serialize(
    data: Any,
    format_type: str = "json",
    file_path: Optional[Union[str, Path]] = None,
    **kwargs: Any,
) -> Optional[str]:
    """Serialize data to the specified format.

    This function provides a unified interface for serializing data to different formats.
    It supports JSON, YAML, XML, and CSV formats.

    Args:
        data: The data to serialize
        format_type: The format to serialize to ('json', 'yaml', 'xml', 'csv')
        file_path: Optional file path to save the serialized data
        **kwargs: Additional format-specific arguments

    Returns:
        The serialized data as a string if file_path is None, otherwise None

    Examples:
        >>> data = {"name": "John", "age": 30}
        >>> serialize(data, "json")
        '{"name": "John", "age": 30}'
        >>> serialize(data, "yaml")
        'name: John\\nage: 30\\n'
    """
    format_type = format_type.lower()
    result: Optional[str] = None

    if format_type == "json":
        indent = kwargs.get("indent", 2)
        if file_path:
            JsonUtils.save(data, file_path, indent=indent)
        else:
            result = JsonUtils.dumps(data, indent=indent)
    elif format_type == "yaml":
        if file_path:
            YamlUtils.save(data, file_path)
        else:
            result = YamlUtils.dumps(data)
    elif format_type == "xml":
        root_tag = kwargs.get("root_tag", "root")
        encoding = kwargs.get("encoding", "utf-8")
        pretty = kwargs.get("pretty", True)

        if isinstance(data, ET.Element):
            element = data
        elif isinstance(data, dict):
            element = XmlUtils.from_dict(data, root_tag)
        else:
            raise ValueError(f"Cannot serialize {type(data)} to XML")

        if file_path:
            XmlUtils.save(element, file_path, encoding=encoding, pretty=pretty)
        else:
            result = XmlUtils.dumps(element, encoding=encoding, pretty=pretty)
    elif format_type == "csv":
        delimiter = kwargs.get("delimiter", ",")
        quotechar = kwargs.get("quotechar", '"')
        header = kwargs.get("header", None)

        if file_path:
            CsvUtils.save(
                data, file_path, delimiter=delimiter, quotechar=quotechar, header=header
            )
        else:
            result = CsvUtils.dumps(
                data, delimiter=delimiter, quotechar=quotechar, header=header
            )
    else:
        raise ValueError(f"Unsupported format: {format_type}")

    return result


def deserialize(
    data: Union[str, Path],
    format_type: str = "json",
    target_type: Optional[Type[T]] = None,
    **kwargs: Any,
) -> Any:
    """Deserialize data from the specified format.

    This function provides a unified interface for deserializing data from different formats.
    It supports JSON, YAML, XML, and CSV formats.

    Args:
        data: The data to deserialize (string or file path)
        format_type: The format to deserialize from ('json', 'yaml', 'xml', 'csv')
        target_type: Optional type to convert the deserialized data to
        **kwargs: Additional format-specific arguments

    Returns:
        The deserialized data

    Examples:
        >>> deserialize('{"name": "John", "age": 30}', "json")
        {'name': 'John', 'age': 30}
        >>> deserialize('name: John\\nage: 30', "yaml")
        {'name': 'John', 'age': 30}
    """
    format_type = format_type.lower()
    result: Any = None

    # Check if data is a file path
    if isinstance(data, (str, Path)) and Path(data).is_file():
        file_path = Path(data)
        if format_type == "json":
            result = JsonUtils.load(file_path)
        elif format_type == "yaml":
            result = YamlUtils.load(file_path)
        elif format_type == "xml":
            result = XmlUtils.load(file_path)
            if kwargs.get("as_dict", False):
                result = XmlUtils.to_dict(result)
        elif format_type == "csv":
            delimiter = kwargs.get("delimiter", ",")
            quotechar = kwargs.get("quotechar", '"')
            has_header = kwargs.get("has_header", True)
            result = CsvUtils.load(
                file_path,
                delimiter=delimiter,
                quotechar=quotechar,
                has_header=has_header,
            )
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    # Otherwise, treat data as a string
    elif isinstance(data, str):
        if format_type == "json":
            result = JsonUtils.loads(data)
        elif format_type == "yaml":
            result = YamlUtils.loads(data)
        elif format_type == "xml":
            result = XmlUtils.loads(data)
            if kwargs.get("as_dict", False):
                result = XmlUtils.to_dict(result)
        elif format_type == "csv":
            delimiter = kwargs.get("delimiter", ",")
            quotechar = kwargs.get("quotechar", '"')
            has_header = kwargs.get("has_header", True)
            result = CsvUtils.loads(
                data, delimiter=delimiter, quotechar=quotechar, has_header=has_header
            )
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    else:
        raise ValueError(f"Cannot deserialize data of type {type(data)}")

    # Convert to target type if specified
    if target_type is not None:
        if hasattr(target_type, "from_dict") and callable(target_type.from_dict):
            from_dict_method = cast(
                Callable[[Dict[str, Any]], T], target_type.from_dict
            )
            if isinstance(result, dict):
                result = from_dict_method(result)
            else:
                raise ValueError(
                    f"Cannot convert {type(result)} to {target_type} using from_dict"
                )
        elif hasattr(target_type, "parse_obj") and callable(target_type.parse_obj):
            parse_obj_method = cast(
                Callable[[Dict[str, Any]], T], target_type.parse_obj
            )
            if isinstance(result, dict):
                result = parse_obj_method(result)
            else:
                raise ValueError(
                    f"Cannot convert {type(result)} to {target_type} using parse_obj"
                )
        else:
            # Try to instantiate the target type with the result as kwargs
            if isinstance(result, dict):
                result = target_type(**result)  # type: ignore
            else:
                raise ValueError(f"Cannot convert {type(result)} to {target_type}")

    return result
