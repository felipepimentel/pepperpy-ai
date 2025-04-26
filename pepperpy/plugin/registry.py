"""
PepperPy Plugin Registry.

Core plugin registration and retrieval functionality.
"""

from typing import Any, Dict, Optional, Type, TypeVar, Union, cast
import logging
import importlib
import inspect
import os
import sys
from pathlib import Path
from types import ModuleType

from pepperpy.core.errors import PluginNotFoundError
from pepperpy.core.logging import get_logger
from pepperpy.plugin.base import PluginInfo

T = TypeVar("T", bound=PluginInfo)

logger = get_logger(__name__)


class PluginRegistry:
    """Registry for plugins."""

    def __init__(self) -> None:
        """Initialize the registry."""
        self._plugins: Dict[str, Dict[str, Dict[str, Any]]] = {
            "llm": {},
            "tts": {},
            "agent": {},
            "tool": {},
            "rag": {},
            "content": {},
            "embeddings": {},
            "workflow": {},
            "cache": {},
        }
        # Dictionary to store plugin info objects for lazy loading
        self._plugin_info: Dict[str, Dict[str, PluginInfo]] = {
            domain: {} for domain in self._plugins.keys()
        }
        self._loaded_plugins: Dict[str, Dict[str, Type[PluginInfo]]] = {
            domain: {} for domain in self._plugins.keys()
        }
        self.logger = logger

    def register_plugin(
        self,
        domain: str,
        name: str,
        plugin_class: Type[PluginInfo],
        meta: dict[str, Any] | None = None,
    ) -> None:
        """Register a plugin class.

        Args:
            domain: Domain of the plugin.
            name: Name of the plugin.
            plugin_class: Plugin class.
            meta: Metadata for the plugin.
        """
        self.logger.debug(f"Registering plugin {domain}/{name}")
        if domain not in self._loaded_plugins:
            self._loaded_plugins[domain] = {}
        self._loaded_plugins[domain][name] = plugin_class

        # Store metadata if provided
        if meta and domain in self._plugins:
            if name not in self._plugins[domain]:
                self._plugins[domain][name] = {}
            self._plugins[domain][name].update(meta)

    def register_plugin_info(
        self, domain: str, name: str, plugin_info: PluginInfo
    ) -> None:
        """Register plugin info.

        Args:
            domain: Domain of the plugin.
            name: Name of the plugin.
            plugin_info: Plugin info.
        """
        self.logger.debug(f"Registering plugin info {domain}/{name}")
        if domain not in self._plugin_info:
            self._plugin_info[domain] = {}
        self._plugin_info[domain][name] = plugin_info

    def load_plugin_if_needed(self, domain: str, name: str) -> Type[PluginInfo]:
        """Load a plugin if needed.

        Args:
            domain: Domain of the plugin.
            name: Name of the plugin.

        Returns:
            Plugin class.

        Raises:
            PluginNotFoundError: If the plugin is not found.
        """
        # Check if the plugin is already loaded.
        if domain in self._loaded_plugins and name in self._loaded_plugins[domain]:
            return self._loaded_plugins[domain][name]

        # Check if we have info about the plugin.
        if domain not in self._plugin_info or name not in self._plugin_info[domain]:
            raise PluginNotFoundError(f"Plugin {domain}/{name} not found")

        plugin_info = self._plugin_info[domain][name]
        
        # If we have a module path, load the module and find the class
        if plugin_info.module_path and plugin_info.module_name:
            try:
                self.logger.debug(f"Loading plugin from {plugin_info.module_path}")
                
                # If the module is already loaded, just get it
                if plugin_info.module_name in sys.modules:
                    module = sys.modules[plugin_info.module_name]
                else:
                    # Otherwise, load it
                    spec = importlib.util.spec_from_file_location(
                        plugin_info.module_name, plugin_info.module_path
                    )
                    if not spec or not spec.loader:
                        raise PluginNotFoundError(f"Cannot load module spec for {plugin_info.module_path}")
                    
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[plugin_info.module_name] = module
                    spec.loader.exec_module(module)
                
                # Find the plugin class in the module
                plugin_class = self._find_plugin_class(module, plugin_info)
                if plugin_class:
                    self.register_plugin(domain, name, plugin_class)
                    return plugin_class
                
                raise PluginNotFoundError(f"Plugin class not found in {plugin_info.module_path}")
            except Exception as e:
                self.logger.error(f"Error loading plugin from {plugin_info.module_path}: {e}")
                raise PluginNotFoundError(f"Error loading plugin: {e}")
        
        raise PluginNotFoundError(f"Plugin {domain}/{name} not loadable")

    def _find_plugin_class(self, module: Any, plugin_info: PluginInfo) -> Optional[Type[PluginInfo]]:
        """Find the plugin class in the given module.
        
        Args:
            module: Module to search
            plugin_info: Plugin information
            
        Returns:
            Plugin class or None
        """
        # If class name is specified, look for it
        if plugin_info.class_name:
            if hasattr(module, plugin_info.class_name):
                return getattr(module, plugin_info.class_name)
        
        # Otherwise look for any class that matches the naming convention
        for name, obj in inspect.getmembers(module):
            if not inspect.isclass(obj):
                continue
                
            # Skip abstract classes
            if inspect.isabstract(obj):
                continue
                
            # Check for naming pattern based on plugin type
            if plugin_info.plugin_type:
                type_suffix = plugin_info.plugin_type.capitalize() + "Provider"
                if name.endswith(type_suffix):
                    return obj
            
            # Check for "Provider" suffix
            if name.endswith("Provider"):
                return obj
                
        return None

    def load_plugin_module(self, domain: str, name: str) -> ModuleType:
        """Load a plugin module.

        Args:
            domain: Domain of the plugin.
            name: Name of the plugin.

        Returns:
            Plugin module.
        """
        plugin_info = self.get_plugin_metadata(domain, name)
        if not plugin_info:
            raise PluginNotFoundError(f"Plugin {domain}/{name} not found")

        if not plugin_info.module_path:
            raise PluginNotFoundError(f"Plugin {domain}/{name} module not found")

        module_path = plugin_info.module_path
        try:
            return importlib.import_module(module_path)
        except ImportError as e:
            self.logger.error(f"Error loading module {module_path}: {e}")
            raise PluginNotFoundError(f"Plugin {domain}/{name} module not found")

    def get_plugin(self, domain: str, name: str) -> Type[PluginInfo]:
        """Get a plugin.

        Args:
            domain: Domain of the plugin.
            name: Name of the plugin.

        Returns:
            Plugin class.

        Raises:
            PluginNotFoundError: If the plugin is not found.
        """
        return self.load_plugin_if_needed(domain, name)

    def get_plugin_metadata(self, domain: str, name: str) -> Optional[PluginInfo]:
        """Get plugin metadata.

        Args:
            domain: Domain of the plugin.
            name: Name of the plugin.

        Returns:
            Plugin metadata or None if not found.
        """
        if domain not in self._plugin_info or name not in self._plugin_info[domain]:
            return None
        return self._plugin_info[domain][name]

    def list_plugins(self, domain: Optional[str] = None) -> Dict[str, Dict[str, PluginInfo]]:
        """List plugins.

        Args:
            domain: Domain to list plugins for. If None, list all plugins.

        Returns:
            Dictionary of plugins by domain and name.
        """
        if domain:
            if domain not in self._plugin_info:
                return {}
            return {domain: self._plugin_info[domain].copy()}
        
        return self._plugin_info.copy()
        
    async def discover_plugins(self) -> Dict[str, Dict[str, PluginInfo]]:
        """Discover plugins from the filesystem.
        
        Returns:
            Dictionary of discovered plugins by domain and name.
        """
        discovered_plugins = {}
        plugin_dirs = [
            os.path.join(os.getcwd(), "plugins")
        ]
        
        for base_dir in plugin_dirs:
            if not os.path.exists(base_dir):
                continue
                
            # Scan for plugins in directory
            self.logger.info(f"Scanning for plugins in {base_dir}")
            try:
                for domain_dir in os.listdir(base_dir):
                    domain_path = os.path.join(base_dir, domain_dir)
                    if not os.path.isdir(domain_path):
                        continue
                        
                    # Initialize domain in discovered_plugins
                    if domain_dir not in discovered_plugins:
                        discovered_plugins[domain_dir] = {}
                        
                    # Scan for plugins within domain directory
                    for plugin_dir in os.listdir(domain_path):
                        plugin_path = os.path.join(domain_path, plugin_dir)
                        if not os.path.isdir(plugin_path):
                            continue
                            
                        # Check for plugin.yaml file
                        plugin_yaml = os.path.join(plugin_path, "plugin.yaml")
                        if not os.path.exists(plugin_yaml):
                            continue
                            
                        # Create plugin info from yaml
                        plugin_info = self._load_plugin_info(plugin_yaml, plugin_path)
                        if plugin_info:
                            # Register plugin info
                            provider_name = plugin_info.provider_name or plugin_dir
                            self.register_plugin_info(domain_dir, provider_name, plugin_info)
                            
                            # Add to discovered plugins
                            discovered_plugins[domain_dir][provider_name] = plugin_info
            except Exception as e:
                self.logger.error(f"Error scanning for plugins in {base_dir}: {e}")
                
        return discovered_plugins
        
    def _load_plugin_info(self, yaml_file: str, plugin_dir: str) -> Optional[PluginInfo]:
        """Load plugin information from YAML file.
        
        Args:
            yaml_file: Path to plugin.yaml file
            plugin_dir: Path to plugin directory
            
        Returns:
            Plugin info or None if error
        """
        try:
            import yaml
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                
            # Check required fields
            required_fields = ["name", "version", "description", "plugin_type", "provider_name"]
            for field in required_fields:
                if field not in data:
                    self.logger.warning(f"Missing required field {field} in {yaml_file}")
                    return None
                    
            # Create module path
            plugin_type = data["plugin_type"]
            provider_name = data["provider_name"]
            
            # Look for provider files
            provider_file = os.path.join(plugin_dir, "provider.py")
            if not os.path.exists(provider_file):
                provider_file = os.path.join(plugin_dir, f"{plugin_type}_provider.py")
                
            if not os.path.exists(provider_file):
                provider_file = os.path.join(plugin_dir, f"{provider_name}.py")
                
            if not os.path.exists(provider_file):
                self.logger.warning(f"No provider file found in {plugin_dir}")
                return None
                
            # Create a unique module name
            module_name = f"pepperpy_plugin_{plugin_type}_{provider_name}_{hash(plugin_dir) & 0xFFFFFFFF}"
            
            # Create plugin info
            return PluginInfo(
                name=data["name"],
                version=data["version"],
                description=data["description"],
                provider_name=data["provider_name"],
                plugin_type=data["plugin_type"],
                module_path=provider_file,
                module_name=module_name,
                class_name=None,  # Will be discovered during loading
                config=data.get("config", {})
            )
        except Exception as e:
            self.logger.error(f"Error loading plugin info from {yaml_file}: {e}")
            return None


