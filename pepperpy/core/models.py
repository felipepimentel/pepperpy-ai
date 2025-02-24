"""Base models and type definitions for the Pepperpy framework.

This module provides core model definitions used throughout the framework.
It includes base models, configuration, and type utilities.

Status: Stable
"""

from __future__ import annotations

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
        """Base model when pydantic is not available."""

        model_config: ClassVar[dict[str, Any]] = {
            "frozen": True,
            "arbitrary_types_allowed": True,
            "validate_assignment": True,
            "populate_by_name": True,
            "str_strip_whitespace": True,
            "validate_default": True,
        }

        def __init__(self, **data: Any) -> None:
            for key, value in data.items():
                setattr(self, key, value)

        @classmethod
        def model_validate(cls, obj: Any) -> Any:
            return cls(**obj)

    def Field(*args: Any, **kwargs: Any) -> Any:
        """Field stub when pydantic is not available."""
        return lambda x: x

    ConfigDict = dict[str, Any]  # type: ignore


__all__ = [
    "BaseModel",
    "ConfigDict",
    "Field",
]
