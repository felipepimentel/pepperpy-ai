"""Documentation template system.

This module provides templates for generating documentation files,
supporting multiple formats (Markdown, reStructuredText, HTML, AsciiDoc) and styles.
"""

from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, TypeVar

from jinja2 import Environment, StrictUndefined, select_autoescape
from jinja2 import Template as JinjaTemplate
from pydantic import BaseModel, Field, field_validator

from .base import Template, TemplateContext, TemplateError, TemplateMetadata

# Type variable for template content
T_Content = TypeVar("T_Content")


class DocFormat(str, Enum):
    """Documentation format types."""

    MARKDOWN = "markdown"
    RST = "rst"
    HTML = "html"
    ASCIIDOC = "asciidoc"


class DocExample(BaseModel):
    """Documentation example model."""

    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    language: str = Field(default="python")
    code: str = Field(..., min_length=1)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language identifier."""
        if not v.strip():
            raise ValueError("Language cannot be empty")
        return v.strip()


class DocParameter(BaseModel):
    """Documentation parameter model."""

    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    type: str | None = None
    default: Any | None = None
    required: bool = True


class DocError(BaseModel):
    """Documentation error model."""

    type: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)


class DocAPIItem(BaseModel):
    """Documentation API item model."""

    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    parameters: list[DocParameter] = Field(default_factory=list)
    returns: str | None = None
    raises: list[DocError] = Field(default_factory=list)
    examples: list[DocExample] = Field(default_factory=list)


class DocContext(BaseModel):
    """Documentation context model."""

    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    overview: str = Field(..., min_length=1)
    installation: str = Field(default="pip install pepperpy")
    usage: str = Field(..., min_length=1)
    examples: list[DocExample] = Field(default_factory=list)
    api: list[DocAPIItem] = Field(default_factory=list)
    license: str | None = None

    @field_validator("title", "description", "overview", "usage")
    @classmethod
    def validate_required_text(cls, v: str) -> str:
        """Validate required text fields."""
        if not v.strip():
            raise ValueError("Required text field cannot be empty")
        return v.strip()


class DocTemplate(Template[str, dict[str, Any], str]):
    """Template for documentation generation.

    This template type handles documentation file generation with support
    for multiple formats and documentation styles.
    """

    # Class-level cache for compiled templates
    _template_cache: ClassVar[dict[str, JinjaTemplate]] = {}

    # Default templates for each format
    _default_templates: ClassVar[dict[str, str]] = {
        DocFormat.MARKDOWN: """# {{ title }}

{{ description }}

## Overview

{{ overview }}

## Installation

```bash
{{ installation }}
```

## Usage

{{ usage }}

{% if examples %}
## Examples

{% for example in examples %}
### {{ example.title }}

{{ example.description }}

```{{ example.language }}
{{ example.code }}
```
{% endfor %}
{% endif %}

{% if api %}
## API Reference

{% for item in api %}
### {{ item.name }}

{{ item.description }}

{% if item.parameters %}
Parameters:
{% for param in item.parameters %}
- `{{ param.name }}`: {{ param.description }}
{% endfor %}
{% endif %}

{% if item.returns %}
Returns:
{{ item.returns }}
{% endif %}

{% if item.raises %}
Raises:
{% for error in item.raises %}
- `{{ error.type }}`: {{ error.description }}
{% endfor %}
{% endif %}
{% endfor %}
{% endif %}

{% if license %}
## License

{{ license }}
{% endif %}
""",
        DocFormat.RST: """{{ title }}
{{ "=" * title|length }}

{{ description }}

Overview
--------

{{ overview }}

Installation
------------

.. code-block:: bash

    {{ installation }}

Usage
-----

{{ usage }}

{% if examples %}
Examples
--------

{% for example in examples %}
{{ example.title }}
{{ "~" * example.title|length }}

{{ example.description }}

.. code-block:: {{ example.language }}

    {{ example.code }}
{% endfor %}
{% endif %}

{% if api %}
API Reference
------------

{% for item in api %}
{{ item.name }}
{{ "~" * item.name|length }}

{{ item.description }}

{% if item.parameters %}
:Parameters:
{% for param in item.parameters %}
    {{ param.name }}: {{ param.description }}
{% endfor %}
{% endif %}

{% if item.returns %}
:Returns:
    {{ item.returns }}
{% endif %}

{% if item.raises %}
:Raises:
{% for error in item.raises %}
    {{ error.type }}: {{ error.description }}
{% endfor %}
{% endif %}
{% endfor %}
{% endif %}

{% if license %}
License
-------

