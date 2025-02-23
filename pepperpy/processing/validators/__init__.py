"""Validators module for the processing system.

This module provides base classes for data validators:
- BaseValidator: Abstract base class for all validators
- DataValidator: Generic data validator implementation
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar

from pepperpy.core.base import Lifecycle
from pepperpy.core.errors import ValidationError
from pepperpy.core.models import BaseModel, Field
from pepperpy.core.types import ComponentState
from pepperpy.monitoring import logger

# Type variables
T = TypeVar("T")
ValidatorType = TypeVar("ValidatorType", bound="BaseValidator")


class ValidatorConfig(BaseModel):
    """Base configuration for validators.

    Attributes:
        name: Validator name
        enabled: Whether validator is enabled
        metadata: Additional configuration metadata
    """

    name: str = Field(description="Validator name")
    enabled: bool = Field(default=True, description="Whether validator is enabled")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class BaseValidator(Lifecycle, Generic[T], ABC):
    """Base class for all validators."""

    def __init__(self, config: ValidatorConfig | None = None) -> None:
        """Initialize validator.

        Args:
            config: Optional validator configuration
        """
        super().__init__()
        self.config = config or ValidatorConfig(name=self.__class__.__name__)
        self._state = ComponentState.CREATED

    async def initialize(self) -> None:
        """Initialize validator.

        This method should be called before using the validator.
        """
        try:
            self._state = ComponentState.READY
            logger.info(f"Validator initialized: {self.config.name}")
        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize validator: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up validator resources."""
        try:
            self._state = ComponentState.CLEANED
            logger.info(f"Validator cleaned up: {self.config.name}")
        except Exception as e:
            logger.error(f"Failed to cleanup validator: {e}")
            raise

    @abstractmethod
    async def validate(self, data: T) -> None:
        """Validate data.

        Args:
            data: Data to validate

        Raises:
            ValidationError: If validation fails
        """
        raise NotImplementedError


class DataValidatorConfig(BaseModel):
    """Configuration for data validator."""

    schema: dict[str, Any] | None = Field(
        default=None,
        description="JSON Schema for validation",
    )
    required_fields: list[str] | None = Field(
        default=None,
        description="List of required fields",
    )
    field_types: dict[str, type] | None = Field(
        default=None,
        description="Field type mapping",
    )


class DataValidator(BaseValidator[T]):
    """Generic data validator implementation."""

    def __init__(self, config: DataValidatorConfig | None = None) -> None:
        """Initialize validator.

        Args:
            config: Optional validator configuration
        """
        super().__init__()
        self.config = config or DataValidatorConfig()

    async def validate(self, data: T) -> None:
        """Validate data.

        Args:
            data: Data to validate

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Check required fields
            if self.config.required_fields:
                if not isinstance(data, dict):
                    raise ValidationError(
                        "Data must be a dictionary",
                        details={"type": type(data).__name__},
                    )
                for field in self.config.required_fields:
                    if field not in data:
                        raise ValidationError(
                            f"Missing required field: {field}",
                            details={"field": field},
                        )

            # Check field types
            if self.config.field_types:
                if not isinstance(data, dict):
                    raise ValidationError(
                        "Data must be a dictionary",
                        details={"type": type(data).__name__},
                    )
                for field, expected_type in self.config.field_types.items():
                    if field in data and not isinstance(data[field], expected_type):
                        raise ValidationError(
                            f"Invalid type for field '{field}': "
                            f"expected {expected_type.__name__}, "
                            f"got {type(data[field]).__name__}",
                            details={
                                "field": field,
                                "expected_type": expected_type.__name__,
                                "actual_type": type(data[field]).__name__,
                            },
                        )

            # Validate against schema
            if self.config.schema:
                from jsonschema import validate as validate_schema

                try:
                    validate_schema(instance=data, schema=self.config.schema)
                except Exception as e:
                    raise ValidationError(
                        "JSON Schema validation failed",
                        details={"error": str(e)},
                    )

        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(
                "Validation failed",
                details={"error": str(e)},
            )


__all__ = [
    "BaseValidator",
    "DataValidator",
    "ValidatorConfig",
]
