"""
PepperPy Plugins Module.

This module provides plugin management and discovery for the PepperPy framework.
"""

# Import base interfaces and classes
# Import factory function
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
    create_provider_instance,
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

# Define __all__ without testing utilities initially
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

# Try to import testing utilities if available
try:
    from pepperpy.plugin.testing import PluginRunner, PluginTester

    __all__.extend(["PluginRunner", "PluginTester"])
except ImportError:
    # Testing module may not be available yet
    pass
