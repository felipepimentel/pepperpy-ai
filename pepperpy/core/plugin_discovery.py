"""Enhanced plugin discovery system for PepperPy.

This module provides a standardized mechanism for discovering, loading,
and registering plugins, with support for automatic dependency resolution,
versioning, and validation.
"""

import importlib
import logging
import os
import re
import sys
from enum import Enum
from importlib.metadata import distribution, entry_points
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union

import yaml

from pepperpy.core.base import PepperpyError, ValidationError
from pepperpy.core.logging import get_logger

# Type for generic plugin
T = TypeVar('T')

logger = get_logger(__name__)


class PluginValidationError(ValidationError):
    """Error raised when plugin validation fails."""
    
    def __init__(
        self,
        message: str,
        plugin_name: Optional[str] = None,
        plugin_path: Optional[str] = None,
        *args,
        **kwargs
    ):
        super().__init__(message, *args, **kwargs)
        self.plugin_name = plugin_name
        self.plugin_path = plugin_path
        
    def __str__(self) -> str:
        parts = [self.message]
        if self.plugin_name:
            parts.append(f"Plugin: {self.plugin_name}")
        if self.plugin_path:
            parts.append(f"Path: {self.plugin_path}")
        return " | ".join(parts)


class PluginLoadError(PepperpyError):
    """Error raised when plugin loading fails."""
    
    def __init__(
        self,
        message: str,
        plugin_name: Optional[str] = None,
        plugin_path: Optional[str] = None,
        cause: Optional[Exception] = None,
        *args,
        **kwargs
    ):
        super().__init__(message, *args, **kwargs)
        self.plugin_name = plugin_name
        self.plugin_path = plugin_path
        self.cause = cause
        
    def __str__(self) -> str:
        parts = [self.message]
        if self.plugin_name:
            parts.append(f"Plugin: {self.plugin_name}")
        if self.plugin_path:
            parts.append(f"Path: {self.plugin_path}")
        if self.cause:
            parts.append(f"Cause: {str(self.cause)}")
        return " | ".join(parts)


class PluginSource(Enum):
    """Source of plugin discovery."""
    
    LOCAL = "local"  # Local filesystem
    ENTRYPOINT = "entrypoint"  # Entry points from installed packages
    NAMESPACE = "namespace"  # Python namespace packages
    DYNAMIC = "dynamic"  # Dynamically registered


