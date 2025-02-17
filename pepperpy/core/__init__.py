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
    Identifiable,
    Lifecycle,
    Metadata,
    Registry,
    Validatable,
)
from pepperpy.core.capabilities import (
    AnalysisError,
    Capability,
    CapabilityContext,
    CapabilityError,
    CapabilityResult,
    CapabilityType,
    GenerationError,
    LearningError,
    MemoryError,
    PerceptionError,
    PlanningError,
    ReasoningError,
)
from pepperpy.core.capabilities import (
    registry as capability_registry,
)
from pepperpy.core.client import PepperpyClient
from pepperpy.core.config import PepperpyConfig
from pepperpy.core.errors import (
    ConfigurationError,
    ErrorCategory,
    ErrorContext,
    ErrorMetadata,
    PepperpyError,
    StateError,
)
from pepperpy.core.events import Event, EventBus, EventHandler, EventType
from pepperpy.core.factory import AgentFactory, ComponentFactory
from pepperpy.core.protocols import (
    FrameworkAdapter,
    Memory,
    MemoryEntry,
    MemoryScope,
    Tool,
    ToolMetadata,
    ToolPermission,
    ToolScope,
)
from pepperpy.core.registry import Registry
from pepperpy.core.types import (
    AgentConfig,
    AgentContext,
    AgentID,
    CapabilityID,
    MemoryID,
    Message,
    MessageType,
    ProviderConfig,
    ProviderID,
    ResourceID,
    Response,
    ResponseStatus,
    WorkflowID,
)

__all__ = [
    # Base components
    "BaseAgent",
    "BaseCapability",
    "BaseComponent",
    "BaseProvider",
    "BaseResource",
    "BaseWorkflow",
    "Identifiable",
    "Lifecycle",
    "Metadata",
    "Registry",
    "Validatable",
    # Agent types
    "AgentConfig",
    "AgentContext",
    "AgentFactory",
    "Message",
    "MessageType",
    "ProviderConfig",
    "Response",
    "ResponseStatus",
    # Capability system
    "Capability",
    "CapabilityContext",
    "CapabilityResult",
    "CapabilityError",
    "CapabilityType",
    "AnalysisError",
    "GenerationError",
    "LearningError",
    "MemoryError",
    "PerceptionError",
    "PlanningError",
    "ReasoningError",
    "capability_registry",
    # Configuration
    "ComponentFactory",
    "PepperpyConfig",
    # Events
    "Event",
    "EventBus",
    "EventHandler",
    "EventType",
    # Framework
    "FrameworkAdapter",
    "Memory",
    "MemoryEntry",
    "MemoryScope",
    # Tools
    "Tool",
    "ToolMetadata",
    "ToolPermission",
    "ToolScope",
    # Errors
    "ConfigurationError",
    "ErrorCategory",
    "ErrorContext",
    "ErrorMetadata",
    "PepperpyError",
    "StateError",
    # Type definitions
    "AgentID",
    "CapabilityID",
    "MemoryID",
    "ProviderID",
    "ResourceID",
    "WorkflowID",
    "PepperpyClient",
]

__version__ = "0.1.0"
