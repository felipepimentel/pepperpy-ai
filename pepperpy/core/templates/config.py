"""Configuration template system.

This module provides templates for managing configuration files,
supporting multiple formats (JSON, YAML) and validation rules.
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar

import yaml
from pydantic import validator

from .base import Template, TemplateContext, TemplateError, TemplateMetadata


class ConfigTemplate(Template[str, dict[str, Any], dict[str, Any]]):
    """Template for configuration files.

    This template type handles configuration file generation and validation,
    supporting multiple formats and schema validation.
    """

    _supported_formats: ClassVar[dict[str, str]] = {
        "yaml": "yaml",
        "yml": "yaml",
        "json": "json",
    }

    _format_loaders: ClassVar[dict[str, Callable[[str], dict[str, Any]]]] = {
        "yaml": yaml.safe_load,
        "json": json.loads,
    }

    _format_dumpers: ClassVar[dict[str, Callable[[dict[str, Any]], str]]] = {
        "yaml": lambda d: yaml.dump(d, sort_keys=False),
        "json": lambda d: json.dumps(d, indent=2),
    }

    def __init__(
        self,
        metadata: TemplateMetadata,
        schema: dict[str, Any] | None = None,
        format: str = "yaml",
    ) -> None:
        """Initialize config template.

        Args:
            metadata: Template metadata
            schema: Optional JSON schema for validation
            format: Output format (yaml or json)
        """
        super().__init__(metadata)
        self._schema = schema
        self._format = format.lower()
        if self._format not in ("yaml", "json"):
            raise ValueError(f"Unsupported format: {format}")

    async def load(self) -> None:
        """Load the template.

        Raises:
            TemplateError: If loading fails
        """
        try:
            # Template content would typically be loaded from a file
            # For now, we'll use a simple default template
            self._template = """
            # {{description}}
            {% for key, value in data.items() %}
            {{key}}: {{value}}
            {% endfor %}
            """
        except Exception as e:
            raise TemplateError(
                f"Failed to load template: {e}",
                template_id=self.metadata.id,
            ) from e

    async def render(
        self,
        context: TemplateContext[dict[str, Any]],
    ) -> dict[str, Any]:
        """Render the template with context.

        Args:
            context: Template context with configuration data

        Returns:
            Rendered configuration

        Raises:
            TemplateError: If rendering fails
        """
        if not self.is_loaded:
            await self.load()

        try:
            # Render template with context
            from jinja2 import Template

            template = Template(self._template or "")
            rendered = template.render(
                description=self.metadata.description,
                data=context.data,
            )

            # Parse rendered content
            config = self._format_loaders[self._format](rendered)

            # Validate against schema if provided
            if self._schema:
                from jsonschema import validate

                validate(config, self._schema)

            return config
        except Exception as e:
            raise TemplateError(
                f"Failed to render template: {e}",
                template_id=self.metadata.id,
            ) from e

    async def validate(self, context: TemplateContext[dict[str, Any]]) -> bool:
        """Validate template with context.

        Args:
            context: Template context with configuration data

        Returns:
            True if valid, False otherwise

        Raises:
            TemplateError: If validation fails
        """
        try:
            if self._schema:
                from jsonschema import validate

                validate(context.data, self._schema)
            return True
        except Exception as e:
            raise TemplateError(
                f"Validation failed: {e}",
                template_id=self.metadata.id,
            ) from e

    async def save(self, path: str | Path) -> None:
        """Save template to disk.

        Args:
            path: Path to save template to

        Raises:
            TemplateError: If saving fails
        """
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with file_path.open("w") as f:
                if self._format == "yaml":
                    yaml.safe_dump({"template": self._template}, f)
                else:
                    json.dump({"template": self._template}, f, indent=2)
        except Exception as e:
            raise TemplateError(
                f"Failed to save template: {e}",
                template_id=self.metadata.id,
            ) from e

    @validator("id")
    def validate_id(self, v: str) -> str:
        """Validate template ID."""
        if not v:
            raise ValueError("Template ID cannot be empty")
        return v

    @validator("version")
    def validate_version(self, v: str) -> str:
        """Validate template version."""
        if not v:
            raise ValueError("Template version cannot be empty")
        return v

    @validator("name")
    def validate_name(self, v: str) -> str:
        """Validate template name."""
        if not v:
            raise ValueError("Template name cannot be empty")
        return v

    @validator("description")
    def validate_description(self, v: str | None) -> str:
        """Validate template description."""
        if v is None:
            return ""
        return v
