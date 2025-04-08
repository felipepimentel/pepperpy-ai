"""
PepperPy Agent Module.

Module for agent configuration and execution.
"""

# Results
# Memory implementations
from pepperpy.agent.base import BaseAgentProvider
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

__all__ = [
    # Results
    "AgentTaskResult",
    "ConversationResult",
    # Base classes and protocols
    "BaseAgentProvider",
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
]
