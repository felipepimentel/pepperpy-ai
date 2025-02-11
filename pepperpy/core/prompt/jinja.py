"""Jinja2-based prompt template implementation."""

from typing import Any

from jinja2 import Environment, StrictUndefined, Template, select_autoescape

from pepperpy.core.prompt.template import BaseTemplate, register_template


@register_template("jinja2")
class Jinja2Template(BaseTemplate):
    """Jinja2-based prompt template implementation."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the template.

        Args:
        ----
            config: Template configuration

        """
        super().__init__(config)
        self._env = Environment(
            undefined=StrictUndefined,
            autoescape=select_autoescape(
                enabled_extensions=("html", "xml", "jinja2"),
                default_for_string=True,
            ),
        )
        self._template: Template | None = None
        self._template_str = config.get("template", "")

    async def initialize(self) -> None:
        """Initialize the template."""
        if not self._template_str:
            raise ValueError("Template string not provided")
        self._template = self._env.from_string(self._template_str)

    async def cleanup(self) -> None:
        """Clean up template resources."""
        self._template = None

    async def render(self, variables: dict[str, Any]) -> str:
        """Render the template with variables.

        Args:
        ----
            variables: Variables to use in rendering

        Returns:
        -------
            Rendered template string

        Raises:
        ------
            ValueError: If template is not initialized

        """
        if not self._template:
            raise ValueError("Template not initialized")
        return self._template.render(**variables)
