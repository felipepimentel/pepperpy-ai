"""Template module."""

from dataclasses import dataclass
from typing import Any

from ..types import JsonDict


@dataclass
class TemplateContext:
    """Template context."""

    variables: dict[str, Any]
    metadata: JsonDict | None = None

    def to_dict(self) -> JsonDict:
        """Convert context to dictionary."""
        return {
            "variables": self.variables,
            "metadata": self.metadata or {},
        }


@dataclass
class Template:
    """Template definition."""

    name: str
    content: str
    description: str | None = None
    metadata: JsonDict | None = None

    def to_dict(self) -> JsonDict:
        """Convert template to dictionary."""
        return {
            "name": self.name,
            "content": self.content,
            "description": self.description or "",
            "metadata": self.metadata or {},
        }

    def render(self, context: TemplateContext) -> str:
        """Render template with context.

        Args:
            context: Template context.

        Returns:
            Rendered template.
        """
        result = self.content
        for key, value in context.variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result
