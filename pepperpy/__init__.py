"""PepperPy AI library."""

from pepperpy import (
    ConfigurationManager,
    Container,
    ErrorManager,
    LoggerFactory,
    MessageBus,
    PluginManager,
)

from .agents import Agent, AgentContext, AgentFactory
from .shared import *  # noqa: F403
from .tools import Tool, ToolChain, ToolFactory

__version__ = "1.0.0"

__all__ = [
    # Agent system
    "Agent",
    "AgentContext",
    "AgentFactory",
    # Core functionality
    "ConfigurationManager",
    "Container",
    "ErrorManager",
    "LoggerFactory",
    "MessageBus",
    "PluginManager",
    # Tool system
    "Tool",
    "ToolChain",
    "ToolFactory",
]
