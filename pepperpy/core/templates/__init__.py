"""Template system for the Pepperpy framework.

This module provides a comprehensive template system for:
- Prompt templates and generation
- Configuration templates
- Code generation templates
- Documentation templates
- Message templates
"""

from .base import Template, TemplateContext, TemplateError, TemplateMetadata
from .prompt import (
    PromptContext,
    PromptMetadata,
    PromptTemplate,
    PromptValidation,
    TemplateRenderError,
    TemplateValidationError,
)

__all__ = [
    "PromptContext",
    "PromptMetadata",
    "PromptTemplate",
    "PromptValidation",
    "Template",
    "TemplateContext",
    "TemplateError",
    "TemplateMetadata",
    "TemplateRenderError",
    "TemplateValidationError",
]
