"""Template renderer for workflow inputs and outputs.

This module provides functionality to render Jinja2 templates for workflow
input and output mappings, supporting variable substitution and expressions.
"""

import re
from datetime import datetime
from typing import Any, Dict, Optional, Union

import jinja2
import structlog

from pepperpy.core.errors import TemplateError

log = structlog.get_logger("pepperpy.hub.template")


class TemplateRenderer:
    """Renderer for workflow templates."""

    def __init__(self):
        """Initialize the template renderer."""
        self.env = jinja2.Environment(
            autoescape=False,
            undefined=jinja2.StrictUndefined,
        )
        self._add_custom_filters()
        self._add_custom_functions()

    def _add_custom_filters(self) -> None:
        """Add custom filters to the Jinja2 environment."""
        self.env.filters.update(
            {
                "to_json": self._to_json,
                "from_json": self._from_json,
                "datetime": self._format_datetime,
            }
        )

    def _add_custom_functions(self) -> None:
        """Add custom functions to the Jinja2 environment."""
        self.env.globals.update(
            {
                "now": datetime.now,
                "utcnow": datetime.utcnow,
                "env": self._get_env,
            }
        )

    def render(
        self,
        template_str: str,
        context: Dict[str, Any],
        strict: bool = True,
    ) -> Any:
        """Render a template string with the given context.

        Args:
        ----
            template_str: Template string to render
            context: Context variables for rendering
            strict: Whether to raise errors for undefined variables

        Returns:
        -------
            Rendered result

        Raises:
        ------
            TemplateError: If template rendering fails

        """
        try:
            # Handle special cases
            if not template_str:
                return None
            if not isinstance(template_str, str):
                return template_str
            if not self._contains_template_syntax(template_str):
                return template_str

            # Create template with optional strict mode
            if not strict:
                env = jinja2.Environment(
                    autoescape=False,
                    undefined=jinja2.Undefined,
                )
            else:
                env = self.env

            # Render template
            template = env.from_string(template_str)
            result = template.render(**context)

            # Try to evaluate as Python literal
            try:
                import ast

                return ast.literal_eval(result)
            except (ValueError, SyntaxError):
                return result

        except Exception as e:
            log.error(
                "Template rendering failed",
                template=template_str,
                error=str(e),
            )
            raise TemplateError(f"Failed to render template: {e}")

    def render_mapping(
        self,
        mapping: Dict[str, Any],
        context: Dict[str, Any],
        strict: bool = True,
    ) -> Dict[str, Any]:
        """Render a mapping of templates with the given context.

        Args:
        ----
            mapping: Mapping of template strings
            context: Context variables for rendering
            strict: Whether to raise errors for undefined variables

        Returns:
        -------
            Mapping of rendered results

        Raises:
        ------
            TemplateError: If template rendering fails

        """
        try:
            result = {}
            for key, value in mapping.items():
                if isinstance(value, str):
                    result[key] = self.render(value, context, strict)
                elif isinstance(value, dict):
                    result[key] = self.render_mapping(value, context, strict)
                elif isinstance(value, list):
                    result[key] = [
                        self.render(item, context, strict)
                        if isinstance(item, str)
                        else item
                        for item in value
                    ]
                else:
                    result[key] = value
            return result

        except Exception as e:
            log.error(
                "Mapping rendering failed",
                mapping=mapping,
                error=str(e),
            )
            raise TemplateError(f"Failed to render mapping: {e}")

    def _contains_template_syntax(self, value: str) -> bool:
        """Check if a string contains Jinja2 template syntax.

        Args:
        ----
            value: String to check

        Returns:
        -------
            True if string contains template syntax

        """
        return bool(
            re.search(r"{[{%].*[}%]}", value)
            or re.search(r"\{\{.*\}\}", value)
            or re.search(r"\{%.*%\}", value)
        )

    def _to_json(self, value: Any) -> str:
        """Convert a value to JSON string.

        Args:
        ----
            value: Value to convert

        Returns:
        -------
            JSON string representation

        """
        import json

        return json.dumps(value)

    def _from_json(self, value: str) -> Any:
        """Parse a JSON string.

        Args:
        ----
            value: JSON string to parse

        Returns:
        -------
            Parsed value

        """
        import json

        return json.loads(value)

    def _format_datetime(
        self, value: Union[datetime, str], format: str = "%Y-%m-%d %H:%M:%S"
    ) -> str:
        """Format a datetime value.

        Args:
        ----
            value: Datetime value to format
            format: Format string

        Returns:
        -------
            Formatted datetime string

        """
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        return value.strftime(format)

    def _get_env(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get an environment variable.

        Args:
        ----
            name: Name of the environment variable
            default: Default value if not found

        Returns:
        -------
            Environment variable value or default

        """
        import os

        return os.getenv(name, default)