# Global plugin registry instance
_registry = PluginRegistry()


def get_registry() -> PluginRegistry:
    """Get the global plugin registry.

    Returns:
        The global plugin registry.
    """
    return _registry


def register_plugin(
    domain: str,
    name: str,
    plugin_class: Type[PluginInfo],
    meta: dict[str, Any] | None = None,
) -> None:
    """Register a plugin in the global registry.

    Args:
        domain: Domain of the plugin.
        name: Name of the plugin.
        plugin_class: Plugin class.
        meta: Metadata for the plugin.
    """
    _registry.register_plugin(domain, name, plugin_class, meta)


def register_plugin_info(
    domain: str, name: str, plugin_info: PluginInfo
) -> None:
    """Register plugin info in the global registry.

    Args:
        domain: Domain of the plugin.
        name: Name of the plugin.
        plugin_info: Plugin info.
    """
    _registry.register_plugin_info(domain, name, plugin_info)


def get_plugin(domain: str, name: str) -> Type[PluginInfo]:
    """Get a plugin from the global registry.

    Args:
        domain: Domain of the plugin.
        name: Name of the plugin.

    Returns:
        Plugin class.

    Raises:
        PluginNotFoundError: If the plugin is not found.
    """
    return _registry.get_plugin(domain, name)


def get_plugin_metadata(domain: str, name: str) -> Optional[PluginInfo]:
    """Get plugin metadata from the global registry.

    Args:
        domain: Domain of the plugin.
        name: Name of the plugin.

    Returns:
        Plugin metadata or None if not found.
    """
    return _registry.get_plugin_metadata(domain, name)


def list_plugins(domain: Optional[str] = None) -> Dict[str, Dict[str, PluginInfo]]:
    """List plugins in the global registry.

    Args:
        domain: Domain to list plugins for. If None, list all plugins.

    Returns:
        Dictionary of plugins by domain and name.
    """
    return _registry.list_plugins(domain)


async def discover_plugins() -> Dict[str, Dict[str, PluginInfo]]:
    """Discover plugins.
    
    Returns:
        Dictionary of discovered plugins.
    """
    return await _registry.discover_plugins()
