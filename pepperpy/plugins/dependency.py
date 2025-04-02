"""Plugin dependency management for PepperPy.

This module provides tools for managing dependencies between plugins,
including a dependency graph, automatic loading, and proper shutdown ordering.
"""

from collections import defaultdict
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from pepperpy.core.errors import ConfigurationError, ProviderError
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)


class DependencyType(Enum):
    """Types of dependencies between plugins."""

    # Required dependency - plugin won't function without it
    REQUIRED = "required"

    # Optional dependency - plugin can function without it
    OPTIONAL = "optional"

    # Runtime dependency - needed during runtime but not initialization
    RUNTIME = "runtime"

    # Enhances dependency - adds functionality to the dependent plugin
    ENHANCES = "enhances"


class DependencyGraph:
    """Graph representing dependencies between plugins."""

    def __init__(self) -> None:
        """Initialize the dependency graph."""
        # Format: {(plugin_type, provider_type): {(dep_plugin_type, dep_provider_type): DependencyType}}
        self._dependencies: Dict[
            Tuple[str, str], Dict[Tuple[str, str], DependencyType]
        ] = defaultdict(dict)

        # Reverse dependencies for quick lookups
        # Format: {(plugin_type, provider_type): {(dependent_type, dependent_provider): DependencyType}}
        self._reverse_dependencies: Dict[
            Tuple[str, str], Dict[Tuple[str, str], DependencyType]
        ] = defaultdict(dict)

        # Cache of sorted dependencies
        self._sorted_dependencies: Optional[List[Tuple[str, str]]] = None

        # Set to track if graph has changed
        self._graph_changed = False

    def add_dependency(
        self,
        plugin_type: str,
        provider_type: str,
        depends_on_type: str,
        depends_on_provider: str,
        dependency_type: DependencyType = DependencyType.REQUIRED,
    ) -> None:
        """Add a dependency to the graph.

        Args:
            plugin_type: Type of the dependent plugin
            provider_type: Provider of the dependent plugin
            depends_on_type: Type of the dependency plugin
            depends_on_provider: Provider of the dependency plugin
            dependency_type: Type of dependency relationship
        """
        plugin_key = (plugin_type, provider_type)
        dependency_key = (depends_on_type, depends_on_provider)

        # Add to dependencies dict
        self._dependencies[plugin_key][dependency_key] = dependency_type

        # Add to reverse dependencies dict for faster lookups
        self._reverse_dependencies[dependency_key][plugin_key] = dependency_type

        # Mark graph as changed
        self._graph_changed = True
        self._sorted_dependencies = None

        logger.debug(
            f"Added dependency: {plugin_type}/{provider_type} -> "
            f"{depends_on_type}/{depends_on_provider} ({dependency_type.value})"
        )

    def remove_dependency(
        self,
        plugin_type: str,
        provider_type: str,
        depends_on_type: str,
        depends_on_provider: str,
    ) -> bool:
        """Remove a dependency from the graph.

        Args:
            plugin_type: Type of the dependent plugin
            provider_type: Provider of the dependent plugin
            depends_on_type: Type of the dependency plugin
            depends_on_provider: Provider of the dependency plugin

        Returns:
            True if dependency was removed, False if it didn't exist
        """
        plugin_key = (plugin_type, provider_type)
        dependency_key = (depends_on_type, depends_on_provider)

        # Check if dependency exists
        if dependency_key not in self._dependencies.get(plugin_key, {}):
            return False

        # Remove from dependencies dict
        del self._dependencies[plugin_key][dependency_key]

        # Remove from reverse dependencies dict
        del self._reverse_dependencies[dependency_key][plugin_key]

        # Clean up empty dicts
        if not self._dependencies[plugin_key]:
            del self._dependencies[plugin_key]

        if not self._reverse_dependencies[dependency_key]:
            del self._reverse_dependencies[dependency_key]

        # Mark graph as changed
        self._graph_changed = True
        self._sorted_dependencies = None

        logger.debug(
            f"Removed dependency: {plugin_type}/{provider_type} -> "
            f"{depends_on_type}/{depends_on_provider}"
        )
        return True

    def get_dependencies(
        self,
        plugin_type: str,
        provider_type: str,
        dependency_type: Optional[DependencyType] = None,
    ) -> List[Tuple[str, str]]:
        """Get all dependencies of a plugin.

        Args:
            plugin_type: Type of the plugin
            provider_type: Provider of the plugin
            dependency_type: Optional filter by dependency type

        Returns:
            List of (plugin_type, provider_type) tuples that the plugin depends on
        """
        plugin_key = (plugin_type, provider_type)
        dependencies = self._dependencies.get(plugin_key, {})

        if dependency_type:
            return [
                dep_key
                for dep_key, dep_type in dependencies.items()
                if dep_type == dependency_type
            ]

        return list(dependencies.keys())

    def get_dependents(
        self,
        plugin_type: str,
        provider_type: str,
        dependency_type: Optional[DependencyType] = None,
    ) -> List[Tuple[str, str]]:
        """Get all plugins that depend on this plugin.

        Args:
            plugin_type: Type of the plugin
            provider_type: Provider of the plugin
            dependency_type: Optional filter by dependency type

        Returns:
            List of (plugin_type, provider_type) tuples that depend on this plugin
        """
        plugin_key = (plugin_type, provider_type)
        dependents = self._reverse_dependencies.get(plugin_key, {})

        if dependency_type:
            return [
                dep_key
                for dep_key, dep_type in dependents.items()
                if dep_type == dependency_type
            ]

        return list(dependents.keys())

    def has_dependency(
        self,
        plugin_type: str,
        provider_type: str,
        depends_on_type: str,
        depends_on_provider: str,
    ) -> bool:
        """Check if a plugin depends on another plugin.

        Args:
            plugin_type: Type of the dependent plugin
            provider_type: Provider of the dependent plugin
            depends_on_type: Type of the dependency plugin
            depends_on_provider: Provider of the dependency plugin

        Returns:
            True if the dependency exists, False otherwise
        """
        plugin_key = (plugin_type, provider_type)
        dependency_key = (depends_on_type, depends_on_provider)

        return dependency_key in self._dependencies.get(plugin_key, {})

    def get_dependency_type(
        self,
        plugin_type: str,
        provider_type: str,
        depends_on_type: str,
        depends_on_provider: str,
    ) -> Optional[DependencyType]:
        """Get the type of dependency between two plugins.

        Args:
            plugin_type: Type of the dependent plugin
            provider_type: Provider of the dependent plugin
            depends_on_type: Type of the dependency plugin
            depends_on_provider: Provider of the dependency plugin

        Returns:
            DependencyType if the dependency exists, None otherwise
        """
        plugin_key = (plugin_type, provider_type)
        dependency_key = (depends_on_type, depends_on_provider)

        return self._dependencies.get(plugin_key, {}).get(dependency_key)

    def topological_sort(self) -> List[Tuple[str, str]]:
        """Sort plugins by dependencies for initialization order.

        This implements a topological sort of the dependency graph.

        Returns:
            List of (plugin_type, provider_type) tuples in dependency order

        Raises:
            ProviderError: If there's a circular dependency
        """
        # Use cached result if available and graph hasn't changed
        if not self._graph_changed and self._sorted_dependencies is not None:
            return self._sorted_dependencies

        # Dictionary tracking visited and temporary markers
        # 0 = unvisited, 1 = temporary mark, 2 = permanent mark
        markers: Dict[Tuple[str, str], int] = {}

        # Result list
        result: List[Tuple[str, str]] = []

        # All nodes in the graph
        all_nodes: Set[Tuple[str, str]] = set(self._dependencies.keys())
        for deps in self._dependencies.values():
            all_nodes.update(deps.keys())

        # Setup all nodes as unvisited
        for node in all_nodes:
            markers[node] = 0

        # Recursive visit function
        def visit(node: Tuple[str, str], path: List[Tuple[str, str]]) -> None:
            if markers[node] == 2:
                # Already permanently marked, skip
                return

            if markers[node] == 1:
                # Temporary mark means we've detected a cycle
                cycle_path = " -> ".join([f"{t}/{p}" for t, p in path + [node]])
                raise ProviderError(f"Circular dependency detected: {cycle_path}")

            # Mark temporarily
            markers[node] = 1

            # Visit all dependencies
            for dependency in self._dependencies.get(node, {}):
                visit(dependency, path + [node])

            # Mark permanently and add to result
            markers[node] = 2
            result.append(node)

        # Visit all unvisited nodes
        for node in all_nodes:
            if markers[node] == 0:
                visit(node, [])

        # Reverse to get correct initialization order
        self._sorted_dependencies = list(reversed(result))
        self._graph_changed = False

        return self._sorted_dependencies

    def reverse_topological_sort(self) -> List[Tuple[str, str]]:
        """Sort plugins by dependencies for shutdown order.

        This returns the reversed topological sort, which is the proper
        order for shutting down plugins.

        Returns:
            List of (plugin_type, provider_type) tuples in shutdown order
        """
        return list(reversed(self.topological_sort()))

    def verify_graph(self) -> bool:
        """Verify that the dependency graph has no circular dependencies.

        Returns:
            True if the graph is valid, False otherwise

        Raises:
            ProviderError: If there's a circular dependency
        """
        try:
            self.topological_sort()
            return True
        except ProviderError:
            return False

    def __contains__(self, item: Tuple[str, str]) -> bool:
        """Check if a plugin is in the dependency graph.

        Args:
            item: Tuple of (plugin_type, provider_type)

        Returns:
            True if the plugin is in the graph, False otherwise
        """
        return item in self._dependencies or any(
            item in deps for deps in self._dependencies.values()
        )

    def __len__(self) -> int:
        """Get the number of plugins in the dependency graph.

        Returns:
            Number of plugins
        """
        all_nodes: Set[Tuple[str, str]] = set(self._dependencies.keys())
        for deps in self._dependencies.values():
            all_nodes.update(deps.keys())
        return len(all_nodes)


