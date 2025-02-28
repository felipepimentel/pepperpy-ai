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
import json
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

import yaml

from pepperpy.common.utils.dates import DateUtils

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


class JsonUtils:
    """Utility functions for JSON manipulation."""

    @staticmethod
    def load(path: Union[str, Path]) -> Any:
        """Load JSON from file.

        Args:
            path: File path

        Returns:
            Parsed JSON data
        """
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f, parse_float=Decimal)

    @staticmethod
    def save(data: Any, path: Union[str, Path], indent: Optional[int] = 2) -> None:
        """Save data to JSON file.

        Args:
            data: Data to save
            path: File path
            indent: Indentation level
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=indent,
                default=SerializationUtils.serialize_object,
                ensure_ascii=False,
            )

    @staticmethod
    def dumps(data: Any, indent: Optional[int] = None) -> str:
        """Convert data to JSON string.

        Args:
            data: Data to convert
            indent: Indentation level

        Returns:
            JSON string
        """
        return json.dumps(
            data,
            indent=indent,
            default=SerializationUtils.serialize_object,
            ensure_ascii=False,
        )

    @staticmethod
    def loads(data: str) -> Any:
        """Parse JSON string.

        Args:
            data: JSON string

        Returns:
            Parsed data
        """
        return json.loads(data, parse_float=Decimal)

    @staticmethod
    def merge(*jsons: Dict[str, Any], deep: bool = False) -> Dict[str, Any]:
        """Merge multiple JSON objects.

        Args:
            *jsons: JSON objects to merge
            deep: Whether to perform deep merge

        Returns:
            Merged JSON object
        """
        result: Dict[str, Any] = {}

        for data in jsons:
            if not deep:
                result.update(data)
            else:
                for key, value in data.items():
                    if (
                        key in result
                        and isinstance(result[key], dict)
                        and isinstance(value, dict)
                    ):
                        result[key] = JsonUtils.merge(result[key], value, deep=True)
                    else:
                        result[key] = value

        return result

    @staticmethod
    def flatten(
        data: Dict[str, Any], parent_key: str = "", separator: str = "."
    ) -> Dict[str, Any]:
        """Flatten nested JSON object.

        Args:
            data: JSON object to flatten
            parent_key: Parent key for nested items
            separator: Key separator

        Returns:
            Flattened JSON object
        """
        items: List[tuple[str, Any]] = []

        for key, value in data.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else key

            if isinstance(value, dict):
                items.extend(
                    JsonUtils.flatten(value, new_key, separator=separator).items()
                )
            else:
                items.append((new_key, value))

        return dict(items)

    @staticmethod
    def unflatten(data: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
        """Unflatten JSON object with dot notation keys.

        Args:
            data: Flattened JSON object
            separator: Key separator

        Returns:
            Nested JSON object
        """
        result: Dict[str, Any] = {}

        for key, value in data.items():
            parts = key.split(separator)
            current = result

            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            current[parts[-1]] = value

        return result

    @staticmethod
    def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """Validate JSON object against schema.

        Args:
            data: JSON object to validate
            schema: JSON schema

        Returns:
            List of validation errors
        """
        errors: List[str] = []

        def validate_type(value: Any, expected_type: str, path: str) -> None:
            if expected_type == "string":
                if not isinstance(value, str):
                    errors.append(
                        f"{path}: expected string, got {type(value).__name__}"
                    )
            elif expected_type == "number":
                if not isinstance(value, (int, float, Decimal)):
                    errors.append(
                        f"{path}: expected number, got {type(value).__name__}"
                    )
            elif expected_type == "integer":
                if not isinstance(value, int):
                    errors.append(
                        f"{path}: expected integer, got {type(value).__name__}"
                    )
            elif expected_type == "boolean":
                if not isinstance(value, bool):
                    errors.append(
                        f"{path}: expected boolean, got {type(value).__name__}"
                    )
            elif expected_type == "array":
                if not isinstance(value, list):
                    errors.append(f"{path}: expected array, got {type(value).__name__}")
            elif expected_type == "object":
                if not isinstance(value, dict):
                    errors.append(
                        f"{path}: expected object, got {type(value).__name__}"
                    )

        def validate_value(value: Any, schema_value: Dict[str, Any], path: str) -> None:
            if "type" in schema_value:
                validate_type(value, schema_value["type"], path)

            if "required" in schema_value and schema_value["required"]:
                if value is None:
                    errors.append(f"{path}: required field is missing")

            if "enum" in schema_value and value not in schema_value["enum"]:
                errors.append(f"{path}: value must be one of {schema_value['enum']}")

            if (
                "minLength" in schema_value
                and isinstance(value, str)
                and len(value) < schema_value["minLength"]
            ):
                errors.append(
                    f"{path}: string length must be >= {schema_value['minLength']}"
                )

            if (
                "maxLength" in schema_value
                and isinstance(value, str)
                and len(value) > schema_value["maxLength"]
            ):
                errors.append(
                    f"{path}: string length must be <= {schema_value['maxLength']}"
                )

        def validate_object(
            obj: Dict[str, Any], schema_obj: Dict[str, Any], path: str = ""
        ) -> None:
            if "properties" in schema_obj:
                for prop_name, prop_schema in schema_obj["properties"].items():
                    prop_path = f"{path}.{prop_name}" if path else prop_name
                    if prop_name in obj:
                        validate_value(obj[prop_name], prop_schema, prop_path)
                    elif "required" in prop_schema and prop_schema["required"]:
                        errors.append(f"{prop_path}: required field is missing")

            if "required" in schema_obj:
                for req_prop in schema_obj["required"]:
                    if req_prop not in obj:
                        req_path = f"{path}.{req_prop}" if path else req_prop
                        errors.append(f"{req_path}: required field is missing")

        validate_object(data, schema)
        return errors


class YamlUtils:
    """Utility functions for YAML manipulation."""

    @staticmethod
    def load(path: Union[str, Path]) -> Any:
        """Load YAML from file.

        Args:
            path: File path

        Returns:
            Parsed YAML data
        """
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @staticmethod
    def save(
        data: Any, path: Union[str, Path], default_flow_style: bool = False
    ) -> None:
        """Save data to YAML file.

        Args:
            data: Data to save
            path: File path
            default_flow_style: Whether to use flow style
        """
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(
                data,
                f,
                default_flow_style=default_flow_style,
                allow_unicode=True,
                sort_keys=False,
                default_style=None,
                indent=2,
                width=80,
                encoding="utf-8",
            )

    @staticmethod
    def dumps(data: Any, default_flow_style: bool = False) -> str:
        """Convert data to YAML string.

        Args:
            data: Data to convert
            default_flow_style: Whether to use flow style

        Returns:
            YAML string
        """
        return yaml.dump(
            data,
            default_flow_style=default_flow_style,
            allow_unicode=True,
            sort_keys=False,
            default_style=None,
            indent=2,
            width=80,
            encoding=None,
        )

    @staticmethod
    def loads(data: str) -> Any:
        """Parse YAML string.

        Args:
            data: YAML string

        Returns:
            Parsed data
        """
        return yaml.safe_load(data)

    @staticmethod
    def merge(*yamls: Dict[str, Any], deep: bool = False) -> Dict[str, Any]:
        """Merge multiple YAML objects.

        Args:
            *yamls: YAML objects to merge
            deep: Whether to perform deep merge

        Returns:
            Merged YAML object
        """
        result: Dict[str, Any] = {}

        for data in yamls:
            if not deep:
                result.update(data)
            else:
                for key, value in data.items():
                    if (
                        key in result
                        and isinstance(result[key], dict)
                        and isinstance(value, dict)
                    ):
                        result[key] = YamlUtils.merge(result[key], value, deep=True)
                    else:
                        result[key] = value

        return result

    @staticmethod
    def flatten(
        data: Dict[str, Any], parent_key: str = "", separator: str = "."
    ) -> Dict[str, Any]:
        """Flatten nested YAML object.

        Args:
            data: YAML object to flatten
            parent_key: Parent key for nested items
            separator: Key separator

        Returns:
            Flattened YAML object
        """
        items: List[tuple[str, Any]] = []

        for key, value in data.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else key

            if isinstance(value, dict):
                items.extend(
                    YamlUtils.flatten(value, new_key, separator=separator).items()
                )
            else:
                items.append((new_key, value))

        return dict(items)

    @staticmethod
    def unflatten(data: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
        """Unflatten YAML object with dot notation keys.

        Args:
            data: Flattened YAML object
            separator: Key separator

        Returns:
            Nested YAML object
        """
        result: Dict[str, Any] = {}

        for key, value in data.items():
            parts = key.split(separator)
            current = result

            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            current[parts[-1]] = value

        return result

    @staticmethod
    def to_json(data: Any) -> str:
        """Convert YAML to JSON string.

        Args:
            data: YAML data

        Returns:
            JSON string
        """
        return yaml.dump(
            data, default_flow_style=True, allow_unicode=True, sort_keys=False
        )

    @staticmethod
    def from_json(data: str) -> Any:
        """Convert JSON string to YAML.

        Args:
            data: JSON string

        Returns:
            YAML data
        """
        return yaml.safe_load(data)


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
