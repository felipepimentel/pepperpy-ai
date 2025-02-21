"""Registry system for managing Pepperpy components.

This module provides a comprehensive registry system for managing:
- Generic component registration and lifecycle
- Agent capability discovery and versioning
- Type-safe component creation and validation
- Event-driven updates and notifications
- Metadata tracking and version control
"""

import asyncio
import importlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Dict, Generic, Optional, Type, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from pepperpy.core.errors import (
    ConfigError,
    NotFoundError,
    RegistryError,
    StateError,
    ValidationError,
)
from pepperpy.events import (
    EventBus,
    EventType,
)
from pepperpy.events.handlers.registry import RegistryEvent
from pepperpy.monitoring import logger

# Configure logging
logger = logger.getChild(__name__)

T = TypeVar("T")


@dataclass
class Version:
    """Version information for components and capabilities."""

    major: int
    minor: int
    patch: int

    @classmethod
    def from_string(cls, version_str: str) -> "Version":
        """Create version from string.

        Args:
            version_str: Version string (e.g., "1.2.3")

        Returns:
            Version: Version instance

        Raises:
            ValueError: If version string is invalid

        """
        try:
            major, minor, patch = map(int, version_str.split("."))
            return cls(major=major, minor=minor, patch=patch)
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid version string: {version_str}") from e

    def __str__(self) -> str:
        """Convert version to string."""
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: "Version") -> bool:
        """Compare versions."""
        return self.major < other.major or (
            self.major == other.major
            and (
                self.minor < other.minor
                or (self.minor == other.minor and self.patch < other.patch)
            )
        )