{{ license }}
{% endif %}
""",
        DocFormat.HTML: """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: system-ui, -apple-system, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }
        pre {
            background: #f6f8fa;
            padding: 1rem;
            border-radius: 6px;
            overflow-x: auto;
        }
        code {
            font-family: ui-monospace, monospace;
        }
        .parameter {
            margin-left: 1rem;
        }
        .returns, .raises {
            margin-top: 0.5rem;
        }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>
    <p>{{ description }}</p>
    <h2>Overview</h2>
    <p>{{ overview }}</p>
    <h2>Installation</h2>
    <pre><code>{{ installation }}</code></pre>
    <h2>Usage</h2>
    <pre><code>{{ usage }}</code></pre>
    {% if examples %}
    <h2>Examples</h2>
    {% for example in examples %}
    <div class="example">
        <h3>{{ example.title }}</h3>
        <p>{{ example.description }}</p>
        <pre><code>{{ example.code }}</code></pre>
    </div>
    {% endfor %}
    {% endif %}
    {% if api %}
    <h2>API Reference</h2>
    {% for item in api %}
    <h3>{{ item.name }}</h3>
    <p>{{ item.description }}</p>
    {% if item.parameters %}
    <h4>Parameters</h4>
    <ul>
    {% for param in item.parameters %}
        <li><code>{{ param.name }}</code>: {{ param.description }}</li>
    {% endfor %}
    </ul>
    {% endif %}
    {% if item.returns %}
    <div class="returns">
        <h4>Returns</h4>
        <p>{{ item.returns }}</p>
    </div>
    {% endif %}
    {% if item.raises %}
    <div class="raises">
        <h4>Raises</h4>
        <ul>
        {% for error in item.raises %}
            <li><code>{{ error.type }}</code>: {{ error.description }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}
    {% endfor %}
    {% endif %}
    {% if license %}
    <h2>License</h2>
    <p>{{ license }}</p>
    {% endif %}
</body>
</html>
""",
        DocFormat.ASCIIDOC: """= {{ title }}

{{ description }}

== Overview

{{ overview }}

== Installation

[source,bash]
----
{{ installation }}
----

== Usage

[source,python]
----
{{ usage }}
----

{% if examples %}
== Examples

{% for example in examples %}
=== {{ example.title }}

{{ example.description }}

[source,{{ example.language }}]
----
{{ example.code }}
----
{% endfor %}
{% endif %}

{% if api %}
== API Reference

{% for item in api %}
=== {{ item.name }}

{{ item.description }}

{% if item.parameters %}
.Parameters
{% for param in item.parameters %}
* `{{ param.name }}`: {{ param.description }}
{% endfor %}
{% endif %}

{% if item.returns %}
.Returns
{{ item.returns }}
{% endif %}

{% if item.raises %}
.Raises
{% for error in item.raises %}
* `{{ error.type }}`: {{ error.description }}
{% endfor %}
{% endif %}
{% endfor %}
{% endif %}

{% if license %}
== License

{{ license }}
{% endif %}
""",
    }

    def __init__(
        self,
        metadata: TemplateMetadata,
        format: DocFormat = DocFormat.MARKDOWN,
        style_guide: dict[str, Any] | None = None,
    ) -> None:
        """Initialize docs template.

        Args:
            metadata: Template metadata
            format: Documentation format
            style_guide: Optional style guide configuration
        """
        super().__init__(metadata)
        self._format = format
        self._style_guide = style_guide or {}
        self._env = Environment(
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=select_autoescape(
                enabled_extensions=("html", "xml", "jinja2"),
                default_for_string=True,
            ),
        )
        self._template: str | None = None

    @property
    def format(self) -> DocFormat:
        """Get documentation format."""
        return self._format

    async def load(self) -> None:
        """Load the template.

        Raises:
            TemplateError: If loading fails
        """
        try:
            # Get default template for format
            self._template = self._default_templates.get(
                self._format,
                self._default_templates[DocFormat.MARKDOWN],
            )
        except Exception as e:
            raise TemplateError(
                f"Failed to load template: {e}",
                template_id=self.metadata.id,
            ) from e

    async def render(self, context: TemplateContext[dict[str, Any]]) -> str:
        """Render the template with context.

        Args:
            context: Template context with documentation data

        Returns:
            Generated documentation

        Raises:
            TemplateError: If rendering fails
        """
        if not self.is_loaded:
            await self.load()

        try:
            # Validate context data
            doc_context = DocContext(**context.data)

            # Get or compile template
            cache_key = f"{self._format}:{self.metadata.id}"
            if cache_key not in self._template_cache:
                if not self._template:
                    raise TemplateError(
                        "Template not loaded",
                        template_id=self.metadata.id,
                    )
                self._template_cache[cache_key] = self._env.from_string(self._template)

            # Render template
            template = self._template_cache[cache_key]
            rendered = template.render(**doc_context.model_dump())

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
            context: Template context with documentation data

        Returns:
            True if valid, False otherwise

        Raises:
            TemplateError: If validation fails
        """
        try:
            # Validate context data
            DocContext(**context.data)
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

            if not self._template:
                raise TemplateError(
                    "Template not loaded",
                    template_id=self.metadata.id,
                )

            with file_path.open("w") as f:
                f.write(self._template)
        except Exception as e:
            raise TemplateError(
                f"Failed to save template: {e}",
                template_id=self.metadata.id,
            ) from e

    def _apply_style_guide(self, content: str) -> str:
        """Apply style guide formatting to content.

        Args:
            content: Documentation content

        Returns:
            Formatted content as a string
        """
        return self._format_content(content)

    def _format_content(
        self,
        content: (
            str
            | int
            | float
            | bool
            | dict[str, str | int | float | bool]
            | list[str | int | float | bool]
            | None
        ),
    ) -> str:
        """Format documentation content.

        Args:
            content: Documentation content to format, can be a string or a value
                that can be converted to string

        Returns:
            Formatted content as a string
        """
        if not isinstance(content, str):
            return str(content)
        return content
