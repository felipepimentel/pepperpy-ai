"""
Agents module for Pepperpy framework.

This module provides a flexible and extensible agent system that combines
various providers and capabilities to perform specific tasks.
"""

from pepperpy.agents.base.base_agent import BaseAgent, AgentError
from pepperpy.agents.factory.agent_factory import AgentFactory, AgentFactoryError

__all__ = [
    'BaseAgent',
    'AgentError',
    'AgentFactory',
    'AgentFactoryError',
]