class PluginInfo:
    """Information about a plugin."""
    
    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        category: str,
        provider_name: str,
        entry_point: str,
        path: Optional[str] = None,
        source: PluginSource = PluginSource.LOCAL,
        metadata: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None,
        enabled: bool = True
    ):
        """Initialize plugin info.
        
        Args:
            name: Plugin name
            version: Plugin version
            description: Plugin description
            category: Plugin category
            provider_name: Provider name
            entry_point: Entry point to provider class
            path: Path to plugin directory
            source: Source of plugin discovery
            metadata: Additional metadata
            dependencies: Plugin dependencies
            enabled: Whether plugin is enabled
        """
        self.name = name
        self.version = version
        self.description = description
        self.category = category
        self.provider_name = provider_name
        self.entry_point = entry_point
        self.path = path
        self.source = source
        self.metadata = metadata or {}
        self.dependencies = dependencies or []
        self.enabled = enabled
        self._plugin_class = None
        self._plugin_instance = None
        
    @classmethod
    def from_yaml(cls, yaml_path: Union[str, Path]) -> "PluginInfo":
        """Create plugin info from YAML file.
        
        Args:
            yaml_path: Path to YAML file
            
        Returns:
            Plugin info
            
        Raises:
            PluginValidationError: If YAML is invalid
        """
        yaml_path = Path(yaml_path)
        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
                
            # Validate required fields
            required_fields = [
                "name", "version", "description", "plugin_type", 
                "provider_name", "entry_point"
            ]
            missing = [f for f in required_fields if f not in data]
            if missing:
                raise PluginValidationError(
                    f"Missing required fields: {', '.join(missing)}",
                    plugin_path=str(yaml_path)
                )
                
            # Create plugin info
            return cls(
                name=data["name"],
                version=data["version"],
                description=data["description"],
                category=data["plugin_type"],
                provider_name=data["provider_name"],
                entry_point=data["entry_point"],
                path=str(yaml_path.parent),
                metadata=data,
                dependencies=data.get("dependencies", []),
                enabled=data.get("enabled", True)
            )
            
        except Exception as e:
            if isinstance(e, PluginValidationError):
                raise
            raise PluginValidationError(
                f"Failed to load plugin YAML: {e}",
                plugin_path=str(yaml_path),
            ) from e
    
    def get_class(self) -> Type[Any]:
        """Get plugin class.
        
        Returns:
            Plugin class
            
        Raises:
            PluginLoadError: If class loading fails
        """
        if self._plugin_class is not None:
            return self._plugin_class
            
        try:
            if ":" in self.entry_point:
                # Format: module.path:ClassName
                module_path, class_name = self.entry_point.split(":", 1)
            else:
                # Format: module.path.ClassName
                module_path, class_name = self.entry_point.rsplit(".", 1)
                
            # If path is provided, add to sys.path temporarily
            path_added = False
            if self.path and self.path not in sys.path:
                sys.path.insert(0, self.path)
                path_added = True
                
            try:
                module = importlib.import_module(module_path)
                self._plugin_class = getattr(module, class_name)
                return self._plugin_class
            finally:
                # Remove from sys.path if added
                if path_added:
                    sys.path.remove(self.path)
                    
        except (ImportError, AttributeError) as e:
            raise PluginLoadError(
                f"Failed to load plugin class: {e}",
                plugin_name=self.name,
                plugin_path=self.path,
                cause=e
            ) from e
    
    def create_instance(self, **kwargs: Any) -> Any:
        """Create plugin instance.
        
        Args:
            **kwargs: Configuration for the plugin
            
        Returns:
            Plugin instance
            
        Raises:
            PluginLoadError: If instance creation fails
        """
        try:
            cls = self.get_class()
            instance = cls(**kwargs)
            self._plugin_instance = instance
            return instance
        except Exception as e:
            if isinstance(e, PluginLoadError):
                raise
            raise PluginLoadError(
                f"Failed to create plugin instance: {e}",
                plugin_name=self.name,
                plugin_path=self.path,
                cause=e
            ) from e


