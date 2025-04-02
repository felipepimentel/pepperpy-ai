"""Plugin manager for PepperPy.

This module provides enhanced plugin management for PepperPy, including
dependency resolution, instance management, and lifecycle coordination.
"""

import os
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from pepperpy.core.errors import ConfigurationError, ValidationError
from pepperpy.core.logging import get_logger
from pepperpy.plugins.plugin import PepperpyPlugin
from pepperpy.plugins.registry import get_plugin

logger = get_logger(__name__)

# Track if dotenv has been loaded
_dotenv_loaded = False


def _ensure_dotenv_loaded() -> None:
    """Ensure dotenv is loaded.

    This function tries to load environment variables from .env files
    at different locations. It's a no-op if dotenv has been loaded before.
    """
    global _dotenv_loaded
    if _dotenv_loaded:
        return

    try:
        # Try to import dotenv
        try:
            from dotenv import load_dotenv
        except ImportError:
            logger.debug("python-dotenv not installed, will not load .env files")
            _dotenv_loaded = True
            return

        # List of potential .env file locations to try
        env_files = [
            os.path.join(os.getcwd(), ".env"),  # Current directory
            os.path.join(os.path.expanduser("~"), ".pepperpy", ".env"),  # User config
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)), ".env"
            ),  # Project root
        ]

        # Try to load from each location
        for env_file in env_files:
            if os.path.exists(env_file):
                logger.debug(f"Loading environment from {env_file}")
                load_dotenv(env_file)

        # Also check for .env file in parent directories up to 3 levels
        current_dir = Path.cwd()
        for _ in range(3):
            parent_dir = current_dir.parent
            if parent_dir == current_dir:  # Reached filesystem root
                break

            env_file = parent_dir / ".env"
            if env_file.exists():
                logger.debug(f"Loading environment from {env_file}")
                load_dotenv(str(env_file))

            current_dir = parent_dir

        _dotenv_loaded = True
    except Exception as e:
        logger.warning(f"Failed to load environment variables from .env files: {e}")
        _dotenv_loaded = True  # Prevent further attempts


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


@dataclass
class PluginInfo:
    """Information about a plugin."""

    name: str
    version: str
    description: str
    author: str
    license: str
    homepage: Optional[str] = None
    repository: Optional[str] = None
    documentation: Optional[str] = None
    dependencies: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


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

    def get_dependency_type(
        self,
        plugin_type: str,
        provider_type: str,
        depends_on_type: str,
        depends_on_provider: str,
    ) -> Optional[DependencyType]:
        """Get the dependency type between two plugins.

        Args:
            plugin_type: Type of the dependent plugin
            provider_type: Provider of the dependent plugin
            depends_on_type: Type of the dependency plugin
            depends_on_provider: Provider of the dependency plugin

        Returns:
            Dependency type if dependency exists, None otherwise
        """
        plugin_key = (plugin_type, provider_type)
        dependency_key = (depends_on_type, depends_on_provider)
        return self._dependencies.get(plugin_key, {}).get(dependency_key)

    def topological_sort(self) -> List[Tuple[str, str]]:
        """Sort plugins in dependency order (dependencies first).

        Returns:
            List of (plugin_type, provider_type) tuples in dependency order
        """
        # Use cached result if graph hasn't changed
        if not self._graph_changed and self._sorted_dependencies is not None:
            return self._sorted_dependencies.copy()

        # Get all nodes in the graph (both plugins and dependencies)
        all_nodes: Set[Tuple[str, str]] = set()
        for plugin_key, dependencies in self._dependencies.items():
            all_nodes.add(plugin_key)
            all_nodes.update(dependencies.keys())

        # Prepare result and visited sets
        sorted_nodes: List[Tuple[str, str]] = []
        visited: Set[Tuple[str, str]] = set()
        temp_visited: Set[Tuple[str, str]] = set()

        def visit(node: Tuple[str, str]) -> None:
            """Visit a node in the graph.

            Args:
                node: Node to visit
            """
            if node in visited:
                return

            if node in temp_visited:
                # Circular dependency detected
                cycle = (
                    " -> ".join(f"{n[0]}/{n[1]}" for n in temp_visited)
                    + f" -> {node[0]}/{node[1]}"
                )
                raise ValueError(f"Circular dependency detected: {cycle}")

            temp_visited.add(node)

            # Visit all dependencies
            for dep_node in self._dependencies.get(node, {}):
                visit(dep_node)

            temp_visited.remove(node)
            visited.add(node)
            sorted_nodes.append(node)

        # Visit all nodes
        for node in all_nodes:
            if node not in visited:
                visit(node)

        # Update cache
        self._sorted_dependencies = sorted_nodes
        self._graph_changed = False

        return sorted_nodes.copy()

    def reverse_topological_sort(self) -> List[Tuple[str, str]]:
        """Sort plugins in reverse dependency order (dependents first).

        Returns:
            List of (plugin_type, provider_type) tuples in reverse dependency order
        """
        # Get topological sort and reverse it
        sorted_nodes = self.topological_sort()
        return list(reversed(sorted_nodes))


