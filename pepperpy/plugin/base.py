"""
PepperPy Plugin Base Module.

This module provides core plugin interfaces and base classes for the PepperPy framework.
"""

import enum
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol, TypeVar, runtime_checkable

from pepperpy.core.errors import PepperpyError
from pepperpy.core.logging import get_logger

# Import resources locally to avoid circular imports
from .resources import (
    ResourceType,
    cleanup_owner_resources,
    get_resource,
    register_resource,
)

logger = get_logger(__name__)


class PluginError(PepperpyError):
    """Base exception for plugin-related errors."""

    pass


class PluginNotFoundError(PluginError):
    """Exception raised when a plugin is not found."""

    pass


class ResourceError(PluginError):
    """Base exception for resource-related errors."""

    pass


class PluginSource(enum.Enum):
    """Source of a plugin."""

    FILE = "file"
    PACKAGE = "package"
    ENTRY_POINT = "entry_point"
    REGISTRY = "registry"
    DYNAMIC = "dynamic"


@dataclass
class PluginDependency:
    """Dependency information for a plugin."""

    plugin_type: str
    provider_type: str
    required: bool = True
    version_constraint: str | None = None


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""

    name: str
    version: str
    description: str
    author: str = ""
    email: str = ""
    license: str = ""
    website: str = ""
    repository: str = ""
    keywords: list[str] = field(default_factory=list)
    documentation: str = ""
    additional: dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginInfo:
    """Enhanced information about a plugin."""

    name: str
    version: str
    description: str
    plugin_type: str
    provider_type: str

    # Plugin metadata
    author: str = ""
    email: str = ""
    license: str = ""

    # Source information
    source: PluginSource = PluginSource.FILE
    path: str | None = None
    module: str | None = None
    class_name: str | None = None
    entry_point: str | None = None

    # Dependencies
    dependencies: list[PluginDependency] = field(default_factory=list)
    python_dependencies: list[str] = field(default_factory=list)
    system_dependencies: list[str] = field(default_factory=list)

    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    # Lazy loading
    _loaded: bool = False
    _plugin_class: Any = None

    def is_loaded(self) -> bool:
        """Check if the plugin class is loaded."""
        return self._loaded

    def get_class(self) -> Any:
        """Get the plugin class (loads it if not already loaded)."""
        if not self._loaded and self._plugin_class is None:
            # In a real implementation, this would load the plugin class
            # from source information
            pass
        return self._plugin_class


class ResourceMixin:
    """Mixin for resource management capabilities."""

    async def register_resource(
        self, resource_type: ResourceType, resource_id: str, resource: Any
    ) -> None:
        """Register a resource.

        Args:
            resource_type: Type of resource
            resource_id: Resource identifier
            resource: Resource object
        """
        register_resource(resource_type.value, resource_id, resource, str(id(self)))

    async def get_resource(self, resource_type: ResourceType, resource_id: str) -> Any:
        """Get a registered resource.

        Args:
            resource_type: Type of resource
            resource_id: Resource identifier

        Returns:
            Resource object

        Raises:
            ResourceError: If the resource is not found
        """
        resource = get_resource(resource_type.value, resource_id)
        if resource is None:
            raise ResourceError(
                f"Resource not found: {resource_type.value}.{resource_id}"
            )
        return resource

    async def cleanup_resources(self) -> None:
        """Clean up all resources owned by this plugin."""
        await cleanup_owner_resources(str(id(self)))


T = TypeVar("T")


@runtime_checkable
class PepperpyPlugin(Protocol):
    """Base protocol for PepperPy plugins."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the plugin."""
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources used by the plugin."""
        ...

    async def can_handle_type(self, content_type: str) -> bool:
        """Check if the plugin can handle the given content type.

        Args:
            content_type: MIME type or extension

        Returns:
            True if the plugin can handle the content type, False otherwise
        """
        return False

    async def detect_type(
        self, content: str | bytes, filename: str | None = None
    ) -> str | None:
        """Detect the type of the given content.

        Args:
            content: Content to analyze
            filename: Optional filename with extension

        Returns:
            Detected content type or None if not detected
        """
        return None

    async def get_resources(self) -> list[ResourceType]:
        """Get resources provided by this plugin.

        Returns:
            List of resource types
        """
        return []


@runtime_checkable
class PluginDiscoveryProtocol(Protocol):
    """Protocol for plugin discovery providers."""

    @abstractmethod
    async def discover_plugins(self) -> list[PluginInfo]:
        """Discover available plugins.

        Returns:
            List of discovered plugin information
        """
        ...

    @abstractmethod
    async def load_plugin(self, plugin_info: PluginInfo) -> Any:
        """Load a plugin from its information.

        Args:
            plugin_info: Plugin information

        Returns:
            Loaded plugin class
        """
        ...


def create_provider_instance(
    domain: str, provider_type: str, **config: Any
) -> Any:
    """Create a provider instance.

    Args:
        domain: Provider domain (llm, tts, etc.)
        provider_type: Provider type
        **config: Provider configuration

    Returns:
        Provider instance

    Raises:
        PluginNotFoundError: If provider not found
    """
    from pepperpy.plugin.registry import get_plugin, get_registry

    # For debug purposes
    registry = get_registry()
    logger.info(f"Creating provider instance for {domain}/{provider_type}")
    logger.info(f"Registry ID: {id(registry)}")
    logger.info(f"Available domains: {list(registry._plugins.keys())}")
    if domain in registry._plugins:
        logger.info(f"Available providers in {domain}: {list(registry._plugins[domain].keys())}")
        
        # Special handling for workflow domain which might be registered differently
        if domain == "workflow" and provider_type not in registry._plugins[domain]:
            # Try direct provider retrieval from _plugins for workflow domain
            if "workflow/repository_analyzer" in registry._plugins[domain]:
                logger.info(f"Found provider with direct lookup: workflow/repository_analyzer")
                plugin_class = registry._plugins[domain]["workflow/repository_analyzer"]["class"]
                return plugin_class(**config)
            
            if "repository_analyzer" in registry._plugins[domain]:
                logger.info(f"Found provider with direct lookup: repository_analyzer")
                plugin_class = registry._plugins[domain]["repository_analyzer"]["class"]
                return plugin_class(**config)

    # Get the plugin class
    plugin_class = get_plugin(domain, provider_type)
    if not plugin_class:
        raise PluginNotFoundError(f"Provider not found: {domain}/{provider_type}")

    # Create an instance
    instance = plugin_class(**config)

    return instance
