"""Hub system for PepperPy.

This module provides a central hub for managing and sharing components in the PepperPy framework:
- Component registry: Register and discover components
- Artifact storage: Store and retrieve artifacts
- Version management: Track component versions and dependencies
- Security: Control access to components and artifacts

The hub system enables the framework to maintain a catalog of available components,
facilitating discovery, sharing, and reuse across projects.
"""

from pepperpy.hub.base import HubArtifact, HubInterface
from pepperpy.hub.discovery import (
    ComponentDiscovery,
    discover_components_in_module,
    discover_components_in_package,
    discover_components_in_path,
    discover_local_components,
)
from pepperpy.hub.manager import HubManager
from pepperpy.hub.registration import (
    Component,
    ComponentRegistry,
    ComponentType,
    get_all_components,
    get_component,
    get_component_by_name,
    get_components_by_type,
    register_component,
    unregister_component,
)

# Export public API
__all__ = [
    "Component",
    "ComponentDiscovery",
    "ComponentRegistry",
    "ComponentType",
    "HubArtifact",
    "HubInterface",
    "HubManager",
    "discover_components_in_module",
    "discover_components_in_package",
    "discover_components_in_path",
    "discover_local_components",
    "get_all_components",
    "get_component",
    "get_component_by_name",
    "get_components_by_type",
    "register_component",
    "unregister_component",
]