class PluginRegistry:
    """Registry for plugins.
    
    This class manages the discovery, registration, and retrieval of plugins.
    It supports multiple plugin sources including local filesystem,
    entry points, and namespaces.
    """
    
    def __init__(self):
        """Initialize plugin registry."""
        self._plugins: Dict[str, PluginInfo] = {}
        self._categories: Dict[str, Dict[str, PluginInfo]] = {}
        self._providers: Dict[str, Dict[str, PluginInfo]] = {}
        self._search_paths: List[str] = []
        self._initialized = False
        
    def register_plugin(self, plugin: PluginInfo) -> None:
        """Register a plugin.
        
        Args:
            plugin: Plugin info
        """
        self._plugins[plugin.name] = plugin
        
        # Register by category
        if plugin.category not in self._categories:
            self._categories[plugin.category] = {}
        self._categories[plugin.category][plugin.name] = plugin
        
        # Register by provider name
        provider_key = f"{plugin.category}:{plugin.provider_name}"
        if provider_key not in self._providers:
            self._providers[provider_key] = {}
        self._providers[provider_key][plugin.name] = plugin
        
        logger.debug(f"Registered plugin: {plugin.name} ({plugin.category}/{plugin.provider_name})")
        
    def unregister_plugin(self, plugin_name: str) -> None:
        """Unregister a plugin.
        
        Args:
            plugin_name: Plugin name
        """
        if plugin_name not in self._plugins:
            return
            
        plugin = self._plugins[plugin_name]
        
        # Unregister from categories
        if plugin.category in self._categories:
            if plugin_name in self._categories[plugin.category]:
                del self._categories[plugin.category][plugin_name]
                
        # Unregister from providers
        provider_key = f"{plugin.category}:{plugin.provider_name}"
        if provider_key in self._providers:
            if plugin_name in self._providers[provider_key]:
                del self._providers[provider_key][plugin_name]
                
        # Unregister from plugins
        del self._plugins[plugin_name]
        
        logger.debug(f"Unregistered plugin: {plugin_name}")
        
    def add_search_path(self, path: str) -> None:
        """Add a search path for plugins.
        
        Args:
            path: Path to search for plugins
        """
        if path not in self._search_paths:
            self._search_paths.append(path)
            logger.debug(f"Added plugin search path: {path}")
            
    def get_plugin(self, plugin_name: str) -> Optional[PluginInfo]:
        """Get plugin by name.
        
        Args:
            plugin_name: Plugin name
            
        Returns:
            Plugin info or None if not found
        """
        return self._plugins.get(plugin_name)
        
    def get_plugin_by_provider(
        self, category: str, provider_name: str
    ) -> Optional[PluginInfo]:
        """Get plugin by category and provider name.
        
        Args:
            category: Plugin category
            provider_name: Provider name
            
        Returns:
            Plugin info or None if not found
        """
        provider_key = f"{category}:{provider_name}"
        if provider_key in self._providers:
            # Return the first plugin for this provider
            providers = self._providers[provider_key]
            if providers:
                return next(iter(providers.values()))
        return None
        
    def get_plugins_by_category(self, category: str) -> Dict[str, PluginInfo]:
        """Get plugins by category.
        
        Args:
            category: Plugin category
            
        Returns:
            Dictionary of plugin name to plugin info
        """
        return self._categories.get(category, {})
        
    def list_plugins(self) -> Dict[str, PluginInfo]:
        """List all plugins.
        
        Returns:
            Dictionary of plugin name to plugin info
        """
        return dict(self._plugins)
        
    def list_categories(self) -> List[str]:
        """List all plugin categories.
        
        Returns:
            List of category names
        """
        return list(self._categories.keys())
        
    def list_providers(self, category: str) -> List[str]:
        """List all providers for a category.
        
        Args:
            category: Plugin category
            
        Returns:
            List of provider names
        """
        providers = set()
        for plugin in self._categories.get(category, {}).values():
            providers.add(plugin.provider_name)
        return list(providers)
        
    def discover_plugins(
        self, 
        search_paths: Optional[List[str]] = None,
        include_entrypoints: bool = True
    ) -> None:
        """Discover and register plugins.
        
        This method scans the configured search paths and entry points
        for plugins and registers them.
        
        Args:
            search_paths: Optional additional search paths
            include_entrypoints: Whether to include entry points
        """
        if search_paths:
            for path in search_paths:
                self.add_search_path(path)
                
        # Discover plugins from search paths
        for path in self._search_paths:
            try:
                self._discover_from_path(path)
            except Exception as e:
                logger.warning(f"Failed to discover plugins from {path}: {e}")
                
        # Discover plugins from entry points
        if include_entrypoints:
            try:
                self._discover_from_entrypoints()
            except Exception as e:
                logger.warning(f"Failed to discover plugins from entry points: {e}")
                
        self._initialized = True
        logger.info(f"Discovered {len(self._plugins)} plugins")
                
    def _discover_from_path(self, path: str) -> None:
        """Discover plugins from a directory path.
        
        Args:
            path: Path to search for plugins
        """
        path = Path(path)
        if not path.exists() or not path.is_dir():
            logger.warning(f"Plugin search path does not exist or is not a directory: {path}")
            return
            
        # Find all plugin.yaml files
        for plugin_yaml in path.glob("**/plugin.yaml"):
            try:
                plugin = PluginInfo.from_yaml(plugin_yaml)
                self.register_plugin(plugin)
            except Exception as e:
                logger.warning(f"Failed to load plugin from {plugin_yaml}: {e}")
                
    def _discover_from_entrypoints(self) -> None:
        """Discover plugins from entry points."""
        try:
            eps = entry_points()
            
            # Handle different entry_points() return type in Python 3.8 vs 3.9+
            pepperpy_eps = getattr(eps, "get", lambda x: eps)(
                "pepperpy.plugins"
            ) or []
            
            for ep in pepperpy_eps:
                try:
                    plugin_class = ep.load()
                    
                    # Get metadata from class
                    metadata = getattr(plugin_class, "plugin_metadata", {})
                    if not metadata:
                        logger.warning(f"No metadata for entry point plugin: {ep.name}")
                        continue
                        
                    # Create plugin info
                    plugin = PluginInfo(
                        name=metadata.get("name", ep.name),
                        version=metadata.get("version", "0.1.0"),
                        description=metadata.get("description", ""),
                        category=metadata.get("category", ""),
                        provider_name=metadata.get("provider_name", ""),
                        entry_point=ep.value,
                        source=PluginSource.ENTRYPOINT,
                        metadata=metadata
                    )
                    
                    self.register_plugin(plugin)
                except Exception as e:
                    logger.warning(f"Failed to load entry point plugin {ep.name}: {e}")
        except Exception as e:
            logger.warning(f"Failed to discover entry point plugins: {e}")


