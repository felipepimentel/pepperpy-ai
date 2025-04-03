"""Dependencies management for PepperPy plugins.

This module provides dependency resolution and management for plugins,
allowing plugins to declare dependencies on other plugins.
"""

from enum import Enum
from typing import Dict, List, Set, TypeVar

from pepperpy.core.errors import PluginError
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class DependencyType(Enum):
    """Types of dependencies between plugins."""

    # Required dependency - plugin won't function without it
    REQUIRED = "required"

    # Optional dependency - plugin can function without it
    OPTIONAL = "optional"

    # Enhances dependency - plugin is enhanced by this dependency
    ENHANCES = "enhances"

    # Conflicts dependency - plugin cannot function with this dependency
    CONFLICTS = "conflicts"


class DependencyError(PluginError):
    """Error raised during dependency resolution."""

    pass


class CircularDependencyError(DependencyError):
    """Error raised when a circular dependency is detected."""

    def __init__(self, cycle: List[str]):
        """Initialize circular dependency error.

        Args:
            cycle: List of plugin IDs forming the cycle
        """
        cycle_str = " -> ".join(cycle)
        super().__init__(f"Circular dependency detected: {cycle_str}")
        self.cycle = cycle


class MissingDependencyError(DependencyError):
    """Error raised when a required dependency is missing."""

    def __init__(self, plugin_id: str, dependency_id: str):
        """Initialize missing dependency error.

        Args:
            plugin_id: ID of the plugin with missing dependency
            dependency_id: ID of the missing dependency
        """
        super().__init__(
            f"Missing required dependency: {plugin_id} requires {dependency_id}",
            plugin_id=plugin_id,
        )
        self.dependency_id = dependency_id


class ConflictingDependencyError(DependencyError):
    """Error raised when a conflicting dependency is detected."""

    def __init__(self, plugin_id: str, conflict_id: str):
        """Initialize conflicting dependency error.

        Args:
            plugin_id: ID of the plugin with conflicting dependency
            conflict_id: ID of the conflicting dependency
        """
        super().__init__(
            f"Conflicting dependency: {plugin_id} conflicts with {conflict_id}",
            plugin_id=plugin_id,
        )
        self.conflict_id = conflict_id


# Registry of plugin dependencies
_dependencies: Dict[str, Dict[str, DependencyType]] = {}

# Registry of loaded plugins
_loaded_plugins: Set[str] = set()

# Registry of plugins waiting to be loaded
_registered_plugins: Set[str] = set()


def add_dependency(
    plugin_id: str,
    dependency_id: str,
    dependency_type: DependencyType = DependencyType.REQUIRED,
) -> None:
    """Add a dependency between plugins.

    Args:
        plugin_id: ID of the dependent plugin
        dependency_id: ID of the dependency plugin
        dependency_type: Type of dependency

    Raises:
        ValueError: If plugin_id or dependency_id is empty
    """
    if not plugin_id:
        raise ValueError("plugin_id must not be empty")
    if not dependency_id:
        raise ValueError("dependency_id must not be empty")

    # Initialize dependency dictionary if needed
    if plugin_id not in _dependencies:
        _dependencies[plugin_id] = {}

    # Add dependency
    _dependencies[plugin_id][dependency_id] = dependency_type
    logger.debug(
        f"Added {dependency_type.value} dependency: {plugin_id} -> {dependency_id}"
    )


def add_plugin(plugin_id: str) -> None:
    """Register a plugin in the dependency system.

    Args:
        plugin_id: ID of the plugin

    Raises:
        ValueError: If plugin_id is empty
    """
    if not plugin_id:
        raise ValueError("plugin_id must not be empty")

    _registered_plugins.add(plugin_id)
    logger.debug(f"Registered plugin in dependency system: {plugin_id}")


def mark_loaded(plugin_id: str) -> None:
    """Mark a plugin as loaded.

    Args:
        plugin_id: ID of the plugin

    Raises:
        ValueError: If plugin_id is empty
    """
    if not plugin_id:
        raise ValueError("plugin_id must not be empty")

    _loaded_plugins.add(plugin_id)
    logger.debug(f"Marked plugin as loaded: {plugin_id}")


