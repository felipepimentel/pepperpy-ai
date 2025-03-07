"""Public interfaces for PepperPy Apps module.

This module provides high-level application templates for various AI tasks.
"""

from pepperpy.apps.assistant import AssistantApp
from pepperpy.apps.base import BaseApp
from pepperpy.apps.content import ContentApp
from pepperpy.apps.data import DataApp
from pepperpy.apps.media import MediaApp
from pepperpy.apps.rag import RAGApp
from pepperpy.apps.text import TextApp

__all__ = [
    "BaseApp",
    "TextApp",
    "DataApp",
    "ContentApp",
    "MediaApp",
    "RAGApp",
    "AssistantApp",
]