class DependencyManager:
    """Manager for plugin dependencies."""

    def __init__(self) -> None:
        """Initialize the dependency manager."""
        self._graph = DependencyGraph()
        self._plugin_metadata: Dict[Tuple[str, str], Dict[str, Any]] = {}

    def register_plugin_metadata(
        self, plugin_type: str, provider_type: str, metadata: Dict[str, Any]
    ) -> None:
        """Register plugin metadata including dependencies.

        Args:
            plugin_type: Type of the plugin
            provider_type: Provider of the plugin
            metadata: Plugin metadata including dependencies
        """
        plugin_key = (plugin_type, provider_type)
        self._plugin_metadata[plugin_key] = metadata

        # Process dependencies if specified
        dependencies = metadata.get("dependencies", [])
        for dependency in dependencies:
            dep_type = dependency.get("type")
            dep_provider = dependency.get("provider")
            dep_dependency_type = DependencyType(
                dependency.get("dependency_type", "required")
            )

            if dep_type and dep_provider:
                self._graph.add_dependency(
                    plugin_type,
                    provider_type,
                    dep_type,
                    dep_provider,
                    dep_dependency_type,
                )

    def get_initialization_order(self) -> List[Tuple[str, str]]:
        """Get the proper initialization order for plugins.

        Returns:
            List of (plugin_type, provider_type) tuples in dependency order
        """
        return self._graph.topological_sort()

    def get_shutdown_order(self) -> List[Tuple[str, str]]:
        """Get the proper shutdown order for plugins.

        Returns:
            List of (plugin_type, provider_type) tuples in shutdown order
        """
        return self._graph.reverse_topological_sort()

    def get_missing_dependencies(
        self,
        plugin_type: str,
        provider_type: str,
        available_plugins: Set[Tuple[str, str]],
    ) -> List[Tuple[str, str]]:
        """Get missing required dependencies for a plugin.

        Args:
            plugin_type: Type of the plugin
            provider_type: Provider of the plugin
            available_plugins: Set of available (plugin_type, provider_type) tuples

        Returns:
            List of missing required dependencies
        """
        required_deps = self._graph.get_dependencies(
            plugin_type, provider_type, DependencyType.REQUIRED
        )

        return [dep for dep in required_deps if dep not in available_plugins]

    def verify_dependencies(
        self, available_plugins: Set[Tuple[str, str]]
    ) -> Dict[Tuple[str, str], List[Tuple[str, str]]]:
        """Verify that all required dependencies are available.

        Args:
            available_plugins: Set of available (plugin_type, provider_type) tuples

        Returns:
            Dictionary mapping plugins to their missing dependencies
        """
        missing_dependencies: Dict[Tuple[str, str], List[Tuple[str, str]]] = {}

        for plugin_key in self._plugin_metadata:
            missing = self.get_missing_dependencies(
                plugin_key[0], plugin_key[1], available_plugins
            )

            if missing:
                missing_dependencies[plugin_key] = missing

        return missing_dependencies


