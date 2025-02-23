"""Core module for the Pepperpy framework.

This module provides the core functionality and types used throughout the framework.
"""

from pepperpy.core.base import (
    BaseAgent,
    BaseCapability,
    BaseComponent,
    BaseProvider,
    BaseResource,
    BaseWorkflow,
    ComponentState,
)
from pepperpy.core.errors import (
    AdapterError,
    AgentError,
    CapabilityError,
    CLIError,
    ComponentError,
    ConfigError,
    ContentError,
    DuplicateError,
    ExtensionError,
    FactoryError,
    HubError,
    LifecycleError,
    LLMError,
    MetricsError,
    MonitoringError,
    NetworkError,
    NotFoundError,
    PluginError,
    ProviderError,
    ResourceError,
    SecurityError,
    StateError,
    StorageError,
    ValidationError,
    WorkflowError,
)
from pepperpy.core.errors import (
    PepperpyMemoryError as MemoryError,
)
from pepperpy.core.lifecycle import Lifecycle, LifecycleManager
from pepperpy.core.metrics import MetricsManager
from pepperpy.core.types import (
    AgentID,
    BaseModel,
    CapabilityID,
    Field,
    Message,
    MessageContent,
    MessageID,
    MessageType,
    MetadataDict,
    MetadataValue,
    ProviderID,
    ResourceID,
    Response,
    WorkflowID,
)

__all__ = [
    # Base classes
    "BaseAgent",
    "BaseCapability",
    "BaseComponent",
    "BaseProvider",
    "BaseResource",
    "BaseWorkflow",
    "ComponentState",
    "Lifecycle",
    "LifecycleManager",
    "MetricsManager",
    # Models
    "BaseModel",
    "Field",
    # Types
    "AgentID",
    "CapabilityID",
    "Message",
    "MessageContent",
    "MessageID",
    "MessageType",
    "MetadataDict",
    "MetadataValue",
    "ProviderID",
    "ResourceID",
    "Response",
    "WorkflowID",
    # Errors
    "AdapterError",
    "AgentError",
    "CapabilityError",
    "CLIError",
    "ComponentError",
    "ConfigError",
    "ContentError",
    "DuplicateError",
    "ExtensionError",
    "FactoryError",
    "HubError",
    "LifecycleError",
    "LLMError",
    "MemoryError",
    "MetricsError",
    "MonitoringError",
    "NetworkError",
    "NotFoundError",
    "PluginError",
    "ProviderError",
    "ResourceError",
    "SecurityError",
    "StateError",
    "StorageError",
    "ValidationError",
    "WorkflowError",
]

__version__ = "0.1.0"
