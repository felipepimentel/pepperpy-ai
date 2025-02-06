"""Registry system for managing Pepperpy components.

This module provides a comprehensive registry system for managing:
- Generic component registration and lifecycle
- Agent capability discovery and versioning
- Type-safe component creation and validation
- Event-driven updates and notifications
- Metadata tracking and version control
"""

import asyncio
import logging
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, ClassVar, Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

from pepperpy.common.errors import NotFoundError
from pepperpy.core.errors import RegistryError, StateError, ValidationError
from pepperpy.core.events import Event, EventBus, EventHandler, EventPriority, EventType

logger = logging.getLogger(__name__)

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

    @validator("key")
    def validate_key(self, v: str) -> str:
        """Validate registry key."""
        if not v.strip():
            raise ValueError("key cannot be empty")
        return v

    @validator("metadata")
    def validate_metadata(self, v: dict[str, Any]) -> dict[str, Any]:
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


class RegistryEvent(Event):
    """Event specific to registry operations."""

    item_id: UUID
    item_key: str
    item_type: str
    version: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RegistryEventHandler(EventHandler):
    """Base class for registry event handlers."""

    @abstractmethod
    async def on_item_registered(self, event: RegistryEvent) -> None:
        """Handle item registration event."""
        pass

    @abstractmethod
    async def on_item_unregistered(self, event: RegistryEvent) -> None:
        """Handle item unregistration event."""
        pass

    @abstractmethod
    async def on_item_updated(self, event: RegistryEvent) -> None:
        """Handle item update event."""
        pass

    async def handle_event(self, event: Event) -> None:
        """Route events to specific handlers."""
        if not isinstance(event, RegistryEvent):
            return

        try:
            if event.type == EventType.PROVIDER_REGISTERED:
                await self.on_item_registered(event)
            elif event.type == EventType.PROVIDER_UNREGISTERED:
                await self.on_item_unregistered(event)
            elif event.type == EventType.SYSTEM_STARTED:
                await self.on_item_updated(event)
        except Exception as e:
            logger.error(f"Error handling registry event: {e!s}")


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
        self._items: dict[str, dict[str, RegistryMetadata]] = {}
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
            UUID of the registered item

        Raises:
            ValidationError: If key is invalid or already exists
            StateError: If registry is not active
        """
        self._ensure_active()

        async with self._lock:
            if key not in self._items:
                self._items[key] = {}

            # Validate version
            try:
                Version.from_string(version)
            except ValueError as e:
                raise ValidationError(f"Invalid version format: {e}") from e

            if version in self._items[key]:
                raise ValidationError(
                    f"Version {version} already exists for key: {key}"
                )

            try:
                item = RegistryMetadata(
                    key=key,
                    type=item_type,
                    version=version,
                    metadata=metadata or {},
                )
                self._items[key][version] = item

                if self._event_bus:
                    event = RegistryEvent(
                        type=EventType.PROVIDER_REGISTERED,
                        source_id=self.name,
                        priority=EventPriority.HIGH,
                        item_id=item.id,
                        item_key=item.key,
                        item_type=(f"{item_type.__module__}.{item_type.__qualname__}"),
                        version=version,
                        metadata=metadata if metadata is not None else {},
                    )
                    await self._event_bus.publish(event)

                return item.id

            except Exception as e:
                raise ValidationError(f"Failed to register item: {e!s}") from e

    async def unregister(self, key: str, version: str | None = None) -> None:
        """Remove an item from the registry.

        Args:
            key: Key of the item to remove
            version: Optional specific version to remove

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
                item = self._items[key][version]
                del self._items[key][version]

                if not self._items[key]:
                    del self._items[key]
            else:
                # Remove all versions
                for ver, item in self._items[key].items():
                    if self._event_bus:
                        event = RegistryEvent(
                            type=EventType.PROVIDER_UNREGISTERED,
                            source_id=self.name,
                            priority=EventPriority.HIGH,
                            item_id=item.id,
                            item_key=item.key,
                            item_type=(
                                f"{item.type.__module__}.{item.type.__qualname__}"
                            ),
                            version=ver,
                        )
                        await self._event_bus.publish(event)
                del self._items[key]

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
                    type=EventType.SYSTEM_STARTED,
                    source_id=self.name,
                    priority=EventPriority.MEDIUM,
                    item_id=item.id,
                    item_key=item.key,
                    item_type=(f"{item.type.__module__}.{item.type.__qualname__}"),
                    version=version,
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
                            type=EventType.PROVIDER_UNREGISTERED,
                            source_id=self.name,
                            priority=EventPriority.HIGH,
                            item_id=item.id,
                            item_key=item.key,
                            item_type=(
                                f"{item.type.__module__}.{item.type.__qualname__}"
                            ),
                            version=version,
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
