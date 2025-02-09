"""Prompt template module for managing AI prompts.

This module provides the base prompt template interface and factory function
for creating prompt templates. Templates are used to generate prompts for
language models with dynamic content.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Protocol, Type, TypeVar

from pepperpy.core.errors import ValidationError


class PromptTemplate(Protocol):
    """Protocol defining the prompt template interface."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the template."""
        ...

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the template."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up template resources."""
        pass

    @abstractmethod
    async def render(self, variables: dict[str, Any]) -> str:
        """Render the template with variables."""
        pass


T = TypeVar("T", bound=PromptTemplate)

# Registry of template types
_template_types: dict[str, Type[PromptTemplate]] = {}


def register_template(template_type: str) -> Callable[[Type[T]], Type[T]]:
    """Decorator to register a template type.

    Args:
        template_type: Unique identifier for the template type

    Returns:
        Decorator function that registers the template class
    """

    def decorator(cls: Type[T]) -> Type[T]:
        if template_type in _template_types:
            raise ValueError(f"Template type already registered: {template_type}")
        _template_types[template_type] = cls  # type: ignore
        return cls

    return decorator


class BaseTemplate(ABC):
    """Base class for prompt template implementations."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the template."""
        self.config = config

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the template."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up template resources."""
        pass

    @abstractmethod
    async def render(self, variables: dict[str, Any]) -> str:
        """Render the template with variables."""
        pass


async def create_prompt_template(config: dict[str, Any]) -> PromptTemplate:
    """Create a prompt template instance."""
    if "type" not in config:
        raise ValidationError(
            "Missing required field: type",
            details={"field": "type"},
        )

    template_type = config["type"]
    if template_type not in _template_types:
        raise ValidationError(
            f"Unknown template type: {template_type}",
            details={"type": template_type},
        )

    template_class = _template_types[template_type]
    return template_class(config)
