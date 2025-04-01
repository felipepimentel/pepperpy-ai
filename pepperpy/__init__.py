"""PepperPy Framework.

A modular framework for building AI applications with enhanced architecture.
"""

# Core components
from pepperpy.core import (
    # Base components
    BaseProvider,
    # Config management
    Config,
    ConfigRegistry,
    ConfigurationError,
    Container,
    # Event system
    Event,
    EventBus,
    EventType,
    NetworkError,
    # Errors
    PepperpyError,
    # Plugin discovery
    PluginInfo,
    PluginRegistry,
    PluginSource,
    ProviderError,
    # DI system
    ServiceLifetime,
    ValidationError,
    create_provider_instance,
    discover_plugins,
    emit_event,
    event_listener,
    get_config_registry,
    get_container,
    get_event_bus,
    # Logging
    get_logger,
    get_plugin,
    get_plugin_by_provider,
    get_plugin_registry,
)

# Import initialization function
from pepperpy.init import init_framework

# Domain-specific providers
from pepperpy.llm import LLMProvider, Message, MessageRole
from pepperpy.pepperpy import PepperPy
from pepperpy.plugins import ProviderPlugin, install_plugin_dependencies

__version__ = "0.1.0"

__all__ = [
    # Core components
    "BaseProvider",
    "PepperpyError",
    "ValidationError",
    "ConfigurationError",
    "ProviderError",
    "NetworkError",
    # DI system
    "ServiceLifetime",
    "Container",
    "get_container",
    "inject",
    # Plugin system
    "PluginInfo",
    "PluginRegistry",
    "PluginSource",
    "create_provider_instance",
    "discover_plugins",
    "get_plugin",
    "get_plugin_by_provider",
    "get_plugin_registry",
    # Event system
    "Event",
    "EventBus",
    "EventType",
    "get_event_bus",
    "event_listener",
    "emit_event",
    # Config management
    "Config",
    "ConfigRegistry",
    "get_config_registry",
    # Domain providers
    "LLMProvider",
    "Message",
    "MessageRole",
    "PepperPy",
    "ProviderPlugin",
    # Utility functions
    "get_logger",
    "install_plugin_dependencies",
]
