"""Common types for security modules."""

from typing import List

from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """Result of artifact validation."""

    is_valid: bool = Field(default=False, description="Whether validation passed")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
