"""Data conversion utilities.

This module provides utility functions for converting data between different formats.
"""

import json
import logging
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel

from pepperpy.core.errors import ConversionError

logger = logging.getLogger(__name__)


class DataFormat:
    """Data format constants."""

    JSON = "json"
    YAML = "yaml"
    DICT = "dict"
    MODEL = "model"
    STRING = "string"


def convert_data(
    data: Any,
    source_format: str,
    target_format: str,
    model_class: Optional[type] = None,
) -> Any:
    """Convert data between formats.

    Args:
        data: Data to convert
        source_format: Source format (json, yaml, dict, model, string)
        target_format: Target format (json, yaml, dict, model, string)
        model_class: Optional Pydantic model class for model conversion

    Returns:
        Any: Converted data

    Raises:
        ConversionError: If conversion fails
    """
    try:
        # First convert to dictionary as intermediate format
        dict_data = _to_dict(data, source_format, model_class)

        # Then convert from dictionary to target format
        return _from_dict(dict_data, target_format, model_class)

    except Exception as e:
        logger.error(
            f"Data conversion failed: {e}",
            extra={
                "source_format": source_format,
                "target_format": target_format,
            },
            exc_info=True,
        )
        raise ConversionError(f"Failed to convert data: {e}") from e


def _to_dict(
    data: Any,
    source_format: str,
    model_class: Optional[type] = None,
) -> Dict[str, Any]:
    """Convert data to dictionary format.

    Args:
        data: Data to convert
        source_format: Source format
        model_class: Optional model class

    Returns:
        Dict[str, Any]: Dictionary data

    Raises:
        ConversionError: If conversion fails
    """
    try:
        if source_format == DataFormat.DICT:
            return data
        elif source_format == DataFormat.JSON:
            return json.loads(data) if isinstance(data, str) else data
        elif source_format == DataFormat.YAML:
            return yaml.safe_load(data) if isinstance(data, str) else data
        elif source_format == DataFormat.MODEL:
            if not isinstance(data, BaseModel):
                raise ConversionError("Data is not a Pydantic model")
            return data.dict()
        elif source_format == DataFormat.STRING:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                try:
                    return yaml.safe_load(data)
                except yaml.YAMLError:
                    raise ConversionError("Failed to parse string as JSON or YAML")
        else:
            raise ConversionError(f"Unsupported source format: {source_format}")

    except Exception as e:
        raise ConversionError(f"Failed to convert to dictionary: {e}") from e


def _from_dict(
    data: Dict[str, Any],
    target_format: str,
    model_class: Optional[type] = None,
) -> Any:
    """Convert dictionary to target format.

    Args:
        data: Dictionary data
        target_format: Target format
        model_class: Optional model class

    Returns:
        Any: Converted data

    Raises:
        ConversionError: If conversion fails
    """
    try:
        if target_format == DataFormat.DICT:
            return data
        elif target_format == DataFormat.JSON:
            return json.dumps(data)
        elif target_format == DataFormat.YAML:
            return yaml.safe_dump(data)
        elif target_format == DataFormat.MODEL:
            if not model_class or not issubclass(model_class, BaseModel):
                raise ConversionError("Invalid model class")
            return model_class(**data)
        elif target_format == DataFormat.STRING:
            return json.dumps(data)
        else:
            raise ConversionError(f"Unsupported target format: {target_format}")

    except Exception as e:
        raise ConversionError(f"Failed to convert from dictionary: {e}") from e