# Global dependency manager instance
_dependency_manager: Optional[DependencyManager] = None


def get_dependency_manager() -> DependencyManager:
    """Get the global dependency manager.

    Returns:
        DependencyManager instance
    """
    global _dependency_manager
    if _dependency_manager is None:
        _dependency_manager = DependencyManager()

    return _dependency_manager


async def load_dependencies(
    plugin_type: str, provider_type: str, plugin_manager
) -> List[Tuple[str, str]]:
    """Load all dependencies for a plugin.

    Args:
        plugin_type: Type of the plugin
        provider_type: Provider of the plugin
        plugin_manager: Plugin manager instance

    Returns:
        List of loaded dependencies

    Raises:
        ConfigurationError: If a required dependency can't be loaded
    """
    dependency_manager = get_dependency_manager()
    loaded_dependencies: List[Tuple[str, str]] = []

    # Get all dependencies
    dependencies = dependency_manager._graph.get_dependencies(
        plugin_type, provider_type
    )

    # Load each dependency
    for dep_type, dep_provider in dependencies:
        dependency_type = dependency_manager._graph.get_dependency_type(
            plugin_type, provider_type, dep_type, dep_provider
        )

        try:
            # Check if already loaded
            instance = plugin_manager.get_instance(dep_type, dep_provider)
            if instance is None:
                # Create and initialize the instance
                instance = plugin_manager.create_instance(dep_type, dep_provider)
                await instance.initialize()

            loaded_dependencies.append((dep_type, dep_provider))

        except Exception as e:
            # For required dependencies, propagate the error
            if dependency_type == DependencyType.REQUIRED:
                raise ConfigurationError(
                    f"Failed to load required dependency {dep_type}/{dep_provider} "
                    f"for {plugin_type}/{provider_type}: {e}"
                ) from e
            else:
                # For optional dependencies, just log the error
                logger.warning(
                    f"Failed to load optional dependency {dep_type}/{dep_provider} "
                    f"for {plugin_type}/{provider_type}: {e}"
                )

    return loaded_dependencies
