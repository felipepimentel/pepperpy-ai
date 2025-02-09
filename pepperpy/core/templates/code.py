"""Code template system.

This module provides templates for generating code files,
supporting multiple languages and code generation patterns.
"""

from pathlib import Path
from typing import Any

from jinja2 import Environment, StrictUndefined, select_autoescape

from .base import Template, TemplateContext, TemplateError, TemplateMetadata


class CodeTemplate(Template[str, dict[str, Any], str]):
    """Template for code generation.

    This template type handles code file generation with support for
    multiple languages and code patterns.
    """

    def __init__(
        self,
        metadata: TemplateMetadata,
        language: str = "python",
        style_guide: dict[str, Any] | None = None,
    ) -> None:
        """Initialize code template.

        Args:
            metadata: Template metadata
            language: Programming language
            style_guide: Optional style guide configuration
        """
        super().__init__(metadata)
        self._language = language.lower()
        self._style_guide = style_guide or {}
        self._env = Environment(
            undefined=StrictUndefined,
            autoescape=select_autoescape(
                enabled_extensions=("html", "xml", "jinja2"),
                default_for_string=True,
            ),
        )

    async def load(self) -> None:
        """Load the template.

        Raises:
            TemplateError: If loading fails
        """
        try:
            # Template content would typically be loaded from a file
            # For now, we'll use a simple default template
            if self._language == "python":
                self._template = '''"""{{ description }}"""

{% for import_stmt in imports %}
{{ import_stmt }}
{% endfor %}

{% if class_name %}
class {{ class_name }}:
    """{{ class_description }}"""

    def __init__(self{% for arg in init_args %}, {{ arg }}{% endfor %}):
        """Initialize {{ class_name }}.

        Args:
            {% for arg, desc in arg_descriptions.items() %}
            {{ arg }}: {{ desc }}
            {% endfor %}
        """
        {% for attr in attributes %}
        self.{{ attr }} = {{ attr }}
        {% endfor %}

    {% for method in methods %}
    def {{ method.name }}(self{% for arg in method.args %}, {{ arg }}{% endfor %}):
        """{{ method.description }}"""
        {{ method.body }}
    {% endfor %}
{% else %}
{% for function in functions %}
def {{ function.name }}(
    {%- for arg in function.args -%}
    {{ arg }}{% if not loop.last %},{% endif %}
    {%- endfor -%}
):
    """{{ function.description }}"""
    {{ function.body }}
{% endfor %}
{% endif %}
'''
            else:
                raise ValueError(f"Unsupported language: {self._language}")
        except Exception as e:
            raise TemplateError(
                f"Failed to load template: {e}",
                template_id=self.metadata.id,
            ) from e

    async def render(self, context: TemplateContext[dict[str, Any]]) -> str:
        """Render the template with context.

        Args:
            context: Template context with code generation data

        Returns:
            Generated code

        Raises:
            TemplateError: If rendering fails
        """
        if not self.is_loaded:
            await self.load()

        try:
            # Render template with context
            template = self._env.from_string(self._template or "")
            rendered = template.render(**context.data)

            # Apply style guide if provided
            if self._style_guide:
                rendered = self._apply_style_guide(rendered)

            return rendered
        except Exception as e:
            raise TemplateError(
                f"Failed to render template: {e}",
                template_id=self.metadata.id,
            ) from e

    async def validate(self, context: TemplateContext[dict[str, Any]]) -> bool:
        """Validate template with context.

        Args:
            context: Template context with code generation data

        Returns:
            True if valid, False otherwise

        Raises:
            TemplateError: If validation fails
        """
        try:
            # Validate required fields
            required_fields = {
                "python": ["imports", "description"],
            }.get(self._language, [])

            for field in required_fields:
                if field not in context.data:
                    raise ValueError(f"Missing required field: {field}")

            # Validate code structure
            if "class_name" in context.data:
                if "class_description" not in context.data:
                    raise ValueError("Missing class description")
                if "methods" in context.data:
                    for method in context.data["methods"]:
                        if "name" not in method or "description" not in method:
                            raise ValueError("Invalid method specification")

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
                f.write(self._template or "")
        except Exception as e:
            raise TemplateError(
                f"Failed to save template: {e}",
                template_id=self.metadata.id,
            ) from e

    def _apply_style_guide(self, code: str) -> str:
        """Apply style guide to generated code.

        Args:
            code: Code to format

        Returns:
            Formatted code
        """
        try:
            if self._language == "python":
                import black

                mode = black.Mode(
                    line_length=self._style_guide.get("line_length", 88),
                    string_normalization=True,
                    is_pyi=False,
                )
                return black.format_str(code, mode=mode)
            return code
        except Exception:
            # If formatting fails, return original code
            return code
