"""Base models for the Pepperpy framework.

This module provides base model functionality with validation.
"""

from datetime import datetime

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field as PydanticField


class BaseModel(PydanticBaseModel):
    """Base model with common functionality."""

    class Config:
        """Model configuration."""

        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
        }


# Re-export Field for consistency
Field = PydanticField


__all__ = ["BaseModel", "Field"]