def has_plugin(plugin_id: str) -> bool:
    """Check if a plugin is registered.

    Args:
        plugin_id: ID of the plugin

    Returns:
        True if the plugin is registered, False otherwise
    """
    return plugin_id in _registered_plugins


def is_loaded(plugin_id: str) -> bool:
    """Check if a plugin is loaded.

    Args:
        plugin_id: ID of the plugin

    Returns:
        True if the plugin is loaded, False otherwise
    """
    return plugin_id in _loaded_plugins


def get_dependencies(plugin_id: str) -> Dict[str, DependencyType]:
    """Get all dependencies for a plugin.

    Args:
        plugin_id: ID of the plugin

    Returns:
        Dictionary of dependency IDs to dependency types
    """
    return _dependencies.get(plugin_id, {})


def get_required_dependencies(plugin_id: str) -> List[str]:
    """Get required dependencies for a plugin.

    Args:
        plugin_id: ID of the plugin

    Returns:
        List of required dependency IDs
    """
    dependencies = get_dependencies(plugin_id)
    return [
        dep_id
        for dep_id, dep_type in dependencies.items()
        if dep_type == DependencyType.REQUIRED
    ]


def get_optional_dependencies(plugin_id: str) -> List[str]:
    """Get optional dependencies for a plugin.

    Args:
        plugin_id: ID of the plugin

    Returns:
        List of optional dependency IDs
    """
    dependencies = get_dependencies(plugin_id)
    return [
        dep_id
        for dep_id, dep_type in dependencies.items()
        if dep_type == DependencyType.OPTIONAL
    ]


def get_enhances_dependencies(plugin_id: str) -> List[str]:
    """Get enhances dependencies for a plugin.

    Args:
        plugin_id: ID of the plugin

    Returns:
        List of enhances dependency IDs
    """
    dependencies = get_dependencies(plugin_id)
    return [
        dep_id
        for dep_id, dep_type in dependencies.items()
        if dep_type == DependencyType.ENHANCES
    ]


def get_conflicts_dependencies(plugin_id: str) -> List[str]:
    """Get conflicts dependencies for a plugin.

    Args:
        plugin_id: ID of the plugin

    Returns:
        List of conflicts dependency IDs
    """
    dependencies = get_dependencies(plugin_id)
    return [
        dep_id
        for dep_id, dep_type in dependencies.items()
        if dep_type == DependencyType.CONFLICTS
    ]


def get_dependents(plugin_id: str) -> List[str]:
    """Get plugins that depend on a plugin.

    Args:
        plugin_id: ID of the plugin

    Returns:
        List of dependent plugin IDs
    """
    return [
        p_id
        for p_id, deps in _dependencies.items()
        if plugin_id in deps
        and deps[plugin_id] in [DependencyType.REQUIRED, DependencyType.OPTIONAL]
    ]


def get_enhancers(plugin_id: str) -> List[str]:
    """Get plugins that enhance a plugin.

    Args:
        plugin_id: ID of the plugin

    Returns:
        List of enhancer plugin IDs
    """
    return [
        p_id
        for p_id, deps in _dependencies.items()
        if plugin_id in deps and deps[plugin_id] == DependencyType.ENHANCES
    ]


def get_conflicts(plugin_id: str) -> List[str]:
    """Get plugins that conflict with a plugin.

    Args:
        plugin_id: ID of the plugin

    Returns:
        List of conflicting plugin IDs
    """
    return [
        p_id
        for p_id, deps in _dependencies.items()
        if plugin_id in deps and deps[plugin_id] == DependencyType.CONFLICTS
    ]


def check_missing_dependencies(plugin_id: str) -> List[str]:
    """Check for missing required dependencies.

    Args:
        plugin_id: ID of the plugin

    Returns:
        List of missing required dependency IDs
    """
    if plugin_id not in _dependencies:
        return []

    return [
        dep_id
        for dep_id, dep_type in _dependencies[plugin_id].items()
        if dep_type == DependencyType.REQUIRED and dep_id not in _registered_plugins
    ]


