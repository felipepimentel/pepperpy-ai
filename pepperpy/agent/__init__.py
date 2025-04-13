"""
PepperPy Agent Module.

Defines interfaces and implementations for autonomous agents.
"""

import importlib
import os
from typing import Any, Dict

from .base import AgentError, AgentProvider, BaseAgentProvider, Message
from .capability import (
    BaseCapability,
    BaseMemoryAware,
    BaseToolUser,
    Capability,
    MemoryAware,
    ToolUser,
)
from .composite import (
    CompositeAgent,
    CompositeAgentBuilder,
    create_composite_agent,
)
from .memory.base import (
    BaseMemoryStore,
    InMemoryStore,
    MemoryError,
    MemoryStore,
    VectorMemoryStore,
    create_memory_store,
)
from .result import ConversationResult, AgentTaskResult
from .task import Memory, TaskBase, EnhancerProxy, AgentTask, Analysis, ConversationTask, ChatSession

__all__ = [
    "AgentError",
    "AgentProvider",
    "BaseAgentProvider",
    "BaseCapability",
    "BaseMemoryAware",
    "BaseMemoryStore",
    "BaseToolUser",
    "Capability",
    "CompositeAgent",
    "CompositeAgentBuilder",
    "ConversationResult",
    "AgentTaskResult",
    "InMemoryStore",
    "Memory",
    "MemoryAware",
    "MemoryError",
    "MemoryStore",
    "Message",
    "TaskBase",
    "EnhancerProxy",
    "AgentTask",
    "Analysis", 
    "ConversationTask",
    "ChatSession",
    "ToolUser",
    "VectorMemoryStore",
    "create_agent",
    "create_composite_agent",
    "create_memory_store",
]


def create_agent(agent_type: str | None = None, **config: Any) -> BaseAgentProvider:
    """Create an agent provider.

    Args:
        agent_type: Type of agent provider to create
        **config: Configuration parameters

    Returns:
        Configured agent provider

    Raises:
        AgentError: If agent type is invalid
    """
    agent_type = agent_type or os.environ.get("PEPPERPY_AGENT_TYPE", "assistant")

    try:
        if agent_type == "composite":
            return create_composite_agent(**config)
        elif agent_type == "assistant":
            from plugins.agent.assistant.provider import AssistantAgentProvider

            return AssistantAgentProvider(**config)
        elif agent_type == "autogen":
            from plugins.agent.autogen.provider import AutogenAgentProvider

            return AutogenAgentProvider(**config)
        else:
            # Try to import from plugins
            module_name = f"plugins.agent.{agent_type}.provider"
            module = importlib.import_module(module_name)
            class_name = f"{agent_type.title()}AgentProvider"
            agent_class = getattr(module, class_name)
            return agent_class(**config)
    except (ImportError, AttributeError) as e:
        raise AgentError(f"Invalid agent type '{agent_type}': {e}") from e
