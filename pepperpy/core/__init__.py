"""Core functionality for the Pepperpy framework.

This module provides core functionality and base classes for the Pepperpy
framework, including:
- Base classes for agents and providers
- Core types and protocols
- Event system
- Registry management
"""

from pepperpy.core.base import (
    AgentConfig,
    AgentContext,
    AgentProtocol,
    AgentState,
)
from pepperpy.core.capabilities import (
    BaseCapability,
    Capability,
    CapabilityConfig,
    CapabilityError,
    CapabilityNotFoundError,
    CapabilityConfigError,
    CapabilityInitError,
    CapabilityCleanupError,
    registry as capability_registry,
)
from pepperpy.core.client import PepperpyClient
from pepperpy.core.config import PepperpyConfig
from pepperpy.core.types import (
    Message,
    MessageType,
    ProviderConfig,
    Response,
    ResponseStatus,
)
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

__all__ = [
    # Agent types
    "AgentConfig",
    "AgentContext",
    "AgentFactory",
    "AgentProtocol",
    "AgentState",
    # Capability system
    "BaseCapability",
    "Capability",
    "CapabilityConfig",
    "CapabilityError",
    "CapabilityNotFoundError",
    "CapabilityConfigError",
    "CapabilityInitError",
    "CapabilityCleanupError",
    "capability_registry",
    # Configuration
    "ComponentFactory",
    "ConfigurationError",
    "ContextError",
    # Events
    "Event",
    "EventBus",
    "EventHandler",
    "EventType",
    # Errors
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