class RegistryItem(BaseModel):
    """Registry item model."""

    class Config:
        """Pydantic model configuration."""

        arbitrary_types_allowed = True
        json_encoders: ClassVar[dict[type, Any]] = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            type: lambda v: f"{v.__module__}.{v.__qualname__}",
        }

    @classmethod
    @field_validator("key")
    def validate_key(cls, v: str) -> str:
        """Validate registry key."""
        if not v.strip():
            raise ValueError("key cannot be empty")
        return v

    @classmethod
    @field_validator("metadata")
    def validate_metadata(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure metadata is immutable."""
        return dict(v)


class RegistryMetadata(RegistryItem, Generic[T]):
    """Base metadata for registry items."""

    id: UUID = Field(default_factory=uuid4)
    key: str
    type: type[T]
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CapabilityMetadata(RegistryMetadata):
    """Metadata for agent capabilities."""

    agent_id: UUID
    framework: str
    requirements: list[str] = Field(default_factory=list)
    deprecated: bool = False
    deprecation_reason: str | None = None
    upgrade_path: str | None = None


class Registry(Generic[T]):
    """Generic registry for managing system components.

    This class provides the core functionality for:
    - Component registration and lifecycle management
    - Version tracking and compatibility checking
    - Event-driven updates and notifications
    - Metadata management and validation

    Attributes:
        name: Registry name for identification
        event_bus: Event bus for registry events

    """

    def __init__(self, name: str, event_bus: EventBus | None = None) -> None:
        """Initialize the registry.

        Args:
            name: Registry name for identification
            event_bus: Optional event bus for registry events

        """
        self._name = name
        self._items: dict[str, dict[str, RegistryMetadata[T]]] = {}
        self._event_bus = event_bus
        self._lock = asyncio.Lock()
        self._active = False

    @property
    def name(self) -> str:
        """Get the registry name."""
        return self._name

    @property
    def is_active(self) -> bool:
        """Check if registry is active."""
        return self._active

    async def start(self) -> None:
        """Start the registry."""
        if self._active:
            raise StateError("Registry is already active")
        self._active = True

    async def stop(self) -> None:
        """Stop the registry."""
        self._active = False

    def _ensure_active(self) -> None:
        """Ensure registry is active."""
        if not self._active:
            raise StateError("Registry is not active")

    async def register(
        self,
        key: str,
        item_type: type[T],
        version: str,
        metadata: dict[str, Any] | None = None,
    ) -> UUID:
        """Register an item in the registry.

        Args:
            key: Unique identifier for the item
            item_type: Type of the item to register
            version: Version of the item
            metadata: Optional metadata for the item

        Returns:
            UUID: Unique identifier for the registered item

        Raises:
            StateError: If registry is not active
            ValidationError: If validation fails
            RegistryError: If registration fails

        """
        self._ensure_active()

        if metadata is None:
            metadata = {}

        try:
            async with self._lock:
                if key not in self._items:
                    self._items[key] = {}

                if version in self._items[key]:
                    raise RegistryError(f"Item already registered: {key}@{version}")

                item_metadata = RegistryMetadata(
                    key=key,
                    type=item_type,
                    version=version,
                    metadata=metadata,
                )

                self._items[key][version] = item_metadata

                if self._event_bus:
                    event = RegistryEvent(
                        event_type=EventType.PROVIDER_REGISTERED,
                        registry_id=uuid4(),
                        operation="register",
                        item_type=item_type.__name__,
                        item_id=str(item_metadata.id),
                        metadata=metadata,
                    )
                    await self._event_bus.publish(event)

                return item_metadata.id

        except Exception as e:
            raise RegistryError(f"Failed to register item: {e}") from e

    async def unregister(self, key: str, version: str | None = None) -> None:
        """Unregister an item from the registry.

        Args:
            key: Item key to unregister
            version: Optional version to unregister. If None, unregisters all versions.

        Raises:
            StateError: If registry is not active
            NotFoundError: If item not found
            RegistryError: If unregistration fails

        """
        self._ensure_active()

        try:
            async with self._lock:
                if key not in self._items:
                    raise NotFoundError(f"Item not found: {key}")

                if version:
                    if version not in self._items[key]:
                        raise NotFoundError(f"Version not found: {key}@{version}")

                    item_metadata = self._items[key][version]
                    del self._items[key][version]

                    if not self._items[key]:
                        del self._items[key]

                    if self._event_bus:
                        event = RegistryEvent(
                            event_type=EventType.PROVIDER_UNREGISTERED,
                            registry_id=uuid4(),
                            operation="unregister",
                            item_type=item_metadata.type.__name__,
                            item_id=str(item_metadata.id),
                            metadata=item_metadata.metadata,
                        )
                        await self._event_bus.publish(event)
                else:
                    # Unregister all versions
                    for ver, item_metadata in self._items[key].items():
                        if self._event_bus:
                            event = RegistryEvent(
                                event_type=EventType.PROVIDER_UNREGISTERED,
                                registry_id=uuid4(),
                                operation="unregister",
                                item_type=item_metadata.type.__name__,
                                item_id=str(item_metadata.id),
                                metadata=item_metadata.metadata,
                            )
                            await self._event_bus.publish(event)

                    del self._items[key]

        except NotFoundError:
            raise
        except Exception as e:
            raise RegistryError(f"Failed to unregister item: {e}") from e

    async def get(
        self, key: str, version: str | None = None
    ) -> type[T] | dict[str, type[T]]:
        """Get an item from the registry.

        Args:
            key: Key of the item to get
            version: Optional specific version to get

        Returns:
            The requested item type or dictionary of versions

        Raises:
            NotFoundError: If key or version is not found
            StateError: If registry is not active

        """
        self._ensure_active()

        async with self._lock:
            if key not in self._items:
                raise NotFoundError(f"Item not found with key: {key}")

            if version:
                if version not in self._items[key]:
                    raise NotFoundError(f"Version {version} not found for key: {key}")
                return self._items[key][version].type

            return {ver: item.type for ver, item in self._items[key].items()}

    async def get_metadata(
        self, key: str, version: str | None = None
    ) -> dict[str, Any] | dict[str, dict[str, Any]]:
        """Get item metadata.

        Args:
            key: Key of the item
            version: Optional specific version

        Returns:
            Item metadata or dictionary of version metadata

        Raises:
            NotFoundError: If key or version is not found
            StateError: If registry is not active

        """
        self._ensure_active()

        async with self._lock:
            if key not in self._items:
                raise NotFoundError(f"Item not found with key: {key}")

            if version:
                if version not in self._items[key]:
                    raise NotFoundError(f"Version {version} not found for key: {key}")
                return self._items[key][version].metadata.copy()

            return {ver: item.metadata.copy() for ver, item in self._items[key].items()}

    async def update_metadata(
        self,
        key: str,
        version: str,
        metadata: dict[str, Any],
    ) -> None:
        """Update item metadata.

        Args:
            key: Key of the item
            version: Version to update
            metadata: New metadata

        Raises:
            NotFoundError: If key or version is not found
            StateError: If registry is not active

        """
        self._ensure_active()

        async with self._lock:
            if key not in self._items or version not in self._items[key]:
                raise NotFoundError(
                    f"Item not found with key: {key} and version: {version}"
                )

            item = self._items[key][version]
            updated_item = item.copy(
                update={
                    "metadata": metadata,
                    "updated_at": datetime.utcnow(),
                }
            )
            self._items[key][version] = updated_item

            if self._event_bus:
                event = RegistryEvent(
                    event_type=EventType.SYSTEM_STARTED,
                    registry_id=uuid4(),
                    operation="update",
                    item_type=item.type.__name__,
                    item_id=str(item.id),
                    metadata=metadata,
                )
                await self._event_bus.publish(event)

    def list_items(self) -> dict[str, dict[str, type[T]]]:
        """Get all registered items.

        Returns:
            Dictionary of registered items by key and version

        Raises:
            StateError: If registry is not active

        """
        self._ensure_active()
        return {
            key: {ver: item.type for ver, item in versions.items()}
            for key, versions in self._items.items()
        }

    def list_metadata(self) -> dict[str, dict[str, dict[str, Any]]]:
        """Get metadata for all registered items.

        Returns:
            Dictionary of item metadata by key and version

        Raises:
            StateError: If registry is not active

        """
        self._ensure_active()
        return {
            key: {ver: item.metadata.copy() for ver, item in versions.items()}
            for key, versions in self._items.items()
        }

    async def clear(self) -> None:
        """Remove all items from the registry.

        Raises:
            StateError: If registry is not active

        """
        self._ensure_active()

        async with self._lock:
            # Publish unregister events for all items
            if self._event_bus:
                for _key, versions in self._items.items():
                    for version, item in versions.items():
                        event = RegistryEvent(
                            event_type=EventType.PROVIDER_UNREGISTERED,
                            registry_id=uuid4(),
                            operation="unregister",
                            item_type=item.type.__name__,
                            item_id=str(item.id),
                            metadata=item.metadata,
                        )
                        await self._event_bus.publish(event)

            self._items.clear()

    def is_compatible(
        self, key: str, required_version: str, available_version: str
    ) -> bool:
        """Check if versions are compatible.

        Args:
            key: Key of the item
            required_version: Required version
            available_version: Available version

        Returns:
            bool: True if versions are compatible

        """
        try:
            required = Version.from_string(required_version)
            available = Version.from_string(available_version)

            # Major version must match for compatibility
            if required.major != available.major:
                return False

            # Available version must be greater than or equal
            return not available < required
        except ValueError:
            return False

    def _validate_component_type(
        self,
        component_type: str,
        component_class: type[T],
    ) -> None:
        """Validate component type and class.

        Args:
            component_type: Type identifier for the component
            component_class: Class to validate

        Raises:
            RegistryError: If validation fails

        """
        if not component_type:
            raise RegistryError("Component type cannot be empty")
        if not isinstance(component_type, str):
            raise RegistryError("Component type must be a string")
        if component_type in self._items:
            raise RegistryError(f"Component type already registered: {component_type}")

        item: type[T] = component_class
        if not isinstance(item, type):
            raise ValidationError(
                f"Invalid component type: {component_type}",
                details={"type": str(type(item))},
            )


class CapabilityRegistry(Registry[Any]):
    """Registry for agent capabilities.

    This class extends the base Registry to provide specific functionality
    for managing agent capabilities, including:
    - Capability registration and discovery
    - Version compatibility checking
    - Capability metadata management
    - Agent-capability relationship tracking
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize the capability registry."""
        super().__init__("capability_registry", event_bus)
        self._agent_capabilities: dict[UUID, set[str]] = {}

    async def register_capability(
        self,
        agent_id: UUID,
        capability_name: str,
        version: str,
        framework: str,
        requirements: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> UUID:
        """Register a capability for an agent.

        Args:
            agent_id: Agent ID
            capability_name: Capability name
            version: Capability version
            framework: Framework name
            requirements: Optional capability requirements
            metadata: Optional capability metadata

        Returns:
            Capability ID

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If registry is not active

        """
        if not self.is_active:
            raise RuntimeError("Registry is not active")

        # Create capability metadata
        capability_metadata = CapabilityMetadata(
            key=capability_name,
            type=type(None),  # Type doesn't matter for capabilities
            version=version,
            agent_id=agent_id,
            framework=framework,
            requirements=requirements or [],
            metadata=metadata or {},
        )

        # Register capability
        capability_id = await super().register(
            key=capability_name,
            item_type=type(None),  # Type doesn't matter for capabilities
            version=version,
            metadata=capability_metadata.dict(),
        )

        # Track agent capability
        if agent_id not in self._agent_capabilities:
            self._agent_capabilities[agent_id] = set()
        self._agent_capabilities[agent_id].add(capability_name)

        logger.info(
            "Registered capability",
            extra={
                "capability_name": capability_name,
                "agent_id": str(agent_id),
                "version": version,
            },
        )

        return capability_id

    async def unregister_capability(
        self, agent_id: UUID, capability_name: str, version: str | None = None
    ) -> None:
        """Unregister a capability for an agent.

        Args:
            agent_id: ID of the agent
            capability_name: Name of the capability
            version: Optional specific version to unregister

        """
        await self.unregister(capability_name, version)
        if agent_id in self._agent_capabilities:
            self._agent_capabilities[agent_id].discard(capability_name)
            if not self._agent_capabilities[agent_id]:
                del self._agent_capabilities[agent_id]

    def get_agents_with_capability(
        self, capability_name: str, version: str | None = None
    ) -> list[UUID]:
        """Get all agents that have registered a specific capability.

        Args:
            capability_name: Name of the capability
            version: Optional specific version to match

        Returns:
            List[UUID]: List of agent IDs with the capability

        """
        agents = []
        for agent_id, capabilities in self._agent_capabilities.items():
            if capability_name in capabilities:
                if version:
                    try:
                        metadata = self._items[capability_name][version].metadata
                        if metadata.get("agent_id") == agent_id:
                            agents.append(agent_id)
                    except KeyError:
                        continue
                else:
                    agents.append(agent_id)
        return agents

    def get_agent_capabilities(
        self, agent_id: UUID
    ) -> dict[str, dict[str, CapabilityMetadata]]:
        """Get all capabilities registered for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Dict[str, Dict[str, CapabilityMetadata]]: Capabilities by name and version

        """
        if agent_id not in self._agent_capabilities:
            return {}

        capabilities = {}
        for cap_name in self._agent_capabilities[agent_id]:
            if cap_name in self._items:
                capabilities[cap_name] = {
                    ver: CapabilityMetadata(
                        id=item.id,
                        key=item.key,
                        type=item.type,
                        version=ver,
                        agent_id=agent_id,
                        framework=item.metadata["framework"],
                        requirements=item.metadata.get("requirements", []),
                        metadata=item.metadata.get("metadata", {}),
                    )
                    for ver, item in self._items[cap_name].items()
                    if item.metadata.get("agent_id") == agent_id
                }
        return capabilities


# Global registry instances
capability_registry = CapabilityRegistry()


class ProviderRegistry:
    """Registry for managing and loading capability providers."""

    def __init__(self):
        """Initialize provider registry."""
        self._providers: Dict[str, Dict[str, Type[Any]]] = {}

    def register(
        self, capability: str, provider_type: str, provider_class: Type[T]
    ) -> None:
        """Register a provider class.

        Args:
            capability: Capability name (e.g. 'llm', 'content')
            provider_type: Provider type identifier
            provider_class: Provider class to register
        """
        if capability not in self._providers:
            self._providers[capability] = {}

        self._providers[capability][provider_type] = provider_class

    def get_provider(self, capability: str, provider_type: str) -> Optional[Type[Any]]:
        """Get a registered provider class.

        Args:
            capability: Capability name
            provider_type: Provider type identifier

        Returns:
            Provider class if found, None otherwise
        """
        return self._providers.get(capability, {}).get(provider_type)

    def load_provider(
        self, capability: str, provider_type: str, base_class: Type[T]
    ) -> Type[T]:
        """Load a provider class dynamically.

        Args:
            capability: Capability name
            provider_type: Provider type identifier
            base_class: Base class that provider must implement

        Returns:
            Provider class

        Raises:
            ConfigError: If provider cannot be loaded
        """
        # Check if already registered
        provider_class = self.get_provider(capability, provider_type)
        if provider_class is not None:
            if not issubclass(provider_class, base_class):
                raise ConfigError(
                    f"Provider class {provider_class.__name__} does not implement {base_class.__name__}"
                )
            return provider_class

        try:
            # Load provider module
            module_path = f"pepperpy.{capability}.providers.{provider_type}"
            module = importlib.import_module(module_path)

            # Get provider class
            provider_class = getattr(module, f"{provider_type.title()}Provider")

            # Validate provider class
            if not issubclass(provider_class, base_class):
                raise ConfigError(
                    f"Provider class {provider_class.__name__} does not implement {base_class.__name__}"
                )

            # Register provider
            self.register(capability, provider_type, provider_class)

            return provider_class

        except (ImportError, AttributeError) as e:
            raise ConfigError(
                f"Failed to load provider {capability}.{provider_type}: {str(e)}"
            )

    def discover_providers(self, package_path: Optional[Path] = None) -> None:
        """Discover and register providers from package.

        Args:
            package_path: Path to package root. If None, uses current package.
        """
        if package_path is None:
            package_path = Path(__file__).parent.parent

        # Scan capability directories
        for capability_dir in package_path.iterdir():
            if not capability_dir.is_dir():
                continue

            providers_dir = capability_dir / "providers"
            if not providers_dir.exists() or not providers_dir.is_dir():
                continue

            # Load providers
            capability = capability_dir.name
            for provider_file in providers_dir.glob("*.py"):
                if provider_file.stem == "__init__":
                    continue

                try:
                    module_path = (
                        f"pepperpy.{capability}.providers.{provider_file.stem}"
                    )
                    importlib.import_module(module_path)
                except ImportError:
                    continue


# Global registry instance
registry = ProviderRegistry()
