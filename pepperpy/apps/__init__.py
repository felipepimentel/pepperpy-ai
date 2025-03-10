"""PepperPy Applications Module.

This module provides high-level application templates for various AI tasks,
simplifying the development of AI applications.

PepperPy applications follow a common architecture and provide consistent
interfaces for different types of data and content processing.

Classes:
    BaseApp: Base class for all PepperPy applications
    TextApp: Application for text processing
    DataApp: Application for structured data processing
    ContentApp: Application for content generation
    MediaApp: Application for media processing
    RAGApp: Application for Retrieval Augmented Generation
    AssistantApp: Application for AI assistants

Example:
    >>> from pepperpy.apps import TextApp
    >>> app = TextApp("my_text_app")
    >>> app.configure(operations=["summarize", "translate"])
    >>> result = await app.process("Text to process")
    >>> print(result.text)
"""

from pepperpy.apps import public
from pepperpy.apps.public import *

# Re-export everything from public
__all__ = public.__all__

"""Applications module for PepperPy.

This module provides high-level applications built on top of the framework.
"""

# Ensure the directory exists
import os
from typing import Any, Dict, List, Optional, Union

os.makedirs(os.path.dirname(__file__), exist_ok=True)

# Import from public module
from pepperpy.apps.public import RAGApp

__all__ = ["RAGApp"]
