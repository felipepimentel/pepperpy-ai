"""Core functionality for PepperPy.

This module provides the core functionality for PepperPy, including:
- Base models and interfaces
- Error handling
- Configuration management
- Dependency injection
- Event system
- Plugin discovery
- Validation utilities
- Logging and metrics
- Utility functions
"""

# We preserve the compatibility with the previous version
from pepperpy.core.base import (
    BaseComponent,
    Component,
    ComponentError,
    ComponentRegistry,
    Document,
    GenerationResult,
    JsonDict,
    JsonType,
    JsonValue,
    Metadata,
    SearchResult,
)

# Enhanced configuration management
from pepperpy.core.config import (
    Config,
    ConfigRegistry,
    ConfigSchema,
    ConfigSource,
    ConfigValue,
    create_typed_config,
    get_config_registry,
    get_domain_config,
    load_config_from_file,
    validated_config,
)

# Enhanced dependency injection
from pepperpy.core.di import (
    CircularDependencyError,
    Container,
    DIError,
    ServiceLifetime,
    ServiceNotFoundError,
    get_container,
    inject,
)

# Enhanced error handling
from pepperpy.core.errors import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ContentError,
    DuplicateError,
    EmbeddingError,
    LLMError,
    NetworkError,
    NotFoundError,
    ParsingError,
    PepperpyError,
    PluginError,
    PluginInitializationError,
    PluginNotFoundError,
    ProviderError,
    RAGError,
    ResourceError,
    ServiceError,
    StorageError,
    TimeoutError,
    ValidationError,
    ValidationErrorCollection,
    WorkflowError,
    raise_from,
    wrap_exception,
)

# Event system
from pepperpy.core.events import (
    Event,
    EventBus,
    EventContext,
    EventError,
    EventMonitor,
    EventType,
    TraceContext,
    emit_event,
    event_listener,
    get_current_context,
    get_event_bus,
    get_event_monitor,
    set_current_context,
    trace,
)

# Helper functions
from pepperpy.core.helpers import (
    convert_to_dict,
    flatten_dict,
    format_string,
    import_provider,
    lazy_provider_class,
    retry,
    unflatten_dict,
)
from pepperpy.core.logging import get_logger, logger
from pepperpy.core.memory import BaseMemory
from pepperpy.core.metrics import MetricsCollector
from pepperpy.core.validation import validate_config
from pepperpy.core.version import __version__
from pepperpy.llm import LLMProvider

# Plugin discovery
from pepperpy.plugins.discovery import (
    PluginInfo,
    PluginLoadError,
    PluginRegistry,
    PluginValidationError,
    create_provider_instance,
    get_plugin_registry,
)

# Provider types
from pepperpy.plugins.plugin import PepperpyPlugin
from pepperpy.rag import RAGProvider
from pepperpy.storage import StorageProvider

# For compatibility with older code - prefer using the newer error classes
ConfigError = ConfigurationError
ConnectionError = NetworkError
HTTPError = NetworkError
RequestError = NetworkError
ResponseError = NetworkError

__all__ = [
    # Base components
    "BaseComponent",
    "Component",
    "ComponentError",
    "ComponentRegistry",
    "Document",
    "GenerationResult",
    "JsonDict",
    "JsonType",
    "JsonValue",
    "Metadata",
    "SearchResult",
    # Error handling
    "AuthenticationError",
    "AuthorizationError",
    "ConfigurationError",
    "ContentError",
    "DuplicateError",
    "EmbeddingError",
    "LLMError",
    "NetworkError",
    "NotFoundError",
    "ParsingError",
    "PepperpyError",
    "PluginError",
    "PluginInitializationError",
    "PluginNotFoundError",
    "ProviderError",
    "RAGError",
    "ResourceError",
    "ServiceError",
    "StorageError",
    "TimeoutError",
    "ValidationError",
    "ValidationErrorCollection",
    "WorkflowError",
    "raise_from",
    "wrap_exception",
    # Configuration management
    "Config",
    "ConfigRegistry",
    "ConfigSchema",
    "ConfigSource",
    "ConfigValue",
    "create_typed_config",
    "get_config_registry",
    "get_domain_config",
    "load_config_from_file",
    "validated_config",
    # Dependency injection
    "CircularDependencyError",
    "Container",
    "DIError",
    "ServiceLifetime",
    "ServiceNotFoundError",
    "get_container",
    "inject",
    # Event system
    "Event",
    "EventBus",
    "EventContext",
    "EventError",
    "EventMonitor",
    "EventType",
    "TraceContext",
    "emit_event",
    "event_listener",
    "get_current_context",
    "get_event_bus",
    "get_event_monitor",
    "set_current_context",
    "trace",
    # Logging and metrics
    "get_logger",
    "logger",
    "BaseMemory",
    "MetricsCollector",
    # Plugin discovery
    "PluginInfo",
    "PluginLoadError",
    "PluginRegistry",
    "PluginValidationError",
    "create_provider_instance",
    "get_plugin_registry",
    # Helper functions
    "convert_to_dict",
    "flatten_dict",
    "format_string",
    "import_provider",
    "lazy_provider_class",
    "retry",
    "unflatten_dict",
]
