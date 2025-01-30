"""
Prompt template management and execution.

This module provides the core functionality for loading, validating,
and executing prompt templates in the Pepperpy system.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml

from pepperpy.common.config import get_config
from pepperpy.providers.base import BaseProvider


@dataclass
class PromptMetadata:
    """Metadata for a prompt template."""
    name: str
    version: str
    category: str
    model: str
    temperature: float
    tags: List[str]


@dataclass
class PromptContext:
    """Context information for a prompt template."""
    description: str
    input_format: str
    output_format: str
    examples: List[Dict[str, str]]


@dataclass
class PromptValidation:
    """Validation rules for a prompt template."""
    required_fields: List[str]
    constraints: Dict[str, Any]


class PromptTemplate:
    """A template for generating prompts with variable substitution."""

    def __init__(
        self,
        template: str,
        metadata: PromptMetadata,
        context: PromptContext,
        validation: PromptValidation,
    ) -> None:
        """Initialize a prompt template.

        Args:
            template: The template string with variables in {{var}} format
            metadata: Metadata about the prompt
            context: Context information about usage
            validation: Validation rules for the prompt
        """
        self.template = template
        self.metadata = metadata
        self.context = context
        self.validation = validation

    @classmethod
    def load(
        cls,
        path: Union[str, Path],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
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
            config = get_config()
            path = Path(config.project_root) / "prompts" / path

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

        return cls(
            template=data["template"],
            metadata=metadata,
            context=context,
            validation=validation,
        )

    def format(self, **kwargs: Any) -> str:
        """Format the template with the provided variables.

        Args:
            **kwargs: Variables to substitute in the template

        Returns:
            The formatted prompt string

        Raises:
            ValueError: If required fields are missing or constraints are violated
        """
        # Validate required fields
        missing = [f for f in self.validation.required_fields if f not in kwargs]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        # Validate constraints
        if "max_length" in self.validation.constraints:
            max_len = self.validation.constraints["max_length"]
            for key, value in kwargs.items():
                if len(str(value)) > max_len:
                    raise ValueError(
                        f"Value for {key} exceeds max length of {max_len}"
                    )

        # Format template
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")

    async def execute(
        self,
        provider: BaseProvider,
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
        formatted = self.format(**kwargs)
        return await provider.generate(
            formatted,
            model=self.metadata.model,
            temperature=self.metadata.temperature,
        ) 