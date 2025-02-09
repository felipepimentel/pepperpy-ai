"""Prompt template management and execution.

This module provides the core functionality for loading, validating,
and executing prompt templates in the Pepperpy system.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar, cast
from uuid import uuid4

import yaml
from jinja2 import Environment, StrictUndefined, Template, select_autoescape
from pydantic import BaseModel, Field, field_validator

from pepperpy.core.types import Message, MessageType
from pepperpy.providers.base import BaseProvider

# Type variables for generic implementations
T_Input = TypeVar("T_Input")
T_Output = TypeVar("T_Output")


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

    def __init__(self, message: str, template_id: str | None = None) -> None:
        """Initialize template error.

        Args:
            message: Error message
            template_id: Optional template identifier
        """
        super().__init__(message)
        self.template_id = template_id


class TemplateValidationError(TemplateError):
    """Raised when template validation fails."""


class TemplateRenderError(TemplateError):
    """Raised when template rendering fails."""


class PromptTemplate(BaseModel):
    """A template for generating prompts.

    Attributes:
        template: The template string.
        variables: Variables used in the template.
        _jinja_env: Jinja2 environment for template rendering
        _jinja_template: Compiled Jinja2 template
    """

    template: str = Field(..., min_length=1)
    variables: dict[str, Any] = Field(default_factory=dict)
    _jinja_env: Environment = Environment(
        undefined=StrictUndefined,
        autoescape=select_autoescape(
            enabled_extensions=("html", "xml", "jinja2"),
            default_for_string=True,
        ),
    )
    _jinja_template: Template | None = None

    def __init__(
        self,
        **data: (
            str
            | int
            | float
            | bool
            | Mapping[str, Any]
            | list[str | int | float | bool]
            | None
        ),
    ) -> None:
        """Initialize the template.

        Args:
            **data: Template data including template string and variables.
        """
        super().__init__(**data)
        self._jinja_template = self._jinja_env.from_string(self.template)

    @field_validator("template")
    @classmethod
    def validate_template(cls, v: str) -> str:
        """Validate template string.

        Args:
            v: Template string to validate

        Returns:
            Validated template string

        Raises:
            ValueError: If template is empty or invalid
        """
        if not v.strip():
            raise ValueError("Template cannot be empty")
        return v.strip()

    def render(
        self,
        context: Mapping[
            str,
            str
            | int
            | float
            | bool
            | Mapping[str, Any]
            | list[str | int | float | bool]
            | None,
        ],
    ) -> str:
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

    async def execute(
        self,
        provider: BaseProvider,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Execute the template using the provided provider.

        Args:
            provider: The provider to use for completion.
            context: Optional additional context for template rendering.

        Returns:
            The completion result from the provider.

        Raises:
            TemplateRenderError: If template rendering fails.
        """
        render_context = context or {}
        prompt = self.render(render_context)
        model = self.variables.get("model")
        temperature = cast(float, self.variables.get("temperature", 0.7))

        # Create message for provider
        message = Message(
            id=uuid4(),
            type=MessageType.COMMAND,
            sender="prompt_template",
            receiver="provider",
            content={"text": prompt},
            metadata={
                "model": str(model) if model else None,
                "temperature": temperature,
            },
        )

        # Prepare provider arguments
        kwargs: dict[str, Any] = {"temperature": temperature}

        # Execute generation
        try:
            response = await provider.generate([message], **kwargs)
            text = response.content.get("text")
            if not isinstance(text, str):
                raise TemplateRenderError("Provider response missing text content")
            return text
        except Exception as e:
            if isinstance(e, TemplateRenderError):
                raise
            raise TemplateRenderError(f"Provider execution failed: {e}") from e

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
            yaml.YAMLError: If YAML parsing fails
        """
        if isinstance(path, str):
            path = Path(path)

        if not path.is_absolute():
            # Use module directory as base for relative paths
            module_dir = Path(__file__).parent
            path = module_dir / "prompts" / path

        if not path.exists():
            raise FileNotFoundError(f"Template not found: {path}")

        try:
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
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}") from e
        except KeyError as e:
            raise ValueError(f"Missing required field: {e}") from e
        except Exception as e:
            raise ValueError(f"Failed to load template: {e}") from e

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

        Raises:
            ValueError: If required data is missing or invalid
        """
        try:
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
        except KeyError as e:
            raise ValueError(f"Missing required field: {e}") from e
        except Exception as e:
            raise ValueError(f"Failed to load template: {e}") from e
