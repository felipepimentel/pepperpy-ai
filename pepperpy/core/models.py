"""Base models and type definitions for the Pepperpy framework.

This module provides core model definitions used throughout the framework.
It includes base models, configuration, and type utilities.

Status: Stable
"""

from __future__ import annotations

import json
from typing import Any, ClassVar

from pepperpy.core.import_utils import import_optional_dependency

# Import pydantic safely
pydantic = import_optional_dependency("pydantic", "pydantic>=2.0.0")
if pydantic:
    BaseModel = pydantic.BaseModel
    ConfigDict = pydantic.ConfigDict
    Field = pydantic.Field
else:

    class BaseModel:
        """Base model when pydantic is not available.

        This class provides a fallback implementation when pydantic is not available.
        It includes basic model functionality like validation, serialization, and configuration.
        """

        model_config: ClassVar[dict[str, Any]] = {
            "frozen": True,
            "arbitrary_types_allowed": True,
            "validate_assignment": True,
            "populate_by_name": True,
            "str_strip_whitespace": True,
            "validate_default": True,
            "extra": "forbid",
            "use_enum_values": True,
        }

        def __init__(self, **data: Any) -> None:
            """Initialize the model with data."""
            self._validate_data(data)
            for key, value in data.items():
                if not key.startswith("_"):
                    setattr(self, key, value)

        def _validate_data(self, data: dict[str, Any]) -> None:
            """Validate input data.

            Args:
                data: Data to validate

            Raises:
                ValueError: If validation fails
            """
            # Basic validation - override in subclasses for more
            for key, value in data.items():
                if key.startswith("_"):
                    raise ValueError(f"Private field not allowed: {key}")

        @classmethod
        def model_validate(cls, obj: Any) -> Any:
            """Validate and create a model instance.

            Args:
                obj: Object to validate and convert to model

            Returns:
                Model instance
            """
            if isinstance(obj, dict):
                return cls(**obj)
            elif isinstance(obj, cls):
                return obj
            else:
                return cls(**obj.__dict__)

        def model_dump(self, exclude_none: bool = False) -> dict[str, Any]:
            """Convert model to dictionary.

            Args:
                exclude_none: Whether to exclude None values

            Returns:
                Dictionary representation of model
            """
            data = {}
            for key, value in self.__dict__.items():
                if not key.startswith("_"):
                    if not exclude_none or value is not None:
                        if isinstance(value, BaseModel):
                            data[key] = value.model_dump(exclude_none=exclude_none)
                        elif isinstance(value, (list, tuple)):
                            data[key] = [
                                v.model_dump(exclude_none=exclude_none)
                                if isinstance(v, BaseModel)
                                else v
                                for v in value
                            ]
                        elif isinstance(value, dict):
                            data[key] = {
                                k: v.model_dump(exclude_none=exclude_none)
                                if isinstance(v, BaseModel)
                                else v
                                for k, v in value.items()
                            }
                        else:
                            data[key] = value
            return data

        def model_dump_json(self, **kwargs: Any) -> str:
            """Convert model to JSON string.

            Args:
                **kwargs: Additional arguments passed to json.dumps

            Returns:
                JSON string representation of model
            """
            return json.dumps(self.model_dump(**kwargs), **kwargs)

    def Field(*args: Any, **kwargs: Any) -> Any:
        """Field stub when pydantic is not available."""
        return lambda x: x

    ConfigDict = dict[str, Any]  # type: ignore


__all__ = [
    "BaseModel",
    "ConfigDict",
    "Field",
]
