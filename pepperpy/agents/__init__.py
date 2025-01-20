"""Agents module for managing AI agents.

This module provides the base agent implementation and interfaces for creating
and managing AI agents. It handles agent configurations, types, and lifecycle
services.
"""

from .agent import BaseAgent, AgentError
from .interfaces import (
    AgentInterface,
    AgentConfig,
    AgentState,
    AgentContext,
    AgentResponse,
)

__all__ = [
    # Base agent
    "BaseAgent",
    "AgentError",
    # Interfaces
    "AgentInterface",
    "AgentConfig",
    "AgentState",
    "AgentContext",
    "AgentResponse",
]
