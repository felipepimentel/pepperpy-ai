"""Pepperpy - A Python library for building AI-powered research assistants.

This module provides a high-level API for creating and managing AI agents
specialized in research tasks, including topic analysis, source discovery,
and information synthesis.
"""

from pepperpy.core.client import PepperpyClient
from pepperpy.core.config import PepperpyConfig
from pepperpy.hub.agents import ResearchAssistantAgent

__version__ = "0.1.0"

__all__ = [
    "PepperpyClient",
    "PepperpyConfig",
    "ResearchAssistantAgent",
]
