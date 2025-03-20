"""Agent provider implementations for PepperPy.

This module provides concrete implementations of agent providers,
supporting different types of AI agents and assistants.

Example:
    >>> from pepperpy.agents.providers import OpenAIAgent
    >>> agent = OpenAIAgent(model="gpt-4")
    >>> response = await agent.process("What's the weather?")
"""

from pepperpy.agents.providers.anthropic import AnthropicAgent
from pepperpy.agents.providers.local import LocalAgent
from pepperpy.agents.providers.openai import OpenAIAgent

__all__ = [
    "OpenAIAgent",
    "AnthropicAgent",
    "LocalAgent",
]
