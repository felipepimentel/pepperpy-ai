"""Agents module for the Pepperpy framework.

This module provides various agent implementations for different purposes.
The agents are organized by their primary function:

- Research agents (research.py):
  - ResearchAgent: General-purpose research agent
  - ResearchAssistant: Academic research assistant
  - ResearcherAgent: Specialized research and analysis agent
"""

from pepperpy.agents.base import BaseAgent
from pepperpy.agents.factory import AgentFactory
from pepperpy.agents.research import (
    ResearchAgent,
    ResearchAssistant,
    ResearcherAgent,
)

__version__ = "0.1.0"

__all__ = [
    "BaseAgent",
    "AgentFactory",
    "ResearchAgent",
    "ResearchAssistant",
    "ResearcherAgent",
]
