"""Core functionality for the Pepperpy framework.

This module provides core functionality and base classes for the Pepperpy
framework, including:
- Base classes for agents and providers
- Core types and protocols
- Event system
- Registry management
"""

from pepperpy.core.base import (
    AgentCapability,
    AgentConfig,
    AgentContext,
    AgentProtocol,
    AgentState,
)
from pepperpy.core.client import PepperpyClient
from pepperpy.core.config import AutoConfig, PepperpyConfig, ProviderConfig
from pepperpy.core.errors import (
    ConfigurationError,
    ContextError,
    FactoryError,
    LifecycleError,
    OrchestratorError,
    PepperpyError,
    PermissionError,
    RuntimeError,
    ShardingError,
    StateError,
    ToolError,
)
from pepperpy.core.events import Event, EventBus, EventHandler, EventType
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
    "AutoConfig",
    "ComponentFactory",
    "ConfigurationError",
    "ContextError",
    "Event",
    "EventBus",
    "EventHandler",
    "EventType",
    "FactoryError",
    "FrameworkAdapter",
    "LifecycleError",
    "Memory",
    "Message",
    "MessageType",
    "OrchestratorError",
    "PepperpyClient",
    "PepperpyConfig",
    "PepperpyError",
    "PermissionError",
    "ProviderConfig",
    "Registry",
    "Response",
    "ResponseStatus",
    "RuntimeError",
    "ShardingError",
    "StateError",
    "Tool",
    "ToolError",
]

__version__ = "0.1.0"
