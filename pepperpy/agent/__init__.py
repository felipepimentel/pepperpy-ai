"""
PepperPy Agent Module.

Module for agent configuration and execution.
"""

# Results
# Memory implementations
from pepperpy.agent.base import AgentProvider, BaseAgentProvider
from pepperpy.agent.memory import PersistentMemory, SimpleMemory
from pepperpy.agent.result import AgentTaskResult, ConversationResult

# Task and protocol classes
from pepperpy.agent.task import (
    AgentTask,
    Analysis,
    ChatSession,
    ConversationTask,
    Message,
    TaskBase,
)

# Tool integration
from pepperpy.agent.tool_enabled import ToolEnabledAgent

__all__ = [
    # Results
    "AgentTaskResult",
    "ConversationResult",
    # Base classes and protocols
    "BaseAgentProvider",
    "AgentProvider",
    # Memory implementations
    "PersistentMemory",
    "SimpleMemory",
    # Task classes
    "TaskBase",
    "AgentTask",
    "Analysis",
    "ConversationTask",
    "ChatSession",
    # Data classes
    "Message",
    # Tool integration
    "ToolEnabledAgent",
]
