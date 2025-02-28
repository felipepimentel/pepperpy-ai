"""Utilitários para manipulação de arquivos XML (DEPRECATED).

Implementa funções auxiliares para manipulação e formatação de arquivos XML.

This module is deprecated and will be removed in version 1.0.0.
Please use 'pepperpy.core.utils.serialization.XmlUtils' instead.
"""

import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from xml.dom import minidom
from xml.etree import ElementTree as ET

# Show deprecation warning
warnings.warn(
    "The 'pepperpy.core.utils.xml' module is deprecated and will be removed in version 1.0.0. "
    "Please use 'pepperpy.core.utils.serialization.XmlUtils' instead.",
    DeprecationWarning,
    stacklevel=2,
)


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
