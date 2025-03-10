"""Public interfaces for PepperPy Apps module.

This module provides high-level application templates for various AI tasks.
It exports all the public classes and functions from the apps module.
"""

from pepperpy.apps.assistant import (
    AssistantApp,
    AssistantResponse,
    Conversation,
    Message,
)
from pepperpy.apps.content import ContentApp, ContentResult
from pepperpy.apps.core import AppResult, BaseApp
from pepperpy.apps.data import DataApp, DataResult
from pepperpy.apps.media import MediaApp, MediaResult
from pepperpy.apps.rag import RAGApp, RAGResult
from pepperpy.apps.text import TextApp, TextResult

__all__ = [
    # Base classes
    "BaseApp",
    "AppResult",
    # Text applications
    "TextApp",
    "TextResult",
    # Data applications
    "DataApp",
    "DataResult",
    # Content applications
    "ContentApp",
    "ContentResult",
    # Media applications
    "MediaApp",
    "MediaResult",
    # RAG applications
    "RAGApp",
    "RAGResult",
    # Assistant applications
    "AssistantApp",
    "Message",
    "Conversation",
    "AssistantResponse",
]
