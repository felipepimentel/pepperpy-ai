"""Core functionality for the Pepperpy framework.

This module provides core functionality and base classes for the Pepperpy
framework, including:
- Base classes for agents and providers
- Core types and protocols
- Event system
- Registry management
"""

from pepperpy.common.errors import (
    ContextError,
    FactoryError,
    LifecycleError,
    OrchestratorError,
    PepperpyError,
    RuntimeError,
    ShardingError,
    StateError,
)
from pepperpy.core.base import (
    AgentCapability,
    AgentConfig,
    AgentContext,
    AgentProtocol,
    AgentState,
)
from pepperpy.core.client import PepperpyClient
from pepperpy.core.events import Event, EventBus, EventHandler
from pepperpy.core.factory import AgentFactory, ComponentFactory
from pepperpy.core.protocols import FrameworkAdapter, Memory, Tool
from pepperpy.core.registry import Registry
from pepperpy.core.types import Message, MessageType, Response, ResponseStatus

__all__ = [
    "AgentCapability",
    "AgentConfig",
    "AgentContext",
    "AgentFactory",
    "AgentProtocol",
    "AgentState",
    "ComponentFactory",
    "ContextError",
    "Event",
    "EventBus",
    "EventHandler",
    "FactoryError",
    "FrameworkAdapter",
    "LifecycleError",
    "Memory",
    "Message",
    "MessageType",
    "OrchestratorError",
    "PepperpyClient",
    "PepperpyError",
    "Registry",
    "Response",
    "ResponseStatus",
    "RuntimeError",
    "ShardingError",
    "StateError",
    "Tool",
]

__version__ = "0.1.0"
