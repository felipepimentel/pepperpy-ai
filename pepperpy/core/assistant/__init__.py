"""Developer assistance module for PepperPy.

This module provides tools and utilities to help developers get started with PepperPy,
including interactive assistants, templates, and guided creation of components.
"""

from typing import Any, Dict, List, Optional, Union

from pepperpy.core.assistant.factory import create_assistant
from pepperpy.core.assistant.templates import get_template, list_templates
from pepperpy.core.assistant.types import AssistantType, TemplateCategory

__all__ = [
    "create_assistant",
    "get_template",
    "list_templates",
    "AssistantType",
    "TemplateCategory",
]
