"""Utilitários para manipulação de arquivos JSON (DEPRECATED).

Implementa funções auxiliares para manipulação e formatação de arquivos JSON.

This module is deprecated and will be removed in version 1.0.0.
Please use 'pepperpy.core.utils.serialization.JsonUtils' instead.
"""

import json
import warnings
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.utils.dates import DateUtils

# Show deprecation warning
warnings.warn(
    "The 'pepperpy.core.utils.json' module is deprecated and will be removed in version 1.0.0. "
    "Please use 'pepperpy.core.utils.serialization.JsonUtils' instead.",
    DeprecationWarning,
    stacklevel=2,
)


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
                default=JsonUtils.json_serialize,
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
            data, indent=indent, default=JsonUtils.json_serialize, ensure_ascii=False
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
    def json_serialize(obj: Any) -> Any:
        """JSON serializer for objects not serializable by default json code.

        Args:
            obj: Object to serialize

        Returns:
            JSON serializable object
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

            if (
                "minimum" in schema_value
                and isinstance(value, (int, float, Decimal))
                and value < schema_value["minimum"]
            ):
                errors.append(f"{path}: value must be >= {schema_value['minimum']}")

            if (
                "maximum" in schema_value
                and isinstance(value, (int, float, Decimal))
                and value > schema_value["maximum"]
            ):
                errors.append(f"{path}: value must be <= {schema_value['maximum']}")

        def validate_object(
            obj: Dict[str, Any], schema_obj: Dict[str, Any], path: str = ""
        ) -> None:
            for key, schema_value in schema_obj.get("properties", {}).items():
                value = obj.get(key)
                current_path = f"{path}.{key}" if path else key

                if value is not None:
                    validate_value(value, schema_value, current_path)

                    if schema_value.get("type") == "object":
                        validate_object(value, schema_value, current_path)
                    elif (
                        schema_value.get("type") == "array" and "items" in schema_value
                    ):
                        for i, item in enumerate(value):
                            item_path = f"{current_path}[{i}]"
                            validate_value(item, schema_value["items"], item_path)

            required = schema_obj.get("required", [])
            for key in required:
                if key not in obj:
                    current_path = f"{path}.{key}" if path else key
                    errors.append(f"{current_path}: required field is missing")

        validate_object(data, schema)
        return errors
