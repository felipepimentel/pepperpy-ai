"""Prompt template management and execution.

This module provides the core functionality for loading, validating,
and executing prompt templates in the Pepperpy system.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, StrictUndefined, Template
from pydantic import BaseModel

from pepperpy.providers.provider import Provider


@dataclass
class PromptMetadata:
    """Metadata for a prompt template."""

    name: str
    version: str
    category: str
    model: str
    temperature: float
    tags: list[str]


@dataclass
class PromptContext:
    """Context information for a prompt template."""

    description: str
    input_format: str
    output_format: str
    examples: list[dict[str, str]]


@dataclass
class PromptValidation:
    """Validation rules for a prompt template."""

    required_fields: list[str]
    constraints: dict[str, Any]


class TemplateError(Exception):
    """Base class for template-related errors."""


class TemplateValidationError(TemplateError):
    """Raised when template validation fails."""


class TemplateRenderError(TemplateError):
    """Raised when template rendering fails."""


class PromptTemplate(BaseModel):
    """A template for generating prompts.

    Attributes:
        template: The template string.
        variables: Variables used in the template.
    """

    template: str
    variables: dict[str, Any] = {}
    _jinja_env: Environment = Environment(undefined=StrictUndefined)
    _jinja_template: Template | None = None

    def __init__(self, **data: Any) -> None:
        """Initialize the template.

        Args:
            **data: Template data including template string and variables.
        """
        super().__init__(**data)
        self._jinja_template = self._jinja_env.from_string(self.template)

    def render(self, context: dict[str, Any]) -> str:
        """Render the template with the given context.

        Args:
            context: The context containing variable values.

        Returns:
            The rendered template string.

        Raises:
            TemplateRenderError: If rendering fails.
        """
        try:
            if not self._jinja_template:
                self._jinja_template = self._jinja_env.from_string(self.template)

            # Combine default variables with context
            render_context = {**self.variables, **context}
            if not self._jinja_template:
                raise TemplateRenderError("Template not initialized")
            return self._jinja_template.render(**render_context)
        except Exception as e:
            raise TemplateRenderError(f"Failed to render template: {e}") from e

    def validate_template(self) -> None:
        """Validate the template.

        Raises:
            TemplateValidationError: If validation fails.
        """
        try:
            self.render({})
        except TemplateRenderError as e:
            raise TemplateValidationError("Template validation failed") from e

    @classmethod
    def load(
        cls,
        path: str | Path,
        model: str | None = None,
        temperature: float | None = None,
    ) -> "PromptTemplate":
        """Load a prompt template from a YAML file.

        Args:
            path: Path to the YAML template file
            model: Optional model override
            temperature: Optional temperature override

        Returns:
            A PromptTemplate instance

        Raises:
            FileNotFoundError: If template file doesn't exist
            ValueError: If template is invalid
        """
        if isinstance(path, str):
            path = Path(path)

        if not path.is_absolute():
            # Use module directory as base for relative paths
            module_dir = Path(__file__).parent.parent
            path = module_dir / "prompts" / path

        if not path.exists():
            raise FileNotFoundError(f"Template not found: {path}")

        with path.open() as f:
            data = yaml.safe_load(f)

        # Create metadata with optional overrides
        metadata = PromptMetadata(
            name=data["metadata"]["name"],
            version=data["metadata"]["version"],
            category=data["metadata"]["category"],
            model=model or data["metadata"]["model"],
            temperature=temperature or data["metadata"]["temperature"],
            tags=data["metadata"]["tags"],
        )

        context = PromptContext(
            description=data["context"]["description"],
            input_format=data["context"]["input_format"],
            output_format=data["context"]["output_format"],
            examples=data["context"]["examples"],
        )

        validation = PromptValidation(
            required_fields=data["validation"]["required_fields"],
            constraints=data["validation"]["constraints"],
        )

        template = cls(
            template=data["template"],
            variables={
                **data.get("variables", {}),
                "model": metadata.model,
                "temperature": metadata.temperature,
                "context": context,
                "validation": validation,
            },
        )

        return template

    @classmethod
    def load_from_dict(
        cls, data: dict[str, Any]
    ) -> tuple["PromptTemplate", PromptMetadata, PromptContext, PromptValidation]:
        """Load a prompt template from a dictionary.

        Args:
            data: Dictionary containing prompt template data.

        Returns:
            A tuple containing:
            - The loaded PromptTemplate instance
            - The PromptMetadata instance
            - The PromptContext instance
            - The PromptValidation instance
        """
        # Create metadata with optional overrides
        metadata = PromptMetadata(
            name=data["metadata"]["name"],
            version=data["metadata"]["version"],
            category=data["metadata"]["category"],
            model=data["metadata"]["model"],
            temperature=data["metadata"]["temperature"],
            tags=data["metadata"]["tags"],
        )

        context = PromptContext(
            description=data["context"]["description"],
            input_format=data["context"]["input_format"],
            output_format=data["context"]["output_format"],
            examples=data["context"]["examples"],
        )

        validation = PromptValidation(
            required_fields=data["validation"]["required_fields"],
            constraints=data["validation"]["constraints"],
        )

        template = cls(
            template=data["template"],
            variables=data.get("variables", {}),
        )

        return template, metadata, context, validation

    async def execute(
        self,
        provider: Provider,
        **kwargs: Any,
    ) -> str:
        """Execute the prompt with the given provider.

        Args:
            provider: The provider to execute the prompt with
            **kwargs: Variables to substitute in the template

        Returns:
            The generated response

        Raises:
            ValueError: If template formatting fails
            Exception: If provider execution fails
        """
        formatted = self.render(kwargs)
        response = await provider.complete(
            formatted,
            model=self.variables.get("model", ""),
            temperature=self.variables.get("temperature", 0.0),
        )

        # Handle both string and async iterator responses
        if isinstance(response, str):
            return response

        # If it's an async iterator, collect all chunks
        chunks = []
        async for chunk in response:
            chunks.append(chunk)
        return "".join(chunks)
