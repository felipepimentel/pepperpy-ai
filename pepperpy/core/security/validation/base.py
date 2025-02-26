"""Base validation module.

This module provides the foundation for schema validation in Pepperpy,
including the base schema class and common validation utilities.
"""

import builtins
from datetime import datetime
from typing import Any, ClassVar, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T", bound="BaseSchema")


class BaseSchema(BaseModel):
    """Base schema for all models.

    This class provides common fields and functionality for all schema models:
    - Creation and update timestamps
    - Version tracking
    - JSON encoding
    - Validation hooks
    """

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")

    class Config:
        """Pydantic configuration."""

        json_encoders: ClassVar[dict[type[Any], Any]] = {
            datetime: lambda v: v.isoformat()
        }
        validate_assignment = True
        frozen = True

    @field_validator("updated_at")
    @classmethod
    def update_timestamp(cls, v: datetime) -> datetime:
        """Update timestamp on save."""
        return datetime.now()

    def dict(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Convert model to dictionary.

        This override ensures the updated_at timestamp is current.
        """
        # Update timestamp before conversion
        object.__setattr__(self, "updated_at", datetime.now())
        return super().dict(*args, **kwargs)

    @classmethod
    def validate_json(cls: type[T], json_data: builtins.dict[str, Any]) -> T:
        """Validate and create instance from JSON data.

        Args:
            json_data: JSON data to validate

        Returns:
            Validated instance

        Raises:
            ValidationError: If validation fails
        """
        return cls.model_validate(json_data)

    @classmethod
    def get_json_schema(cls) -> builtins.dict[str, Any]:
        """Get JSON schema for the model.

        Returns:
            JSON schema
        """
        return cls.model_json_schema()
