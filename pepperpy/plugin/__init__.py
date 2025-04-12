"""
PepperPy Plugins Module.

This module provides plugin management and discovery for the PepperPy framework.
"""

# Import base interfaces and classes
from pepperpy.plugin.base import (
    PepperpyPlugin,
    PluginDiscoveryProtocol,
    PluginError,
    PluginInfo,
    PluginMetadata,
    PluginNotFoundError,
    ResourceError,
    ResourceMixin,
    ResourceType,
)

# Import discovery functions
from pepperpy.plugin.discovery import (
    DiscoveryError,
    discover_plugins,
    load_plugin,
)

# Import ProviderPlugin from plugin.py
from pepperpy.plugin.plugin import ProviderPlugin

# Import provider base class
from pepperpy.plugin.provider import BasePluginProvider

# Import registry functions
from pepperpy.plugin.registry import (
    get_plugin,
    get_plugin_metadata,
    list_plugins,
    register_plugin,
)

__all__ = [
    # Base interfaces and classes
    "PepperpyPlugin",
    "PluginDiscoveryProtocol",
    "PluginError",
    "PluginInfo",
    "PluginMetadata",
    "PluginNotFoundError",
    "ResourceError",
    "ResourceMixin",
    "ResourceType",
    # Registry functions
    "get_plugin",
    "get_plugin_metadata",
    "list_plugins",
    "register_plugin",
    # Discovery functions
    "DiscoveryError",
    "discover_plugins",
    "load_plugin",
    # Provider base class
    "BasePluginProvider",
    # Provider plugin alias
    "ProviderPlugin",
    # Factory function
    "create_provider_instance",
]

# Factory function
from pepperpy.plugin.base import create_provider_instance

__all__.append("create_provider_instance")
