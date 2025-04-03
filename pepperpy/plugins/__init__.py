"""
PepperPy Plugin System.

This package contains the plugin system base class and abstractions,
plugin discovery and management, resource tracking, configuration
handling, and state persistence.
"""

import importlib.util
import sys
from typing import Any, Dict, List, Optional, Type, Union

# Base Plugins
from .plugin import (
    DependencyType,
    PepperpyPlugin,
    PluginStateManager,
    ProviderInterface,
    ProviderPlugin,
    get_state_manager,
)

# Import these modules only if they exist
try:
    # Plugin Registration (minimal imports to avoid errors)
    from .registry import (
        get_plugin,
        register_plugin,
    )
except ImportError:
    # Stub functions if not available
    def register_plugin(*args, **kwargs):
        """Stub for register_plugin."""
        pass

    def get_plugin(*args, **kwargs) -> Any:
        """Stub for get_plugin."""
        return None


try:
    # Enhanced Plugin Discovery
    from .discovery import (
        PluginDependency,
        PluginDiscoveryManager,
        PluginInfo,
        PluginSource,
        discover_plugins,
        register_scan_path,
    )
except ImportError:
    pass

try:
    # Lazy Loading
    from .lazy import (
        LazyPlugin,
        lazy_load,
    )
except ImportError:
    pass

try:
    # Validation
    from .validation import (
        PluginValidationResult,
        ValidationIssue,
        ValidationLevel,
        register_validator,
        validate_plugin,
    )
except ImportError:
    pass

try:
    # Resources
    from .resources import (
        ResourceAlreadyExistsError,
        ResourceError,
        ResourceNotFoundError,
        ResourceRegistry,
        ResourceType,
        async_scoped_resource,
        cleanup_owner_resources,
        cleanup_resource,
        get_resource,
        get_resource_metadata,
        get_resources_by_owner,
        get_resources_by_type,
        has_resource,
        register_resource,
        scoped_resource,
        unregister_resource,
    )
except ImportError:
    pass

try:
    # Dependencies
    from .dependencies import (
        CircularDependencyError,
        ConflictingDependencyError,
        DependencyError,
        MissingDependencyError,
        add_dependency,
        add_plugin,
        check_conflicts,
        check_missing_dependencies,
        get_conflicts_dependencies,
        get_dependencies,
        get_enhances_dependencies,
        get_load_order,
        get_optional_dependencies,
        get_required_dependencies,
        has_plugin,
        is_loaded,
        mark_loaded,
        resolve_dependencies,
    )
    from .dependencies import (
        DependencyType as _DepType,  # Avoid name collision
    )
except ImportError:
    pass

try:
    # Integration
    from .integration import (
        PluginManager,
        cleanup_all_plugins,
        cleanup_plugin,
        discover_and_register_plugins,
        get_plugin_manager,
        initialize_all_plugins,
        initialize_plugin,
    )
except ImportError:
    pass

try:
    # Resource Pooling
    from .resource_pool import (
        ResourcePool,
        ResourcePoolManager,
        get_resource_pool_manager,
    )
except ImportError:
    pass

try:
    # Event System
    from .events import (
        CoreEventType,
        EventContext,
        EventPriority,
        publish,
        subscribe,
        unsubscribe,
        unsubscribe_all,
    )
except ImportError:
    pass

try:
    # State Management
    from .state import (
        PluginState,
        StateTrackedPlugin,
        get_state,
        has_plugin,
        set_state,
    )
    from .state import (
        register_plugin as register_plugin_state,
    )
except ImportError:
    pass

try:
    # Service System
    from .services import (
        ServiceAccessError,
        ServiceError,
        ServiceNotFoundError,
        ServiceScope,
        await_service,
        call_service,
        get_service,
        get_service_metadata,
        has_service,
        list_providers,
        list_services,
        register_dependency,
        register_service,
        service,
        unregister_all_dependencies,
        unregister_all_services,
        unregister_dependency,
        unregister_service,
    )
except ImportError:
    pass

__all__ = [
    # Base Plugins
    "PepperpyPlugin",
    "ProviderInterface",
    "ProviderPlugin",
    "PluginStateManager",
    "get_state_manager",
    # Plugin Registration and Management
    "register_plugin",
    "get_plugin",
]

# Add additional exports if modules are available
if "lazy" in globals():
    __all__.extend(["LazyPlugin", "lazy_load"])

if "validation" in globals():
    __all__.extend(
        [
            "PluginValidationResult",
            "ValidationIssue",
            "ValidationLevel",
            "register_validator",
            "validate_plugin",
        ]
    )

if "discovery" in globals():
    __all__.extend(
        [
            "PluginDependency",
            "PluginDiscoveryManager",
            "PluginInfo",
            "PluginSource",
        ]
    )

if "resources" in globals():
    __all__.extend(
        [
            "ResourceType",
            "cleanup_resources",
            "get_resource",
            "register_resource",
        ]
    )

if "dependencies" in globals():
    __all__.extend(
        [
            "CircularDependencyError",
            "ConflictingDependencyError",
            "DependencyError",
            "DependencyType",
            "MissingDependencyError",
            "add_dependency",
            "add_plugin",
            "check_conflicts",
            "check_missing_dependencies",
            "get_dependencies",
            "get_load_order",
            "is_loaded",
            "mark_loaded",
            "resolve_dependencies",
        ]
    )

if "events" in globals():
    __all__.extend(
        [
            "CoreEventType",
            "EventContext",
            "EventPriority",
            "publish",
            "subscribe",
            "unsubscribe",
            "unsubscribe_all",
        ]
    )

if "services" in globals():
    __all__.extend(
        [
            "ServiceAccessError",
            "ServiceError",
            "ServiceNotFoundError",
            "ServiceScope",
            "await_service",
            "call_service",
            "get_service",
            "has_service",
            "list_providers",
            "list_services",
            "register_dependency",
            "register_service",
            "service",
            "unregister_dependency",
            "unregister_service",
        ]
    )
