"""Core type definitions for PepperPy.

This module provides the core type definitions for the PepperPy framework,
including common types and utilities for type checking.
"""

import inspect
import types
from dataclasses import is_dataclass
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

# Type variable for parametric types
T = TypeVar("T")
U = TypeVar("U")


# JSON-compatible types
JsonPrimitive = Union[str, int, float, bool, None]
JsonObject = Dict[str, Any]  # Recursive type not expressible cleanly in Python
JsonArray = List[Any]  # Recursive type not expressible cleanly in Python
JsonValue = Union[JsonPrimitive, JsonObject, JsonArray]


class DataType(str, Enum):
    """Types of data that can be processed by PepperPy.

    These types represent the fundamental data types that are used throughout
    the PepperPy framework.
    """

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    EMBEDDING = "embedding"
    METADATA = "metadata"
    JSON = "json"
    BINARY = "binary"
    UNKNOWN = "unknown"


def get_data_type(value: Any) -> DataType:
    """Get the data type of a value.

    Args:
        value: The value to get the data type of

    Returns:
        The data type of the value
    """
    if value is None:
        return DataType.UNKNOWN

    # Check for string
    if isinstance(value, str):
        return DataType.TEXT

    # Check for bytes
    if isinstance(value, bytes):
        return DataType.BINARY

    # Check for JSON-compatible types
    if isinstance(value, (bool, int, float)):
        return DataType.JSON

    # Check for JSON-compatible containers
    if isinstance(value, dict):
        return DataType.JSON

    if isinstance(value, list):
        return DataType.JSON

    # Check for common metadata types
    if isinstance(value, datetime):
        return DataType.METADATA

    if isinstance(value, Enum):
        return DataType.METADATA

    # Check for data class
    if is_dataclass(value):
        return DataType.METADATA

    # Default to unknown
    return DataType.UNKNOWN


def is_optional_type(type_: Type) -> bool:
    """Check if a type is Optional[X].

    Args:
        type_: The type to check

    Returns:
        True if the type is Optional[X], False otherwise
    """
    origin = get_origin(type_)
    args = get_args(type_)

    return origin is Union and len(args) == 2 and isinstance(None, args[1])


def get_optional_type(type_: Type) -> Optional[Type]:
    """Get the type X from Optional[X].

    Args:
        type_: The optional type

    Returns:
        The type X, or None if the type is not Optional[X]
    """
    if not is_optional_type(type_):
        return None

    args = get_args(type_)
    return args[0]


def is_list_type(type_: Type) -> bool:
    """Check if a type is List[X].

    Args:
        type_: The type to check

    Returns:
        True if the type is List[X], False otherwise
    """
    origin = get_origin(type_)
    args = get_args(type_)

    return origin is list and len(args) == 1


def get_list_type(type_: Type) -> Optional[Type]:
    """Get the type X from List[X].

    Args:
        type_: The list type

    Returns:
        The type X, or None if the type is not List[X]
    """
    if not is_list_type(type_):
        return None

    args = get_args(type_)
    return args[0]


def is_dict_type(type_: Type) -> bool:
    """Check if a type is Dict[K, V].

    Args:
        type_: The type to check

    Returns:
        True if the type is Dict[K, V], False otherwise
    """
    origin = get_origin(type_)
    args = get_args(type_)

    return origin is dict and len(args) == 2


def get_dict_types(type_: Type) -> Optional[Tuple[Type, Type]]:
    """Get the types K and V from Dict[K, V].

    Args:
        type_: The dict type

    Returns:
        A tuple of (K, V), or None if the type is not Dict[K, V]
    """
    if not is_dict_type(type_):
        return None

    args = get_args(type_)
    return (args[0], args[1])


def is_union_type(type_: Type) -> bool:
    """Check if a type is Union[X, Y, ...].

    Args:
        type_: The type to check

    Returns:
        True if the type is Union[X, Y, ...], False otherwise
    """
    origin = get_origin(type_)
    return origin is Union


def get_union_types(type_: Type) -> Optional[Tuple[Type, ...]]:
    """Get the types X, Y, ... from Union[X, Y, ...].

    Args:
        type_: The union type

    Returns:
        A tuple of types, or None if the type is not Union[X, Y, ...]
    """
    if not is_union_type(type_):
        return None

    return get_args(type_)


