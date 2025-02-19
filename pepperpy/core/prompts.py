"""Prompt template system for the Pepperpy framework.

This module provides functionality for managing and rendering prompt
templates with variable substitution and validation.
"""

from typing import Any, Dict
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from pepperpy.core.errors import ConfigurationError
from pepperpy.core.logging import get_logger

# Configure logging
logger = get_logger(__name__)


class PromptTemplate(BaseModel):
    """Prompt template with variable substitution.

    Attributes:
        id: Unique template identifier
        template: Template string with variables
        variables: Variable definitions and constraints
        metadata: Additional template metadata
    """

    id: UUID = Field(default_factory=uuid4)
    template: str
    variables: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def render(self, variables: Dict[str, Any]) -> str:
        """Render the template with provided variables.

        Args:
            variables: Variable values for substitution

        Returns:
            Rendered template string

        Raises:
            ConfigurationError: If required variables are missing
        """
        try:
            return self.template.format(**variables)
        except KeyError as e:
            raise ConfigurationError(f"Missing required variable: {e}")
        except Exception as e:
            raise ConfigurationError(f"Template rendering failed: {e}")


async def create_prompt_template(config: Dict[str, Any]) -> PromptTemplate:
    """Create a prompt template from configuration.

    Args:
        config: Template configuration

    Returns:
        Configured prompt template

    Raises:
        ConfigurationError: If configuration is invalid
    """
    try:
        return PromptTemplate(**config)
    except Exception as e:
        raise ConfigurationError(f"Failed to create prompt template: {e}")
