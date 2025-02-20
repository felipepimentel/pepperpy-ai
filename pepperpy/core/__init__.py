"""Core module for the Pepperpy framework.

This module provides the core functionality and base components for building
AI-powered applications with Pepperpy.
"""

from pepperpy.core.base import (
    BaseAgent,
    BaseCapability,
    BaseComponent,
    BaseProvider,
    BaseResource,
    BaseWorkflow,
    ComponentID,
    Identifiable,
    Lifecycle,
    Metadata,
    Registry,
    Validatable,
)
from pepperpy.core.client import PepperpyClient
from pepperpy.core.config import Configuration, PepperpyConfig
from pepperpy.core.errors import (
    ConfigurationError,
    ErrorCategory,
    ErrorContext,
    ErrorMetadata,
    PepperpyError,
    StateError,
)
from pepperpy.core.factory import AgentFactory, ComponentFactory
from pepperpy.core.processor import Processor
from pepperpy.core.types import (
    AgentID,
    CapabilityID,
    MemoryID,
    ProviderID,
    ResourceID,
    WorkflowID,
)
from pepperpy.events import Event, EventBus, EventHandler, EventType

__all__ = [
    "AgentFactory",
    "AgentID",
    "BaseAgent",
    "BaseCapability",
    "BaseComponent",
    "BaseProvider",
    "BaseResource",
    "BaseWorkflow",
    "CapabilityID",
    "ComponentFactory",
    "ComponentID",
    "Configuration",
    "ConfigurationError",
    "ErrorCategory",
    "ErrorContext",
    "ErrorMetadata",
    "Event",
    "EventBus",
    "EventHandler",
    "EventType",
    "Identifiable",
    "Lifecycle",
    "MemoryID",
    "Metadata",
    "PepperpyClient",
    "PepperpyConfig",
    "PepperpyError",
    "Processor",
    "ProviderID",
    "Registry",
    "ResourceID",
    "StateError",
    "Validatable",
    "WorkflowID",
]

__version__ = "0.1.0"
