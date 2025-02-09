"""Prompt module for managing AI prompts.

This module provides prompt template functionality for generating prompts
for language models with dynamic content.
"""

from .template import (
    BaseTemplate,
    PromptTemplate,
    create_prompt_template,
    register_template,
)

__all__ = [
    "BaseTemplate",
    "PromptTemplate",
    "create_prompt_template",
    "register_template",
]
