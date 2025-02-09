"""Base template system.

This module provides the core interfaces and base classes for the
template system, including template loading, rendering, and validation.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, ClassVar, Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

T = TypeVar("T")  # Template type
C = TypeVar("C")  # Context type
R = TypeVar("R")  # Result type


class TemplateError(Exception):
    """Base class for template-related errors."""

    def __init__(self, message: str, template_id: UUID | None = None) -> None:
        """Initialize template error.

        Args:
            message: Error message
            template_id: Optional template ID where error occurred
        """
        super().__init__(message)
        self.template_id = template_id


class TemplateMetadata(BaseModel):
    """Metadata for templates.

    Attributes:
        id: Template identifier
        name: Template name
        version: Template version
        description: Template description
        created_at: Creation timestamp
        updated_at: Last update timestamp
        metadata: Additional metadata
    """

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    description: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model configuration."""

        frozen = True
        json_encoders: ClassVar[dict[type, Any]] = {
            datetime: lambda v: v.isoformat(),
            UUID: str,
        }

    @validator("metadata")
    def validate_metadata(self, v: dict[str, Any]) -> dict[str, Any]:
        """Validate metadata dictionary."""
        return dict(v)


class TemplateContext(BaseModel, Generic[C]):
    """Context for template operations.

    Attributes:
        id: Context identifier
        template_id: Associated template ID
        data: Context data
        metadata: Additional metadata
        created_at: Creation timestamp
    """

    id: UUID = Field(default_factory=uuid4)
    template_id: UUID
    data: C
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic model configuration."""

        frozen = True
        json_encoders: ClassVar[dict[type, Any]] = {
            datetime: lambda v: v.isoformat(),
            UUID: str,
        }

    @validator("metadata")
    def validate_metadata(self, v: dict[str, Any]) -> dict[str, Any]:
        """Validate metadata dictionary."""
        return dict(v)


class Template(ABC, Generic[T, C, R]):
    """Base class for templates.

    This class defines the core interface that all templates must implement,
    providing methods for template loading, rendering, and validation.
    """

    def __init__(self, metadata: TemplateMetadata) -> None:
        """Initialize template.

        Args:
            metadata: Template metadata
        """
        self._metadata = metadata
        self._template: T | None = None

    @property
    def metadata(self) -> TemplateMetadata:
        """Get template metadata."""
        return self._metadata

    @property
    def is_loaded(self) -> bool:
        """Check if template is loaded."""
        return self._template is not None

    @abstractmethod
    async def load(self) -> None:
        """Load the template.

        This method should load and parse the template content.

        Raises:
            TemplateError: If loading fails
        """
        pass

    @abstractmethod
    async def render(self, context: TemplateContext[C]) -> R:
        """Render the template with context.

        Args:
            context: Template context

        Returns:
            Rendered result

        Raises:
            TemplateError: If rendering fails
        """
        pass

    @abstractmethod
    async def validate(self, context: TemplateContext[C]) -> bool:
        """Validate template with context.

        Args:
            context: Template context

        Returns:
            True if valid, False otherwise

        Raises:
            TemplateError: If validation fails
        """
        pass

    @abstractmethod
    async def save(self, path: str) -> None:
        """Save template to disk.

        Args:
            path: Path to save template to

        Raises:
            TemplateError: If saving fails
        """
        pass
