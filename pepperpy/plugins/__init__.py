"""Plugin system for PepperPy.

This package provides the plugin system for PepperPy, including:
- Plugin base class and abstractions
- Plugin discovery and management
- Resource tracking and cleanup
- Configuration handling
- State persistence and hot-reloading
"""

import importlib
import os
import sys
from typing import Type, Dict, List, Any, Optional

from pepperpy.core.logging import get_logger
from pepperpy.plugins.extensions import (
    extended_plugin,
    hot_reloadable_plugin,
    persistent_plugin,
    start_hot_reload,
    stop_hot_reload,
)
from pepperpy.plugins.plugin import PepperpyPlugin, auto_context, auto_initialize
from pepperpy.plugins.registry import (
    PluginError,
    PluginInfo,
    PluginSource,
    clear_path_cache,
    create_provider_instance,
    discover_plugins,
    ensure_discovery_initialized,
    find_fallback,
    get_plugin,
    get_plugin_metadata,
    get_plugins_by_type,
    initialize_discovery,
    list_plugin_types,
    list_plugins,
    load_plugin,
    register_plugin,
    register_plugin_alias,
    register_plugin_fallbacks,
    register_plugin_path,
)
from pepperpy.plugins.resources import (
    ResourceMixin,
    ResourcePool,
    cleanup_all_resources,
    get_resource_pool,
)

logger = get_logger(__name__)

__all__ = [
    # Plugin abstractions
    "PepperpyPlugin",
    "PluginError",
    "PluginInfo",
    "PluginSource",
    "auto_context",
    "auto_initialize",
    
    # Discovery and management
    "create_provider_instance",
    "discover_plugins",
    "ensure_discovery_initialized",
    "find_fallback",
    "get_plugin",
    "get_plugin_metadata",
    "get_plugins_by_type",
    "initialize_discovery",
    "list_plugins",
    "list_plugin_types",
    "load_plugin",
    "register_plugin",
    
    # Advanced plugin registry management
    "register_plugin_path",
    "register_plugin_alias",
    "register_plugin_fallbacks",
    "clear_path_cache",
    
    # Resource management
    "ResourceMixin",
    "ResourcePool",
    "cleanup_all_resources",
    "get_resource_pool",
    
    # Extensions
    "extended_plugin",
    "hot_reloadable_plugin",
    "persistent_plugin",
    "start_hot_reload",
    "stop_hot_reload",
]
