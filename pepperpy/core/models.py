"""Base models for the Pepperpy framework.

This module provides base model functionality with validation.
"""

from typing import Any, ClassVar, Protocol, TypeVar

try:
    from pydantic import BaseModel as PydanticBaseModel  # type: ignore
    from pydantic import Field  # type: ignore
except ImportError:
    PydanticBaseModel = object

    def Field(*args: Any, **kwargs: Any) -> Any:  # type: ignore
        return lambda x: x


class BaseModelProtocol(Protocol):
    """Protocol defining the interface for base models."""

    def model_validate(self, obj: Any) -> Any: ...
    def model_dump(self, exclude_none: bool = False) -> dict[str, Any]: ...
    def model_dump_json(self, **kwargs: Any) -> str: ...


class PepperpyBaseModel:
    """Base model when pydantic is not available.

    This class provides a fallback implementation when pydantic is not available.
    It includes basic model functionality like validation, serialization, and configuration.
    """

    model_config: ClassVar[dict[str, Any]] = {
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
        "populate_by_name": True,
        "str_strip_whitespace": True,
        "validate_default": True,
    }

    def __init__(self, **data: Any) -> None:
        """Initialize the model.

        Args:
            **data: Model data
        """
        self._validate_data(data)
        for key, value in data.items():
            setattr(self, key, value)

    def _validate_data(self, data: dict[str, Any]) -> None:
        """Validate model data.

        Args:
            data: Data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Basic validation in fallback implementation
        for key, value in data.items():
            if not hasattr(self.__class__, key):
                raise ValueError(f"Invalid field: {key}")

    @classmethod
    def model_validate(cls, obj: Any) -> Any:
        """Validate and create model from object.

        Args:
            obj: Object to validate

        Returns:
            Model instance
        """
        if isinstance(obj, dict):
            return cls(**obj)
        elif isinstance(obj, cls):
            return obj
        else:
            raise ValueError(f"Cannot validate object of type: {type(obj)}")

    def model_dump(self, exclude_none: bool = False) -> dict[str, Any]:
        """Convert model to dictionary.

        Args:
            exclude_none: Whether to exclude None values

        Returns:
            Model as dictionary
        """
        data = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                if not exclude_none or value is not None:
                    data[key] = value
        return data

    def model_dump_json(self, **kwargs: Any) -> str:
        """Convert model to JSON string.

        Args:
            **kwargs: JSON serialization options

        Returns:
            Model as JSON string
        """
        import json

        return json.dumps(self.model_dump(**kwargs))


# Use pydantic BaseModel if available, otherwise use fallback
_base_model = (
    PydanticBaseModel if not isinstance(PydanticBaseModel, type) else PydanticBaseModel
)
BaseModel = _base_model


# Type variable for models
ModelT = TypeVar("ModelT", bound=BaseModelProtocol)


__all__ = ["BaseModel", "BaseModelProtocol", "Field", "ModelT"]
