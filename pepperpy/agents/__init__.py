"""Agent and Assistant capabilities for PepperPy.

This module provides a unified interface for working with AI agents and assistants,
including intent recognition, memory management, and interaction patterns.

Example:
    >>> from pepperpy.agents import Agent, Assistant
    >>> agent = Agent.from_config({
    ...     "type": "chat",
    ...     "model": "gpt-4",
    ...     "system_prompt": "You are a helpful assistant."
    ... })
    >>> assistant = Assistant.from_config({
    ...     "type": "task",
    ...     "tools": ["search", "calculate"]
    ... })
"""

from pepperpy.agents.assistant import Assistant, AssistantConfig
from pepperpy.agents.base import Agent, AgentConfig
from pepperpy.agents.intent import Intent, IntentConfig
from pepperpy.agents.memory import Memory, MemoryConfig

__all__ = [
    # Base types
    "Agent",
    "AgentConfig",
    "Assistant",
    "AssistantConfig",
    # Intent management
    "Intent",
    "IntentConfig",
    # Memory management
    "Memory",
    "MemoryConfig",
]
