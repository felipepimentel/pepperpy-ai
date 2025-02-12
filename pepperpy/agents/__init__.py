"""Agents package initialization.

This module provides access to different agent types through a unified interface.
"""

from pepperpy.agents.research_assistant import ResearchAssistant
from pepperpy.core.base import BaseAgent

__all__ = [
    "BaseAgent",
    "ResearchAssistant",
]