# Global plugin registry instance
_plugin_registry = None


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry.
    
    Returns:
        Plugin registry
    """
    global _plugin_registry
    if _plugin_registry is None:
        _plugin_registry = PluginRegistry()
        
        # Add default search paths
        # First try the package path
        try:
            package_path = Path(__file__).parent.parent.parent / "plugins"
            if package_path.exists():
                _plugin_registry.add_search_path(str(package_path))
        except Exception:
            pass
            
        # Then try the current working directory
        try:
            cwd_path = Path.cwd() / "plugins"
            if cwd_path.exists():
                _plugin_registry.add_search_path(str(cwd_path))
        except Exception:
            pass
            
    return _plugin_registry


def discover_plugins(
    search_paths: Optional[List[str]] = None,
    include_entrypoints: bool = True
) -> None:
    """Discover and register plugins.
    
    Args:
        search_paths: Optional additional search paths
        include_entrypoints: Whether to include entry points
    """
    registry = get_plugin_registry()
    registry.discover_plugins(search_paths, include_entrypoints)


def get_plugin(plugin_name: str) -> Optional[PluginInfo]:
    """Get plugin by name.
    
    Args:
        plugin_name: Plugin name
        
    Returns:
        Plugin info or None if not found
    """
    registry = get_plugin_registry()
    return registry.get_plugin(plugin_name)


def get_plugin_by_provider(
    category: str, provider_name: str
) -> Optional[PluginInfo]:
    """Get plugin by category and provider name.
    
    Args:
        category: Plugin category
        provider_name: Provider name
        
    Returns:
        Plugin info or None if not found
    """
    registry = get_plugin_registry()
    return registry.get_plugin_by_provider(category, provider_name)


def create_provider_instance(
    category: str, 
    provider_name: str, 
    **kwargs: Any
) -> Any:
    """Create a provider instance.
    
    Args:
        category: Plugin category
        provider_name: Provider name
        **kwargs: Configuration for the provider
        
    Returns:
        Provider instance
        
    Raises:
        PluginLoadError: If provider loading fails
    """
    registry = get_plugin_registry()
    plugin = registry.get_plugin_by_provider(category, provider_name)
    if not plugin:
        raise PluginLoadError(
            f"Provider not found: {category}/{provider_name}",
            plugin_name=f"{category}/{provider_name}"
        )
        
    return plugin.create_instance(**kwargs)