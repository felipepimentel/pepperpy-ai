"""Agent capabilities for PepperPy.

This module provides a unified interface for working with AI agents,
including intent recognition, memory management, and interaction patterns.

Example:
    >>> from pepperpy.agents import Agent
    >>> agent = Agent("assistant")
    >>> agent.add_memory("User likes Python")
    >>> response = agent.process("What language do I like?")
    >>> assert "Python" in response
"""

from pepperpy.agents.base import Agent

__all__ = [
    "Agent",
]