def check_conflicts(plugin_id: str) -> List[str]:
    """Check for conflicting dependencies.

    Args:
        plugin_id: ID of the plugin

    Returns:
        List of conflicting plugin IDs that are registered
    """
    if plugin_id not in _dependencies:
        return []

    return [
        dep_id
        for dep_id, dep_type in _dependencies[plugin_id].items()
        if dep_type == DependencyType.CONFLICTS and dep_id in _registered_plugins
    ]


def resolve_dependencies(plugin_id: str) -> List[str]:
    """Resolve dependencies for a plugin in load order.

    Args:
        plugin_id: ID of the plugin

    Returns:
        List of plugin IDs in order of loading

    Raises:
        MissingDependencyError: If a required dependency is missing
        ConflictingDependencyError: If a conflicting dependency is detected
        CircularDependencyError: If a circular dependency is detected
    """
    # Check for missing dependencies
    missing = check_missing_dependencies(plugin_id)
    if missing:
        raise MissingDependencyError(plugin_id, missing[0])

    # Check for conflicts
    conflicts = check_conflicts(plugin_id)
    if conflicts:
        raise ConflictingDependencyError(plugin_id, conflicts[0])

    # Perform topological sort
    return _topological_sort(plugin_id)


def _topological_sort(plugin_id: str) -> List[str]:
    """Perform topological sort on dependencies.

    Args:
        plugin_id: Starting plugin ID

    Returns:
        List of plugin IDs in dependency order

    Raises:
        CircularDependencyError: If a circular dependency is detected
    """
    # Initialize result and visited sets
    result: List[str] = []
    visited: Set[str] = set()
    temp_visited: Set[str] = set()

    def visit(node: str, path: List[str]) -> None:
        """Visit a node in the dependency graph.

        Args:
            node: Plugin ID to visit
            path: Current path in the graph

        Raises:
            CircularDependencyError: If a circular dependency is detected
        """
        # Check for circular dependency
        if node in temp_visited:
            cycle = path[path.index(node) :] + [node]
            raise CircularDependencyError(cycle)

        # Skip if already visited
        if node in visited:
            return

        # Mark as temporarily visited
        temp_visited.add(node)
        path.append(node)

        # Visit dependencies
        dependencies = get_required_dependencies(node)
        for dep in dependencies:
            if dep in _registered_plugins:  # Only visit registered plugins
                visit(dep, path)

        # Mark as visited and add to result
        temp_visited.remove(node)
        visited.add(node)
        result.append(node)

    # Start visiting from the given plugin
    visit(plugin_id, [])

    # Add optional dependencies that are not already in the result
    optional_deps = get_optional_dependencies(plugin_id) + get_enhances_dependencies(
        plugin_id
    )
    for dep in optional_deps:
        if dep in _registered_plugins and dep not in result:
            result.append(dep)

    return result


def get_load_order(plugin_ids: List[str]) -> List[str]:
    """Get the load order for a list of plugins.

    Args:
        plugin_ids: List of plugin IDs

    Returns:
        List of plugin IDs in order of loading

    Raises:
        MissingDependencyError: If a required dependency is missing
        ConflictingDependencyError: If a conflicting dependency is detected
        CircularDependencyError: If a circular dependency is detected
    """
    # Check all plugins for missing dependencies and conflicts
    for plugin_id in plugin_ids:
        missing = check_missing_dependencies(plugin_id)
        if missing:
            raise MissingDependencyError(plugin_id, missing[0])

        conflicts = check_conflicts(plugin_id)
        if conflicts:
            raise ConflictingDependencyError(plugin_id, conflicts[0])

    # Initialize result
    result: List[str] = []
    visited: Set[str] = set()

    # Visit all plugins
    for plugin_id in plugin_ids:
        if plugin_id not in visited:
            # Get dependencies for this plugin
            deps = resolve_dependencies(plugin_id)

            # Add to result if not already present
            for dep in deps:
                if dep not in result:
                    result.append(dep)

            # Mark as visited
            visited.add(plugin_id)

    return result
