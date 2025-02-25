"""Pepperpy framework.

A Python framework for building AI-powered applications.
"""

__version__ = "0.1.0"

from pepperpy.core.context import (
    clear_context,
    get_context,
    get_context_value,
    set_context,
    update_context,
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
from pepperpy.core.registry import (
    clear_registry,
    create_provider,
    get_or_create_provider,
    get_provider,
    get_provider_type,
    register_provider,
    register_provider_type,
)
from pepperpy.security import (
    AuthenticationError,
    AuthorizationError,
    BaseSecurityProvider,
    SecurityProvider,
    hash_data,
    verify_hash,
    verify_key,
)

__all__ = [
    "AdapterError",
    "AgentError",
    "AuthenticationError",
    "AuthorizationError",
    "BaseSecurityProvider",
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
    "MetricsError",
    "MonitoringError",
    "NetworkError",
    "NotFoundError",
    "PluginError",
    "ProviderError",
    "ResourceError",
    "SecurityError",
    "SecurityProvider",
    "StateError",
    "StorageError",
    "ValidationError",
    "WorkflowError",
    "clear_context",
    "clear_registry",
    "create_provider",
    "get_context",
    "get_context_value",
    "get_or_create_provider",
    "get_provider",
    "get_provider_type",
    "hash_data",
    "register_provider",
    "register_provider_type",
    "set_context",
    "update_context",
    "verify_hash",
    "verify_key",
]
