"""@file: factory.py
@purpose: Runtime factory system for component creation and management
@component: Runtime
@created: 2024-02-15
@task: TASK-003
@status: active
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Type, TypeVar, cast
from uuid import UUID, uuid4

from pepperpy.core.base import BaseComponent, Metadata
from pepperpy.core.errors import ConfigurationError, StateError
from pepperpy.core.logging import get_logger
from pepperpy.core.types import JSON
from pepperpy.runtime.context import Context, get_current_context
from pepperpy.runtime.lifecycle import (
    Lifecycle,
    get_lifecycle_manager,
)

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseComponent)


@dataclass
class Factory:
    """Factory for creating and managing runtime components."""

    id: UUID = field(default_factory=uuid4)
    name: str = field(default="default")
    component_type: Type[BaseComponent] = field(default=BaseComponent)
    lifecycle: Optional[Lifecycle] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Initialize factory after creation."""
        self.validate()

    def validate(self) -> None:
        """Validate factory configuration."""
        if not self.name:
            raise ConfigurationError("Factory name is required")
        if not issubclass(self.component_type, BaseComponent):
            raise ConfigurationError(
                f"Invalid component type: {self.component_type.__name__}"
            )

    async def create(
        self,
        context: Optional[Context] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> T:
        """Create a new component instance.

        Args:
            context: Optional context to associate with component
            metadata: Optional component metadata

        Returns:
            Created component instance

        Raises:
            StateError: If factory is not ready
            ConfigurationError: If component creation fails

        """
        if not self.lifecycle or self.lifecycle.state != "ready":
            raise StateError("Factory is not ready")

        try:
            now = datetime.utcnow()
            component = self.component_type(
                id=uuid4(),
                metadata=Metadata(
                    created_at=now,
                    updated_at=now,
                    version="1.0.0",
                    tags=[],
                    properties=metadata or {},
                ),
            )
            await component.initialize()
            return cast(T, component)
        except Exception as e:
            logger.error(f"Failed to create component: {e}")
            raise ConfigurationError(f"Component creation failed: {e}") from e

    def to_json(self) -> JSON:
        """Convert factory to JSON format.

        Returns:
            JSON representation of factory

        """
        return {
            "id": str(self.id),
            "name": self.name,
            "component_type": self.component_type.__name__,
            "lifecycle_id": str(self.lifecycle.id) if self.lifecycle else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_json(cls, data: JSON) -> "Factory":
        """Create factory from JSON data.

        Args:
            data: JSON data to create factory from

        Returns:
            Created factory instance

        """
        return cls(
            id=UUID(data["id"]),
            name=data["name"],
            component_type=globals()[data["component_type"]],
            lifecycle=None,  # Lifecycle must be set separately
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


class FactoryManager:
    """Manager for runtime factories."""

    def __init__(self) -> None:
        """Initialize factory manager."""
        self._factories: Dict[UUID, Factory] = {}
        self._lock = threading.Lock()
        self._lifecycle_manager = get_lifecycle_manager()

    def create(
        self,
        name: str,
        component_type: Type[BaseComponent],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Factory:
        """Create a new factory.

        Args:
            name: Factory name
            component_type: Type of components to create
            metadata: Optional factory metadata

        Returns:
            Created factory instance

        """
        factory = Factory(
            name=name,
            component_type=component_type,
            metadata=metadata or {},
        )

        # Create and associate lifecycle
        lifecycle = self._lifecycle_manager.create(
            context=get_current_context(),
            metadata={"factory_id": str(factory.id)},
        )
        factory.lifecycle = lifecycle

        with self._lock:
            self._factories[factory.id] = factory

        return factory

    def get(self, factory_id: UUID) -> Optional[Factory]:
        """Get a factory by ID.

        Args:
            factory_id: Factory ID to get

        Returns:
            Factory instance if found, None otherwise

        """
        return self._factories.get(factory_id)

    def remove(self, factory_id: UUID) -> None:
        """Remove a factory.

        Args:
            factory_id: Factory ID to remove

        """
        with self._lock:
            if factory_id in self._factories:
                factory = self._factories[factory_id]
                if factory.lifecycle:
                    self._lifecycle_manager.remove(factory.lifecycle.id)
                del self._factories[factory_id]


class FactoryProvider:
    """Provider for factory registration and lookup."""

    def __init__(self) -> None:
        """Initialize factory provider."""
        self._factories: Dict[str, Callable[..., Factory]] = {}
        self._lock = threading.Lock()

    def register(self, name: str, factory_func: Callable[..., Factory]) -> None:
        """Register a factory function.

        Args:
            name: Factory name
            factory_func: Factory creation function

        """
        with self._lock:
            self._factories[name] = factory_func

    def unregister(self, name: str) -> None:
        """Unregister a factory function.

        Args:
            name: Factory name to unregister

        """
        with self._lock:
            if name in self._factories:
                del self._factories[name]

    def get(self, name: str) -> Optional[Callable[..., Factory]]:
        """Get a factory function by name.

        Args:
            name: Factory name to get

        Returns:
            Factory function if found, None otherwise

        """
        return self._factories.get(name)


# Global instances
_factory_manager = FactoryManager()
_factory_provider = FactoryProvider()


def get_factory() -> FactoryManager:
    """Get the global factory manager.

    Returns:
        Global factory manager instance

    """
    return _factory_manager


def register_factory(name: str, factory_func: Callable[..., Factory]) -> None:
    """Register a factory function globally.

    Args:
        name: Factory name
        factory_func: Factory creation function

    """
    _factory_provider.register(name, factory_func)
