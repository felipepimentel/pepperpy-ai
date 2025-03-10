"""Public interfaces for PepperPy Types module.

This module provides a stable public interface for the types functionality.
It exposes the core type definitions and utilities that are considered part
of the public API.
"""

from pepperpy.types.core import (
    ClassInfo,
    DataType,
    JsonArray,
    JsonObject,
    JsonPrimitive,
    JsonValue,
    get_class_info,
    get_data_type,
    get_dict_types,
    get_generic_args,
    get_generic_origin,
    get_list_type,
    get_module_classes,
    get_optional_type,
    get_union_types,
    is_dict_type,
    is_generic_type,
    is_list_type,
    is_optional_type,
    is_union_type,
)

# Re-export everything
__all__ = [
    # Classes
    "ClassInfo",
    "DataType",
    # Type aliases
    "JsonArray",
    "JsonObject",
    "JsonPrimitive",
    "JsonValue",
    # Type checking functions
    "is_optional_type",
    "is_list_type",
    "is_dict_type",
    "is_union_type",
    "is_generic_type",
    # Type extraction functions
    "get_optional_type",
    "get_list_type",
    "get_dict_types",
    "get_union_types",
    "get_generic_origin",
    "get_generic_args",
    # Utility functions
    "get_data_type",
    "get_class_info",
    "get_module_classes",
]