class PluginManager:
    """Manager for PepperPy plugins."""

    def __init__(self) -> None:
        """Initialize plugin manager."""
        self._instances: Dict[str, Dict[str, PepperpyPlugin]] = {}
        self._initialized = False
        self._dependency_graph = DependencyGraph()
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
                self._dependency_graph.add_dependency(
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
        return self._dependency_graph.topological_sort()

    def get_shutdown_order(self) -> List[Tuple[str, str]]:
        """Get the proper shutdown order for plugins.

        Returns:
            List of (plugin_type, provider_type) tuples in shutdown order
        """
        return self._dependency_graph.reverse_topological_sort()

    def create_instance(
        self, plugin_type: str, provider_type: str, **config: Any
    ) -> PepperpyPlugin:
        """Create a plugin instance.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider
            **config: Plugin configuration

        Returns:
            Plugin instance

        Raises:
            ValidationError: If plugin not found or creation fails
        """
        # Get plugin class
        plugin_class = get_plugin(plugin_type, provider_type)
        if not plugin_class:
            raise ValidationError(f"Plugin not found: {plugin_type}/{provider_type}")

        # Create instance
        try:
            instance = plugin_class(**config)
            if plugin_type not in self._instances:
                self._instances[plugin_type] = {}
            self._instances[plugin_type][provider_type] = instance
            return instance
        except Exception as e:
            raise ValidationError(f"Failed to create plugin instance: {e}") from e

    def get_instance(
        self, plugin_type: str, provider_type: str
    ) -> Optional[PepperpyPlugin]:
        """Get a plugin instance.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider

        Returns:
            Plugin instance if found, None otherwise
        """
        return self._instances.get(plugin_type, {}).get(provider_type)

    async def initialize(self) -> None:
        """Initialize plugin manager and all registered instances in dependency order."""
        if self._initialized:
            return

        # Get initialization order
        try:
            init_order = self.get_initialization_order()
        except ValueError as e:
            raise ConfigurationError(f"Failed to determine initialization order: {e}")

        # Initialize instances in dependency order
        for plugin_type, provider_type in init_order:
            instance = self.get_instance(plugin_type, provider_type)
            if instance:
                await instance.initialize()

        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up plugin manager and all registered instances in reverse dependency order."""
        # Get shutdown order
        try:
            shutdown_order = self.get_shutdown_order()
        except ValueError as e:
            logger.error(f"Failed to determine shutdown order, using random order: {e}")
            # Fallback to dictionary order
            shutdown_order = []
            for plugin_type, providers in self._instances.items():
                for provider_type in providers:
                    shutdown_order.append((plugin_type, provider_type))

        # Clean up instances in shutdown order
        for plugin_type, provider_type in shutdown_order:
            instance = self.get_instance(plugin_type, provider_type)
            if instance:
                try:
                    await instance.cleanup()
                except Exception as e:
                    logger.error(
                        f"Error cleaning up plugin {plugin_type}/{provider_type}: {e}"
                    )

        self._instances.clear()
        self._initialized = False

    def list_instances(self) -> Dict[str, Dict[str, PepperpyPlugin]]:
        """List all plugin instances.

        Returns:
            Dict of plugin types to provider types to plugin instances
        """
        return self._instances

    async def load_dependencies(
        self, plugin_type: str, provider_type: str
    ) -> List[Tuple[str, str]]:
        """Load all dependencies for a plugin.

        Args:
            plugin_type: Type of the plugin
            provider_type: Provider of the plugin

        Returns:
            List of loaded dependencies

        Raises:
            ConfigurationError: If a required dependency can't be loaded
        """
        loaded_dependencies: List[Tuple[str, str]] = []

        # Get all dependencies
        dependencies = self._dependency_graph.get_dependencies(
            plugin_type, provider_type
        )

        # Load each dependency
        for dep_type, dep_provider in dependencies:
            dependency_type = self._dependency_graph.get_dependency_type(
                plugin_type, provider_type, dep_type, dep_provider
            )

            try:
                # Check if already loaded
                instance = self.get_instance(dep_type, dep_provider)
                if instance is None:
                    # Create and initialize the instance
                    instance = self.create_instance(dep_type, dep_provider)
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


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager.

    Returns:
        Plugin manager instance
    """
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


async def create_and_initialize_provider(
    plugin_type: str, provider_type: str, **config: Any
) -> PepperpyPlugin:
    """Create and initialize a provider instance.

    Args:
        plugin_type: Type of plugin
        provider_type: Type of provider
        **config: Provider configuration

    Returns:
        Initialized provider instance

    Raises:
        ValidationError: If provider creation or initialization fails
    """
    # Ensure dotenv is loaded
    _ensure_dotenv_loaded()

    # Get plugin manager
    manager = get_plugin_manager()

    # Create instance
    instance = manager.create_instance(plugin_type, provider_type, **config)

    # Load dependencies
    await manager.load_dependencies(plugin_type, provider_type)

    # Initialize instance
    if not instance.initialized:
        await instance.initialize()

    return instance
