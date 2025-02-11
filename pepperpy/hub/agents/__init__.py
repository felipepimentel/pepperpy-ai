"""Agents package for managing AI agents.

This package provides base classes and implementations for different AI agents.
"""

from pepperpy.hub.agents.base import Agent, AgentConfig, AgentRegistry
from pepperpy.hub.agents.research_assistant import ResearchAssistantAgent

__all__ = [
    "Agent",
    "AgentConfig",
    "AgentRegistry",
    "ResearchAssistantAgent",
]
