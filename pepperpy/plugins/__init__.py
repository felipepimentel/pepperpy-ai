"""Plugin system for PepperPy.

This package provides the plugin system for PepperPy, including:
- Plugin base class and abstractions
- Plugin discovery and management
- Resource tracking and cleanup
- Configuration handling
"""

import importlib
import os
import sys
from typing import Type

from pepperpy.core.logging import get_logger
from pepperpy.plugins.core import (
    PluginError,
    PluginInfo,
    PluginSource,
    create_provider_instance,
    discover_plugins,
    get_plugin,
    get_plugin_metadata,
    get_plugins_by_type,
    list_plugin_types,
    list_plugins,
    load_plugin,
    register_plugin,
)
from pepperpy.plugins.plugin import PepperpyPlugin, auto_context, auto_initialize

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
    "get_plugin",
    "get_plugin_metadata",
    "get_plugins_by_type",
    "list_plugins",
    "list_plugin_types",
    "load_plugin",
    "register_plugin",
]