def is_generic_type(type_: Type) -> bool:
    """Check if a type is a generic type.

    Args:
        type_: The type to check

    Returns:
        True if the type is a generic type, False otherwise
    """
    origin = get_origin(type_)
    args = get_args(type_)

    return origin is not None and len(args) > 0


def get_generic_origin(type_: Type) -> Optional[Type]:
    """Get the origin of a generic type.

    Args:
        type_: The generic type

    Returns:
        The origin of the generic type, or None if the type is not a generic type
    """
    if not is_generic_type(type_):
        return None

    return get_origin(type_)


def get_generic_args(type_: Type) -> Optional[Tuple[Type, ...]]:
    """Get the type arguments of a generic type.

    Args:
        type_: The generic type

    Returns:
        The type arguments of the generic type, or None if the type is not a generic type
    """
    if not is_generic_type(type_):
        return None

    return get_args(type_)


class ClassInfo:
    """Information about a class.

    This class provides information about a class, such as its name, module,
    methods, properties, and type hints.
    """

    def __init__(self, cls: Type):
        """Initialize class information.

        Args:
            cls: The class to get information about
        """
        self.cls = cls
        self.name = cls.__name__
        self.module = cls.__module__
        self.qualname = f"{self.module}.{self.name}" if self.module else self.name
        self.doc = cls.__doc__ or ""

        # Get type hints
        try:
            self.type_hints = get_type_hints(cls)
        except (TypeError, ValueError):
            self.type_hints = {}

        # Get methods
        self.methods = self._get_methods()

        # Get properties
        self.properties = self._get_properties()

        # Check if it's a data class
        self.is_dataclass = is_dataclass(cls)

    def _get_methods(self) -> Dict[str, Callable]:
        """Get the methods of the class.

        Returns:
            A dictionary of method names to method objects
        """
        methods = {}

        for name, value in inspect.getmembers(self.cls):
            if (
                name.startswith("_")
                or not callable(value)
                or isinstance(value, property)
            ):
                continue

            methods[name] = value

        return methods

    def _get_properties(self) -> Dict[str, property]:
        """Get the properties of the class.

        Returns:
            A dictionary of property names to property objects
        """
        properties = {}

        for name, value in inspect.getmembers(self.cls):
            if name.startswith("_") or not isinstance(value, property):
                continue

            properties[name] = value

        return properties

    def get_method_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a method.

        Args:
            name: The name of the method

        Returns:
            Information about the method, or None if the method does not exist
        """
        method = self.methods.get(name)
        if not method:
            return None

        # Get method signature
        try:
            signature = inspect.signature(method)
        except (TypeError, ValueError):
            signature = None

        # Get method doc
        doc = method.__doc__ or ""

        # Get method type hints
        try:
            type_hints = get_type_hints(method)
        except (TypeError, ValueError):
            type_hints = {}

        return {
            "name": name,
            "signature": signature,
            "doc": doc,
            "type_hints": type_hints,
        }

    def get_property_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a property.

        Args:
            name: The name of the property

        Returns:
            Information about the property, or None if the property does not exist
        """
        prop = self.properties.get(name)
        if not prop:
            return None

        # Get property doc
        doc = prop.__doc__ or ""

        # Get property type hint
        type_hint = self.type_hints.get(name)

        return {
            "name": name,
            "doc": doc,
            "type_hint": type_hint,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert the class information to a dictionary.

        Returns:
            A dictionary representation of the class information
        """
        return {
            "name": self.name,
            "module": self.module,
            "qualname": self.qualname,
            "doc": self.doc,
            "is_dataclass": self.is_dataclass,
            "methods": list(self.methods.keys()),
            "properties": list(self.properties.keys()),
        }


def get_class_info(cls: Type) -> ClassInfo:
    """Get information about a class.

    Args:
        cls: The class to get information about

    Returns:
        Information about the class
    """
    return ClassInfo(cls)


def get_module_classes(module: types.ModuleType) -> Dict[str, Type]:
    """Get the classes defined in a module.

    Args:
        module: The module to get classes from

    Returns:
        A dictionary of class names to class objects
    """
    classes = {}

    for name, value in inspect.getmembers(module):
        if (
            name.startswith("_")
            or not isinstance(value, type)
            or value.__module__ != module.__name__
        ):
            continue

        classes[name] = value

    return classes
